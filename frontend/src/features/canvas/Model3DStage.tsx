import { useEffect, useMemo, useRef, useState } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Edges, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { ModuleScene, Scene3D, Solid3D } from "./Product3DScene";
import { solidToGeometry } from "./scene3dGeometry";
import {
  disposeFinishMaterials,
  finishGeometryMaterials,
  prepareFinishTextures,
} from "./finishMaterials3d";
import { solidMaterial, type MaterialMode } from "./materials3d";
import {
  explodeDistance,
  explodeLayer,
  moduleLeafPoses,
  MOTION_SECONDS,
  solidCenter,
  type LeafPoseState,
} from "./poses3d";
import {
  cameraShot,
  poseMatrix,
  STUDIO_BACKGROUND,
  STUDIO_GROUND,
  STUDIO_LIGHTS,
  STUDIO_WALL,
  STUDIO_GUIDE,
  studioColor,
  studioEnvironment,
  wallBoxes,
  type CameraPreset,
} from "./studioRig3d";
import type { WallBox } from "./mountedWall";

function tokenColor(token: string, fallback: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback;
}
function SolidMesh({
  solid,
  selected,
  theme,
  mode,
  clipPlane,
  onPick,
}: {
  solid: Solid3D;
  selected: boolean;
  /** Re-resolves token colors when the app theme switches — theme changes
   * flip CSS variables without otherwise re-rendering this subtree. */
  theme: string;
  mode: MaterialMode;
  clipPlane: THREE.Plane | null;
  onPick(owner: string): void;
}): JSX.Element {
  const geometry = useMemo(
    () => (solid.kind === "box" ? new THREE.BoxGeometry(...solid.size) : solidToGeometry(solid)),
    [solid],
  );
  const [textureEpoch, setTextureEpoch] = useState(0);
  useEffect(() => {
    let alive = true;
    if (solid.finish)
      void prepareFinishTextures(solid.finish).then(() => {
        if (alive) setTextureEpoch((value) => value + 1);
      });
    return () => {
      alive = false;
    };
  }, [solid.finish]);
  const faceMaterials = useMemo(
    () =>
      geometry && solid.finish && mode === "commercial"
        ? finishGeometryMaterials(geometry, solid.finish)
        : null,
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loaded texture becomes available
    [geometry, solid.finish, mode, textureEpoch],
  );
  useEffect(
    () => () => {
      if (faceMaterials) disposeFinishMaterials(faceMaterials);
    },
    [faceMaterials],
  );
  useEffect(() => {
    for (const item of faceMaterials ?? []) {
      item.clippingPlanes = clipPlane ? [clipPlane] : [];
      item.needsUpdate = true;
    }
  }, [faceMaterials, clipPlane]);

  // eslint-disable-next-line react-hooks/exhaustive-deps -- theme re-resolves
  // the same tokens against the new CSS variable values.
  const material = useMemo(() => solidMaterial(solid, mode), [solid, mode]);
  const color = useMemo(
    () =>
      solid.hardwareColor && mode === "commercial"
        ? new THREE.Color().setRGB(
            ...(solid.hardwareColor.linear_rgb.map(Number) as [number, number, number]),
            THREE.LinearSRGBColorSpace,
          )
        : tokenColor(material.colorToken, material.colorFallback),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [solid.hardwareColor, mode, material, theme],
  );
  // BufferGeometry passed to <mesh geometry> is not auto-disposed by r3f —
  // every edit regenerates solids, so the replaced geometry must be freed
  // or GPU memory grows monotonically through a session.
  useEffect(() => {
    return () => {
      geometry?.dispose();
    };
  }, [geometry]);
  return (
    <mesh
      geometry={geometry ?? undefined}
      position={solid.kind === "box" ? solid.center : undefined}
      onClick={(event) => {
        event.stopPropagation();
        onPick(solid.owner);
      }}
    >
      {faceMaterials ? (
        <primitive attach="material" object={faceMaterials} dispose={null} />
      ) : (
        <meshStandardMaterial
          color={color}
          transparent={material.transparent}
          opacity={material.opacity}
          depthWrite={!material.glass}
          roughness={material.roughness}
          metalness={material.metalness}
          // An empty array — never undefined: r3f applies this prop onto
          // material.clippingPlanes and three's WebGLClipping crashes on a
          // missing .length, leaving the whole canvas blank once Corte was
          // toggled off.
          clippingPlanes={clipPlane ? [clipPlane] : []}
        />
      )}
      {/* Approximate member boxes (no declared catalog section) get the
       * schematic edge look — visually distinct from a real extruded
       * profile so convention never masquerades as authority. */}
      {(selected || solid.approximate === true || mode === "technical") &&
        (solid.kind === "box" || solid.kind === "profile") && (
          <Edges
            scale={1.002}
            color={
              selected ? tokenColor("--theme-accent", "teal") : tokenColor("--model3d-edge", "gray")
            }
          />
        )}
    </mesh>
  );
}

function ModuleContent({
  module,
  states,
  explode,
  renderSolid,
}: {
  module: ModuleScene;
  states: Record<string, LeafPoseState>;
  explode: boolean;
  renderSolid(solid: Solid3D, key: string): JSX.Element;
}): JSX.Element {
  const groups = useRef(new Map<string, THREE.Group>());
  const layerGroups = useRef(new Map<string, THREE.Group>());
  const progress = useRef<Record<string, LeafPoseState>>({});
  const previous = useRef<Record<string, LeafPoseState>>({});
  const elapsed = useRef(MOTION_SECONDS);
  const exploded = useRef(0),
    explodeFrom = useRef(0);
  const invalidate = useThree((s) => s.invalidate);
  const reduced = useRef(false);
  const guideGeometry = useMemo(() => {
    const representatives = new Map<string, Solid3D>();
    for (const solid of module.solids) {
      const layer = explodeLayer(solid);
      if (layer) representatives.set(`${solid.leafId ?? "fixed"}/${layer}`, solid);
    }
    const origins = [...representatives.values()].map((solid) => ({
      center: solidCenter(solid),
      layer: explodeLayer(solid),
    }));
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        origins.flatMap((o) => [...o.center, ...o.center]),
        3,
      ),
    );
    return { geometry, origins };
  }, [module]);
  useEffect(() => () => guideGeometry.geometry.dispose(), [guideGeometry]);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    reduced.current = query.matches;
    const changed = () => {
      reduced.current = query.matches;
      invalidate();
    };
    query.addEventListener("change", changed);
    return () => query.removeEventListener("change", changed);
  }, [invalidate]);
  useEffect(() => {
    previous.current = { ...progress.current };
    explodeFrom.current = exploded.current;
    elapsed.current = 0;
    invalidate();
  }, [states, explode, module, invalidate]);
  useFrame((_, delta) => {
    if (elapsed.current >= MOTION_SECONDS) return;
    elapsed.current = reduced.current
      ? MOTION_SECONDS
      : Math.min(MOTION_SECONDS, elapsed.current + delta);
    const t = elapsed.current / MOTION_SECONDS;
    const ease = (v: number) => 1 - (1 - v) ** 3;
    for (const leaf of module.leaves) {
      const from = previous.current[leaf.leafId] ?? { amount: 0, mode: "open" };
      const to = states[leaf.leafId] ?? { amount: 0, mode: "open" };
      const switchPivot = from.mode !== to.mode && from.amount > 0 && to.amount > 0;
      progress.current[leaf.leafId] = switchPivot
        ? t < 0.5
          ? { amount: from.amount * (1 - ease(t * 2)), mode: from.mode }
          : { amount: to.amount * ease((t - 0.5) * 2), mode: to.mode }
        : { amount: from.amount + (to.amount - from.amount) * ease(t), mode: to.mode };
    }
    const poses = moduleLeafPoses(module, explode ? {} : progress.current);
    for (const [id, group] of groups.current) {
      const pose = poses[id];
      group.matrix.copy(pose ? poseMatrix(pose) : new THREE.Matrix4());
      group.matrixWorldNeedsUpdate = true;
    }
    exploded.current = explodeFrom.current + ((explode ? 1 : 0) - explodeFrom.current) * ease(t);
    const distance = explodeDistance(module.depth) * exploded.current;
    for (const [key, group] of layerGroups.current)
      group.position.z = Number(key.slice(key.lastIndexOf("/") + 1)) * distance;
    const positions = guideGeometry.geometry.getAttribute("position");
    guideGeometry.origins.forEach((origin, index) =>
      positions.setXYZ(
        index * 2 + 1,
        origin.center[0],
        origin.center[1],
        origin.center[2] + origin.layer * distance,
      ),
    );
    positions.needsUpdate = true;
    guideGeometry.geometry.computeBoundingSphere();
    if (t < 1) invalidate();
  });
  const layers = (leafId?: string): JSX.Element[] =>
    [0, 1, 2, 3].map((layer) => {
      const key = `${leafId ?? "fixed"}/${layer}`;
      return (
        <group
          key={key}
          ref={(group) => {
            if (group) layerGroups.current.set(key, group);
            else layerGroups.current.delete(key);
          }}
        >
          {module.solids
            .filter((s) => s.leafId === leafId && explodeLayer(s) === layer)
            .map((s, i) => renderSolid(s, `${key}/${i}`))}
        </group>
      );
    });
  return (
    <group position={module.position} rotation={[0, module.rotationY, 0]}>
      {module.leaves.map((leaf) => (
        <group
          key={leaf.leafId}
          matrixAutoUpdate={false}
          ref={(group) => {
            if (group) groups.current.set(leaf.leafId, group);
            else groups.current.delete(leaf.leafId);
          }}
        >
          {layers(leaf.leafId)}
        </group>
      ))}
      {layers()}
      {explode && (
        <lineSegments geometry={guideGeometry.geometry}>
          <lineBasicMaterial color={studioColor(STUDIO_GUIDE)} />
        </lineSegments>
      )}
    </group>
  );
}

function CameraRig({
  scene,
  preset,
  explode,
  states,
  onExport,
  onError,
}: {
  scene: Scene3D;
  preset: CameraPreset;
  explode: boolean;
  states: Record<string, Record<string, LeafPoseState>>;
  onExport(capture: () => string): void;
  onError(): void;
}): null {
  const camera = useThree((s) => s.camera),
    controls = useThree((s) => s.controls) as unknown as {
      target: THREE.Vector3;
      update(): void;
    } | null;
  const size = useThree((s) => s.size),
    gl = useThree((s) => s.gl),
    world = useThree((s) => s.scene),
    invalidate = useThree((s) => s.invalidate);
  const latestStates = useRef(states);
  latestStates.current = states;
  useEffect(() => {
    const shot = cameraShot(
      scene,
      preset,
      size.width / Math.max(size.height, 1),
      explode,
      latestStates.current,
    );
    camera.position.set(...shot.position);
    camera.lookAt(...shot.target);
    camera.near = 1;
    camera.far = scene.radius * 30;
    camera.updateProjectionMatrix();
    controls?.target.set(...shot.target);
    controls?.update();
    invalidate();
  }, [scene, preset, explode, size.width, size.height, camera, controls, invalidate]);
  useEffect(() => {
    onExport(() => {
      gl.render(world, camera);
      return gl.domElement.toDataURL("image/png");
    });
    const lost = (event: Event) => {
      event.preventDefault();
      onError();
    };
    gl.domElement.addEventListener("webglcontextlost", lost);
    gl.domElement.tabIndex = 0;
    gl.domElement.setAttribute(
      "aria-label",
      "Vista 3D. Use flechas para desplazar y más o menos para ampliar.",
    );
    const key = (event: KeyboardEvent) => {
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "+", "=", "-"].includes(event.key))
        return;
      event.preventDefault();
      const target = controls?.target ?? new THREE.Vector3();
      if (["+", "=", "-"].includes(event.key))
        camera.position
          .sub(target)
          .multiplyScalar(event.key === "-" ? 1.2 : 0.8)
          .add(target);
      else {
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
        const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
        const direction =
          event.key === "ArrowLeft"
            ? right.multiplyScalar(-1)
            : event.key === "ArrowRight"
              ? right
              : event.key === "ArrowDown"
                ? up.multiplyScalar(-1)
                : up;
        direction.multiplyScalar(camera.position.distanceTo(target) * 0.025);
        camera.position.add(direction);
        controls?.target.add(direction);
      }
      controls?.update();
      invalidate();
    };
    gl.domElement.addEventListener("keydown", key);
    return () => {
      gl.domElement.removeEventListener("webglcontextlost", lost);
      gl.domElement.removeEventListener("keydown", key);
    };
  }, [gl, world, camera, controls, invalidate, onExport, onError]);
  return null;
}

function Environment({ mode }: { mode: MaterialMode }): null {
  const gl = useThree((s) => s.gl),
    scene = useThree((s) => s.scene);
  useEffect(() => studioEnvironment(gl, scene, mode === "commercial"), [gl, scene, mode]);
  useEffect(() => {
    gl.localClippingEnabled = true;
    return () => {
      gl.localClippingEnabled = false;
    };
  }, [gl]);
  return null;
}

export function Model3DStage({
  scene,
  states,
  selection,
  theme,
  mode,
  preset,
  clip,
  explode,
  wall,
  mounted = EMPTY_MOUNTED,
  onPick,
  onExport,
  onError,
}: {
  scene: Scene3D;
  states: Record<string, Record<string, LeafPoseState>>;
  selection: string | null;
  theme: string;
  mode: MaterialMode;
  preset: CameraPreset;
  clip: boolean;
  explode: boolean;
  wall: boolean;
  /** Masonry around each module's measured vano, in module-local space. */
  mounted?: Record<string, WallBox[]>;
  onPick(owner: string): void;
  onExport(capture: () => string): void;
  onError(): void;
}): JSX.Element {
  const clipPlane = useMemo(() => new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0), []);
  // The masonry under a measured opening stands on the floor, not through it.
  const floor = useMemo(
    () =>
      Math.min(
        scene.bounds.min[1],
        ...scene.modules.flatMap((module) =>
          wall
            ? (mounted[module.moduleId] ?? []).map(
                (box) => module.position[1] + box.center[1] - box.size[1] / 2,
              )
            : [],
        ),
      ),
    [scene, mounted, wall],
  );
  const renderSolid = (solid: Solid3D, key: string) => (
    <SolidMesh
      key={key}
      solid={solid}
      selected={selection === solid.owner}
      theme={theme}
      mode={mode}
      clipPlane={clip ? clipPlane : null}
      onPick={onPick}
    />
  );
  return (
    <>
      <color attach="background" args={[studioColor(STUDIO_BACKGROUND)]} />
      <Environment mode={mode} />
      <ambientLight intensity={mode === "commercial" ? 0.55 : 0.85} />
      {STUDIO_LIGHTS.map((light, index) => (
        <directionalLight
          key={index}
          position={light.position}
          intensity={mode === "commercial" ? light.intensity : light.intensity * 0.7}
        />
      ))}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, floor - scene.center[1] - 2, 0]}>
        <planeGeometry args={[scene.radius * 5, scene.radius * 4]} />
        <meshStandardMaterial color={studioColor(STUDIO_GROUND)} roughness={0.95} />
      </mesh>
      <group position={scene.center.map((v) => -v) as [number, number, number]}>
        {scene.modules.map((module) => (
          <ModuleContent
            key={module.moduleId}
            module={module}
            states={states[module.moduleId] ?? EMPTY_STATES}
            explode={explode}
            renderSolid={renderSolid}
          />
        ))}
        {scene.couplers.map((solid, i) => renderSolid(solid, `coupler-${i}`))}
        {wall &&
          Object.keys(mounted).length > 0 &&
          scene.modules
            .filter((module) => mounted[module.moduleId])
            .map((module) => (
              <group
                key={`opening-${module.moduleId}`}
                position={module.position}
                rotation={[0, module.rotationY, 0]}
              >
                {mounted[module.moduleId]!.map((box, index) => (
                  <mesh key={index} position={box.center}>
                    <boxGeometry args={box.size} />
                    <meshStandardMaterial color={studioColor(STUDIO_WALL)} roughness={0.92} />
                  </mesh>
                ))}
              </group>
            ))}
        {wall &&
          Object.keys(mounted).length === 0 &&
          wallBoxes(scene).map((box, index) => (
            <mesh key={index} position={box.center}>
              <boxGeometry args={box.size} />
              <meshStandardMaterial color={studioColor(STUDIO_WALL)} roughness={0.92} />
            </mesh>
          ))}
      </group>
      <OrbitControls
        makeDefault
        enableDamping={false}
        minDistance={scene.radius * 0.12}
        maxDistance={scene.radius * 12}
      />
      <CameraRig
        scene={scene}
        preset={preset}
        explode={explode}
        states={states}
        onExport={onExport}
        onError={onError}
      />
    </>
  );
}
const EMPTY_STATES: Record<string, LeafPoseState> = {};
const EMPTY_MOUNTED: Record<string, WallBox[]> = {};

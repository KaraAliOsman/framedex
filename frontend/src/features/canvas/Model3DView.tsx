import { useEffect, useMemo, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { Edges, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { PlanGeometry } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import type { ProductJson } from "./productEditing";
import { useTheme } from "../../theme/ThemeProvider";
import { buildScene3D, type Scene3D, type Solid3D } from "./Product3DScene";
import { solidToGeometry } from "./scene3dGeometry";
import { solidMaterial, type MaterialMode } from "./materials3d";
import type { MemberGeometry } from "./members";

/** §16 synchronized 3D view (§05 physical renderer) — the scene derives
 * from the same product model the editor renders (no separate 3D data).
 * Orbit/pan/zoom via OrbitControls; solids carry the same owner ids the
 * 2D selection uses, so clicking a member, leaf or coupler here selects
 * it everywhere. Declared catalog sections extrude as real profiles;
 * undeclared members stay a visibly schematic box (edge lines), never
 * a fabricated declaration. */

function tokenColor(token: string, fallback: string): string {
  const value =
    typeof window === "undefined"
      ? ""
      : getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  return value || fallback;
}

function SolidMesh({
  solid,
  selected,
  theme,
  mode,
  onPick,
}: {
  solid: Solid3D;
  selected: boolean;
  /** Re-resolves token colors when the app theme switches — theme changes
   * flip CSS variables without otherwise re-rendering this subtree. */
  theme: string;
  mode: MaterialMode;
  onPick(owner: string): void;
}): JSX.Element {
  const geometry = useMemo(() => solidToGeometry(solid), [solid]);

  // eslint-disable-next-line react-hooks/exhaustive-deps -- theme re-resolves
  // the same tokens against the new CSS variable values.
  const material = useMemo(() => solidMaterial(solid, mode), [solid, mode]);
  const color = useMemo(
    () => tokenColor(material.colorToken, material.colorFallback),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [material, theme],
  );
  const emissive = useMemo(
    () => (selected ? tokenColor("--theme-warning", "#b45309") : "#000000"),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selected, theme],
  );
  return (
    <mesh
      geometry={geometry ?? undefined}
      position={solid.kind === "box" ? solid.center : undefined}
      onClick={(event) => {
        event.stopPropagation();
        onPick(solid.owner);
      }}
    >
      {solid.kind === "box" && <boxGeometry args={solid.size} />}
      <meshStandardMaterial
        color={color}
        transparent={material.transparent}
        opacity={material.opacity}
        depthWrite={!material.glass}
        roughness={material.roughness}
        metalness={material.metalness}
        emissive={emissive}
        emissiveIntensity={selected ? 0.55 : 0}
      />
      {/* Approximate member boxes (no declared catalog section) get the
       * schematic edge look — visually distinct from a real extruded
       * profile so convention never masquerades as authority. */}
      {(solid.approximate === true || mode === "technical") &&
        (solid.kind === "box" || solid.kind === "profile") && (
          <Edges scale={1.002} color={tokenColor("--model3d-edge", "#6b7075")} />
        )}
    </mesh>
  );
}

/** Keeps the live camera fitted when the scene bounds change — the Canvas
 * `camera` prop only applies at mount, so a growing assembly would leave
 * the original frustum. Refits along the current view direction so the
 * user's orbit angle survives a product edit. */
function CameraRig({ radius }: { radius: number }): null {
  const camera = useThree((state) => state.camera);
  const controls = useThree((state) => state.controls) as unknown as {
    target?: THREE.Vector3;
    update?: () => void;
  } | null;
  useEffect(() => {
    const distance = radius * 2.4;
    // Refit along the current view direction around the controls' target —
    // panning moves both, so rescaling about the world origin would change
    // the orbit angle and slide the product off-screen.
    const target = controls?.target ?? new THREE.Vector3();
    const dir = camera.position.clone().sub(target);
    if (dir.lengthSq() === 0) dir.set(0.5, 0.55, 1);
    camera.position.copy(target).add(dir.normalize().multiplyScalar(distance));
    camera.near = 1;
    camera.far = distance * 10;
    camera.updateProjectionMatrix();
    controls?.update?.();
  }, [camera, controls, radius]);
  return null;
}

function SceneContent({
  scene,
  selection,
  theme,
  mode,
  inside,
  onPick,
}: {
  scene: Scene3D;
  selection: string | null;
  theme: string;
  mode: MaterialMode;
  inside: boolean;
  onPick(owner: string): void;
}): JSX.Element {
  return (
    <>
      <ambientLight intensity={mode === "commercial" ? 0.55 : 0.85} />
      {/* Commercial mode gets studio key/fill; technical stays flat-lit. */}
      <directionalLight
        position={[4000, 6000, 5000]}
        intensity={mode === "commercial" ? 1.5 : 1.1}
      />
      <directionalLight
        position={[-3000, 2000, -4000]}
        intensity={mode === "commercial" ? 0.6 : 0.35}
      />
      {mode === "commercial" && <directionalLight position={[0, -2000, 2500]} intensity={0.25} />}
      {/* Inside/outside: the assembly (centered on the scene origin by the
       * inner group) rotates 180° so the room face or the street face
       * points at the default camera. */}
      <group rotation={[0, inside ? Math.PI : 0, 0]}>
        <group position={[-scene.center[0], -scene.center[1], -scene.center[2]]}>
          {scene.modules.map((module) => (
            <group
              key={module.moduleId}
              position={module.position}
              rotation={[0, module.rotationY, 0]}
            >
              {module.solids.map((solid, index) => (
                <SolidMesh
                  key={`${module.moduleId}-${index}`}
                  solid={solid}
                  selected={selection === solid.owner}
                  theme={theme}
                  mode={mode}
                  onPick={onPick}
                />
              ))}
            </group>
          ))}
          {scene.couplers.map((solid, index) => (
            <SolidMesh
              key={`coupler-${index}`}
              solid={solid}
              selected={selection === solid.owner}
              theme={theme}
              mode={mode}
              onPick={onPick}
            />
          ))}
        </group>
      </group>
      <OrbitControls
        makeDefault
        target={[0, 0, 0]}
        enableDamping={false}
        minDistance={scene.radius * 0.2}
        maxDistance={scene.radius * 8}
      />
      <CameraRig radius={scene.radius} />
    </>
  );
}

export default function Model3DView({
  product,
  members,
  plan,
  selection,
  onSelectModule,
  onSelectBay,
  onSelectCoupling,
}: {
  product: ProductJson;
  members: MemberGeometry;
  plan?: PlanGeometry | null;
  /** The shared selection id — module id, `moduleId/bayId`, or coupling id. */
  selection: string | null;
  onSelectModule(moduleId: string): void;
  onSelectBay(moduleId: string, bayId: string): void;
  onSelectCoupling(couplingId: string): void;
}): JSX.Element {
  const { theme } = useTheme();
  const [mode, setMode] = useState<MaterialMode>("commercial");
  const [inside, setInside] = useState(false);
  const scene = useMemo(() => buildScene3D(product, members, plan), [product, members, plan]);
  const moduleIds = useMemo(
    () => new Set(product.assembly.modules.map((module) => module.id)),
    [product],
  );
  const pick = (owner: string): void => {
    const split = owner.indexOf("/");
    if (split > 0) {
      onSelectBay(owner.slice(0, split), owner.slice(split + 1));
      return;
    }
    if (moduleIds.has(owner)) {
      onSelectModule(owner);
      return;
    }
    onSelectCoupling(owner);
  };
  const cameraDistance = scene.radius * 2.4;
  return (
    <div className="model3d-view">
      <div className="model3d-toolbar" role="toolbar" aria-label={t("assembly.view3d")}>
        <button
          type="button"
          className={mode === "commercial" ? "is-active" : ""}
          onClick={() => setMode("commercial")}
        >
          {t("assembly.view3dCommercial")}
        </button>
        <button
          type="button"
          className={mode === "technical" ? "is-active" : ""}
          onClick={() => setMode("technical")}
        >
          {t("assembly.view3dTechnical")}
        </button>
        <button
          type="button"
          className={inside ? "" : "is-active"}
          onClick={() => setInside(false)}
        >
          {t("assembly.view3dOutside")}
        </button>
        <button type="button" className={inside ? "is-active" : ""} onClick={() => setInside(true)}>
          {t("assembly.view3dInside")}
        </button>
      </div>
      <Canvas
        frameloop="demand"
        dpr={[1, 2]}
        camera={{
          position: [cameraDistance * 0.5, scene.radius * 0.55, cameraDistance],
          fov: 42,
          near: 1,
          far: cameraDistance * 10,
        }}
        className="model3d-canvas"
      >
        <SceneContent
          scene={scene}
          selection={selection}
          theme={theme}
          mode={mode}
          inside={inside}
          onPick={pick}
        />
      </Canvas>
    </div>
  );
}

import { useEffect, useMemo } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { PlanGeometry } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";
import { useTheme } from "../../theme/ThemeProvider";
import { buildScene3D, type Scene3D, type Solid3D } from "./Product3DScene";
import type { MemberGeometry } from "./members";

/** §16 synchronized 3D view — the scene derives from the same product model
 * the editor renders (no separate 3D data). Orbit/pan/zoom via
 * OrbitControls; solids carry the same owner ids the 2D selection uses, so
 * clicking a member, leaf or coupler here selects it everywhere. */

/** Surface treatments keyed to the catalog material — the same families
 * the 2D member palette distinguishes (PVC light, aluminium mid, glass
 * translucent, steel for fittings). Colors come from the theme tokens:
 * three.js needs resolved values, not `var()` strings, so each token is
 * read once per render via getComputedStyle. */
const SURFACE_TOKENS: Record<string, string> = {
  PVC: "--member-pvc-fill",
  ALUMINIUM: "--member-aluminium-fill",
};

function tokenColor(tokenExpr: string, fallback: string): string {
  const name = tokenExpr.slice(4, -1).trim();
  const value =
    typeof window === "undefined"
      ? ""
      : getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function solidColor(solid: Solid3D): string {
  if (solid.surface === "glass") return tokenColor("var(--model3d-glass)", "#8fb8cc");
  if (solid.surface === "panel") return tokenColor("var(--member-panel-fill)", "#b9bcc0");
  if (solid.surface === "fitting" || solid.surface === "support")
    return tokenColor("var(--model3d-steel)", "#a9b2b8");
  if (solid.surface === "coupler") return tokenColor("var(--model3d-coupler)", "#5d6469");
  return tokenColor(`var(${SURFACE_TOKENS[solid.material] ?? "--member-panel-fill"})`, "#d6d3c9");
}

function SolidMesh({
  solid,
  selected,
  theme,
  onPick,
}: {
  solid: Solid3D;
  selected: boolean;
  /** Re-resolves token colors when the app theme switches — theme changes
   * flip CSS variables without otherwise re-rendering this subtree. */
  theme: string;
  onPick(owner: string): void;
}): JSX.Element {
  const geometry = useMemo(() => {
    if (solid.kind === "shape") {
      const shape = new THREE.Shape(solid.outline.map(([x, y]) => new THREE.Vector2(x, y)));
      for (const hole of solid.holes) {
        shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
      }
      const geo = new THREE.ExtrudeGeometry(shape, {
        depth: solid.depth,
        bevelEnabled: false,
      });
      geo.translate(0, 0, solid.z0);
      return geo;
    }
    if (solid.kind === "prism") {
      // Plan polygon (x,z) → shape in (x,y), extrude along +z then rotate so
      // the extrusion becomes vertical. world_z = −shape.y, so outline is
      // pre-negated here.
      const shape = new THREE.Shape(solid.outline.map(([x, z]) => new THREE.Vector2(x, -z)));
      const geo = new THREE.ExtrudeGeometry(shape, {
        depth: solid.y1 - solid.y0,
        bevelEnabled: false,
      });
      geo.rotateX(-Math.PI / 2);
      geo.translate(0, solid.y0, 0);
      return geo;
    }
    return null;
  }, [solid]);

  const glass = solid.surface === "glass";
  // eslint-disable-next-line react-hooks/exhaustive-deps -- theme re-resolves
  // the same tokens against the new CSS variable values.
  const color = useMemo(() => solidColor(solid), [solid, theme]);
  const emissive = useMemo(
    () => (selected ? tokenColor("var(--theme-warning)", "#b45309") : "#000000"),
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
        transparent={glass}
        opacity={glass ? 0.38 : 1}
        depthWrite={!glass}
        roughness={solid.surface === "glass" ? 0.15 : 0.75}
        metalness={solid.surface === "fitting" || solid.surface === "support" ? 0.55 : 0.05}
        emissive={emissive}
        emissiveIntensity={selected ? 0.55 : 0}
      />
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
  onPick,
}: {
  scene: Scene3D;
  selection: string | null;
  theme: string;
  onPick(owner: string): void;
}): JSX.Element {
  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[4000, 6000, 5000]} intensity={1.1} />
      <directionalLight position={[-3000, 2000, -4000]} intensity={0.35} />
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
            onPick={onPick}
          />
        ))}
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
      <SceneContent scene={scene} selection={selection} theme={theme} onPick={pick} />
    </Canvas>
  );
}

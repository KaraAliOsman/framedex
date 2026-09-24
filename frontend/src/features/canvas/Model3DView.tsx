import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { PlanGeometry } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";
import { buildScene3D, type Scene3D, type Solid3D } from "./Product3DScene";
import type { MemberGeometry } from "./members";

/** §16 synchronized 3D view — the scene derives from the same product model
 * the editor renders (no separate 3D data). Orbit/pan/zoom via
 * OrbitControls; solids carry the same owner ids the 2D selection uses, so
 * clicking a member, leaf or coupler here selects it everywhere. */

/** Surface treatments keyed to the catalog material — the same families
 * the 2D member palette distinguishes (PVC light, aluminium mid, glass
 * translucent, steel for fittings). */
const SURFACE_COLORS: Record<string, string> = {
  PVC: "#e7e5dc",
  ALUMINIUM: "#848b91",
  GLASS: "#8fb8cc",
  STEEL: "#a9b2b8",
};
const FALLBACK_COLOR = "#d6d3c9";

function solidColor(solid: Solid3D): string {
  if (solid.surface === "glass") return SURFACE_COLORS.GLASS!;
  if (solid.surface === "panel") return "#b9bcc0";
  if (solid.surface === "fitting" || solid.surface === "support") return SURFACE_COLORS.STEEL!;
  if (solid.surface === "coupler") return "#5d6469";
  return SURFACE_COLORS[solid.material] ?? FALLBACK_COLOR;
}

function SolidMesh({
  solid,
  selected,
  onPick,
}: {
  solid: Solid3D;
  selected: boolean;
  onPick(owner: string): void;
}): JSX.Element {
  const geometry = useMemo(() => {
    if (solid.kind === "shape") {
      const shape = new THREE.Shape(solid.outline.map(([x, y]) => new THREE.Vector2(x, y)));
      for (const hole of solid.holes) {
        shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
      }
      return new THREE.ExtrudeGeometry(shape, { depth: solid.depth, bevelEnabled: false });
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
        color={solidColor(solid)}
        transparent={glass}
        opacity={glass ? 0.38 : 1}
        depthWrite={!glass}
        roughness={solid.surface === "glass" ? 0.15 : 0.75}
        metalness={solid.surface === "fitting" || solid.surface === "support" ? 0.55 : 0.05}
        emissive={selected ? "#b45309" : "#000000"}
        emissiveIntensity={selected ? 0.55 : 0}
      />
    </mesh>
  );
}

function SceneContent({
  scene,
  selection,
  onPick,
}: {
  scene: Scene3D;
  selection: string | null;
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
      <SceneContent scene={scene} selection={selection} onPick={pick} />
    </Canvas>
  );
}

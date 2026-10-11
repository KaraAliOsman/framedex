import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import type { Scene3D, Vec3 } from "./Product3DScene";
import {
  moduleLeafPoses,
  solidCenter,
  transformPosePoint,
  type Pose3D,
  type LeafPoseState,
} from "./poses3d";

export type CameraPreset = "interior" | "exterior" | "detail";
export type CameraShot = { position: Vec3; target: Vec3; fov: number };
export const STUDIO_LIGHTS = [
  { position: [4000, 6000, 5000] as Vec3, intensity: 1.5 },
  { position: [-3000, 2000, -4000] as Vec3, intensity: 0.6 },
  { position: [0, -2000, 2500] as Vec3, intensity: 0.25 },
];
export const STUDIO_BACKGROUND = "--studio-background";
export const STUDIO_GROUND = "--studio-ground";
export const STUDIO_WALL = "--studio-wall";
export const STUDIO_GUIDE = "--studio-guide";
export const STUDIO_TONE_MAPPING = THREE.ACESFilmicToneMapping;

export function studioColor(token: string): string {
  return typeof document === "undefined"
    ? "white"
    : getComputedStyle(document.documentElement).getPropertyValue(token).trim() || "white";
}

export function poseMatrix(pose: Pose3D): THREE.Matrix4 {
  const matrix = new THREE.Matrix4().makeTranslation(
    ...(pose.pivot.map((v, i) => v + pose.translation[i]!) as Vec3),
  );
  matrix.multiply(new THREE.Matrix4().makeRotationY(pose.rotationY));
  matrix.multiply(new THREE.Matrix4().makeRotationX(pose.rotationX));
  matrix.multiply(new THREE.Matrix4().makeTranslation(...(pose.pivot.map((v) => -v) as Vec3)));
  return matrix;
}

export function cameraShot(
  scene: Scene3D,
  preset: CameraPreset,
  aspect: number,
  exploded = false,
  states: Record<string, Record<string, LeafPoseState>> = {},
): CameraShot {
  const width = scene.bounds.max[0] - scene.bounds.min[0];
  const height = scene.bounds.max[1] - scene.bounds.min[1];
  const halfFov = (21 * Math.PI) / 180;
  const distance =
    (Math.max(height / 2, width / (2 * Math.max(aspect, 0.1))) / Math.tan(halfFov)) * 1.3 +
    (exploded ? scene.radius * 0.5 : 0);
  const exterior = preset === "exterior";
  let target: Vec3 = [0, 0, 0];
  if (preset === "detail") {
    const module = scene.modules.find((m) => m.solids.some((s) => s.surface === "handle"));
    const handle = module?.solids.find((s) => s.surface === "handle");
    if (module && handle) {
      const pose = handle.leafId
        ? moduleLeafPoses(module, states[module.moduleId] ?? {})[handle.leafId]
        : null;
      const p = new THREE.Vector3(
        ...(pose ? transformPosePoint(solidCenter(handle), pose) : solidCenter(handle)),
      );
      p.applyAxisAngle(new THREE.Vector3(0, 1, 0), module.rotationY)
        .add(new THREE.Vector3(...module.position))
        .sub(new THREE.Vector3(...scene.center));
      target = [p.x, p.y, p.z];
    }
  }
  const d = preset === "detail" ? distance * 0.4 : distance;
  return {
    position: [target[0] + d * 0.22, target[1] + d * 0.09, target[2] + d * (exterior ? -1 : 1)],
    target,
    fov: 42,
  };
}

export function studioEnvironment(
  gl: THREE.WebGLRenderer,
  scene: THREE.Scene,
  commercial = true,
): () => void {
  const pmrem = new THREE.PMREMGenerator(gl),
    room = new RoomEnvironment();
  const texture = pmrem.fromScene(room, 0.04).texture;
  room.dispose();
  scene.environment = texture;
  scene.environmentIntensity = commercial ? 0.6 : 0.45;
  return () => {
    scene.environment = null;
    texture.dispose();
    pmrem.dispose();
  };
}

/** Optional wall is a visual reference, never a survey/mounting declaration. */
export function wallBoxes(scene: Scene3D): { center: Vec3; size: Vec3 }[] {
  const [left, bottom, back] = scene.bounds.min,
    [right, top] = scene.bounds.max;
  const border = Math.max(100, scene.radius * 0.12),
    depth = Math.max(120, scene.radius * 0.1);
  return [
    {
      center: [left - border / 2, (bottom + top) / 2, back - depth / 2],
      size: [border, top - bottom + border * 2, depth],
    },
    {
      center: [right + border / 2, (bottom + top) / 2, back - depth / 2],
      size: [border, top - bottom + border * 2, depth],
    },
    {
      center: [(left + right) / 2, top + border / 2, back - depth / 2],
      size: [right - left, border, depth],
    },
    {
      center: [(left + right) / 2, bottom - border / 2, back - depth / 2],
      size: [right - left, border, depth],
    },
    {
      center: [(left + right) / 2, bottom - 12, back + 25],
      size: [right - left + 40, 24, depth * 0.6],
    },
  ];
}

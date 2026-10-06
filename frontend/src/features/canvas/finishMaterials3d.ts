import * as THREE from "three";
import type { FinishColor, ResolvedFinish } from "../../api/generated/models";

const textures = new Map<string, THREE.Texture>();
const pending = new Map<string, Promise<void>>();

export async function prepareFinishTextures(finish?: ResolvedFinish): Promise<void> {
  const paths = [
    finish?.interior.texture_path,
    finish?.exterior.texture_path,
    finish?.base?.texture_path,
  ].filter((path): path is string => Boolean(path));
  await Promise.all(
    paths.map((path) => {
      let ready = pending.get(path);
      if (!ready) {
        ready = new Promise<void>((resolve) => {
          new THREE.TextureLoader().load(
            path,
            (texture) => {
              texture.colorSpace = THREE.SRGBColorSpace;
              texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
              textures.set(path, texture);
              resolve();
            },
            undefined,
            () => resolve(),
          );
        });
        pending.set(path, ready);
      }
      return ready;
    }),
  );
}

/** Mesh color uses linear channels directly. CSS/theme colors never tint it. */
export function finishFaceMaterial(color: FinishColor): THREE.MeshStandardMaterial {
  const rgb = color.linear_rgb.map(Number);
  const map = color.texture_path ? textures.get(color.texture_path)?.clone() : undefined;
  return new THREE.MeshStandardMaterial({
    color: map
      ? new THREE.Color(1, 1, 1)
      : new THREE.Color().setRGB(rgb[0]!, rgb[1]!, rgb[2]!, THREE.LinearSRGBColorSpace),
    roughness: color.gloss === null ? 0.6 : 1 - Number(color.gloss),
    metalness: color.kind === "ANODIZED" ? 0.65 : color.kind === "RAL" ? 0.12 : 0.04,
    map,
  });
}

/** +z faces the room, −z the street. Edges expose the declared PVC base. */
export function finishGeometryMaterials(
  geometry: THREE.BufferGeometry,
  finish: ResolvedFinish,
): THREE.MeshStandardMaterial[] {
  const normals = geometry.getAttribute("normal");
  const index = geometry.getIndex();
  const count = index?.count ?? normals.count;
  geometry.clearGroups();
  let start = 0;
  let previous = -1;
  for (let at = 0; at < count; at += 3) {
    const ids = [at, at + 1, at + 2].map((offset) => (index ? index.getX(offset) : offset));
    const z = ids.reduce((sum, id) => sum + normals.getZ(id), 0) / 3;
    const face = z > 0.5 ? 1 : z < -0.5 ? 2 : 0;
    if (previous !== face) {
      if (previous >= 0) geometry.addGroup(start, at - start, previous);
      start = at;
      previous = face;
    }
  }
  geometry.addGroup(start, count - start, previous);
  return [finish.base ?? finish.exterior, finish.interior, finish.exterior].map(finishFaceMaterial);
}

export function disposeFinishMaterials(materials: THREE.MeshStandardMaterial[]): void {
  for (const material of materials) {
    material.map?.dispose();
    material.dispose();
  }
}

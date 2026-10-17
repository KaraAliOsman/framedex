import * as THREE from "three";
import type { FinishColor, ResolvedFinish } from "../../api/generated/models";

const textures = new Map<string, THREE.Texture>();
const pending = new Map<string, Promise<void>>();
let illustrativeGrain: THREE.DataTexture | undefined;

/** Neutral luminance only: the declared swatch remains the material color.
 * This visual fallback is explicitly identified as illustrative in the view. */
function grainTexture(): THREE.DataTexture {
  if (illustrativeGrain) return illustrativeGrain;
  const width = 64,
    height = 512,
    pixels = new Uint8Array(width * height * 4);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const wave =
        x + 2.4 * Math.sin((y * Math.PI * 2) / height) + 0.8 * Math.sin((y * Math.PI * 8) / height);
      const shade = Math.round(
        244 + 9 * Math.sin((wave * Math.PI) / 4) + 2 * Math.sin(wave * Math.PI),
      );
      const at = (y * width + x) * 4;
      pixels.set([shade, shade, shade, 255], at);
    }
  }
  illustrativeGrain = new THREE.DataTexture(pixels, width, height);
  illustrativeGrain.name = "Veta ilustrativa; no es una muestra del fabricante";
  illustrativeGrain.wrapS = illustrativeGrain.wrapT = THREE.RepeatWrapping;
  illustrativeGrain.needsUpdate = true;
  return illustrativeGrain;
}

export function finishTextureAvailable(path: string): boolean {
  return textures.has(path);
}

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
  const declared = color.texture_path ? textures.get(color.texture_path) : undefined;
  const map = (
    declared ?? (["FOIL", "WOOD_EFFECT"].includes(color.kind) ? grainTexture() : undefined)
  )?.clone();
  return new THREE.MeshStandardMaterial({
    color: declared
      ? new THREE.Color(1, 1, 1)
      : new THREE.Color().setRGB(rgb[0]!, rgb[1]!, rgb[2]!, THREE.LinearSRGBColorSpace),
    roughness: color.gloss === null ? 0.6 : 1 - Number(color.gloss),
    metalness: color.kind === "ANODIZED" ? 0.65 : color.kind === "RAL" ? 0.12 : 0.04,
    map: map ?? null,
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

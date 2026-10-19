import * as THREE from "three";
import type { FinishColor, ResolvedFinish } from "../../api/generated/models";

const textures = new Map<string, THREE.Texture>();
const pending = new Map<string, Promise<void>>();
const grains = new Map<string, THREE.CanvasTexture>();

/** Physical size of one texture tile, in model millimetres: wood grain runs
 * along the member, so a tile is long and narrow. Presentation only. */
const GRAIN_ALONG_MM = 1200;
const GRAIN_ACROSS_MM = 160;

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

function woodLike(color: FinishColor): boolean {
  return color.kind === "FOIL" || color.kind === "WOOD_EFFECT";
}

function seeded(text: string): () => number {
  let state = 2166136261;
  for (let index = 0; index < text.length; index++)
    state = Math.imul(state ^ text.charCodeAt(index), 16777619);
  return () => {
    state = Math.imul(state ^ (state >>> 15), 2246822507);
    state = Math.imul(state ^ (state >>> 13), 3266489909);
    return ((state ^= state >>> 16) >>> 0) / 4294967296;
  };
}

/** A procedural grain for a wood-effect finish without a manufacturer map:
 * the declared colour is the base, darker fibres run along the tile. It is a
 * presentation aid, never a claim about the manufacturer's actual pattern. */
function grainTexture(color: FinishColor): THREE.CanvasTexture | undefined {
  if (typeof document === "undefined") return undefined;
  const cached = grains.get(color.code);
  if (cached) return cached;
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 1024;
  const context = canvas.getContext("2d");
  if (!context) return undefined;
  const base = new THREE.Color()
    .setRGB(
      ...(color.linear_rgb.map(Number) as [number, number, number]),
      THREE.LinearSRGBColorSpace,
    )
    .getStyle(THREE.SRGBColorSpace);
  context.fillStyle = base;
  context.fillRect(0, 0, canvas.width, canvas.height);
  const random = seeded(color.code);
  for (let fibre = 0; fibre < 70; fibre++) {
    const x = random() * canvas.width;
    const sway = 2 + random() * 6;
    const phase = random() * Math.PI * 2;
    const dark = random() > 0.25;
    context.strokeStyle = dark ? "black" : "white";
    context.globalAlpha = dark ? 0.04 + random() * 0.1 : 0.03 + random() * 0.05;
    context.lineWidth = 0.6 + random() * 2.4;
    context.beginPath();
    for (let y = 0; y <= canvas.height; y += 16) {
      const offset = Math.sin(phase + (y / canvas.height) * Math.PI * 2) * sway;
      if (y === 0) context.moveTo(x + offset, y);
      else context.lineTo(x + offset, y);
    }
    context.stroke();
  }
  context.globalAlpha = 1;
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = 4;
  grains.set(color.code, texture);
  return texture;
}

/** Mesh color uses linear channels directly. CSS/theme colors never tint it. */
export function finishFaceMaterial(color: FinishColor): THREE.MeshStandardMaterial {
  const rgb = color.linear_rgb.map(Number);
  const loaded = color.texture_path ? textures.get(color.texture_path) : undefined;
  const source = loaded ?? (woodLike(color) ? grainTexture(color) : undefined);
  const map = source?.clone();
  if (map) map.needsUpdate = true;
  return new THREE.MeshStandardMaterial({
    color: map
      ? new THREE.Color(1, 1, 1)
      : new THREE.Color().setRGB(rgb[0]!, rgb[1]!, rgb[2]!, THREE.LinearSRGBColorSpace),
    roughness: color.gloss === null ? 0.6 : 1 - Number(color.gloss),
    metalness: color.kind === "ANODIZED" ? 0.65 : color.kind === "RAL" ? 0.12 : 0.04,
    map,
  });
}

type Presentation = { tileMm: number; grain: "ALONG" | "ACROSS" | "NONE" };
function presentationOf(color: FinishColor): Presentation | undefined {
  return (color as FinishColor & { presentation?: Presentation }).presentation;
}

/** Planar UVs in millimetres with v along the member: the grain follows each
 * profile (vertical on posts, horizontal on rails) instead of the page, and
 * keeps the same physical scale on a short sash and a long frame. A company
 * sample declares its own square tile and grain direction. */
function applyGrainUv(geometry: THREE.BufferGeometry, presentation?: Presentation): void {
  const position = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  if (!position || !normal) return;
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return;
  const alongX = box.max.x - box.min.x >= box.max.y - box.min.y;
  const uv = new Float32Array(position.count * 2);
  for (let index = 0; index < position.count; index++) {
    const x = position.getX(index),
      y = position.getY(index),
      z = position.getZ(index);
    const along = alongX ? x : y;
    const facing = Math.abs(normal.getZ(index)) > 0.5;
    const across = facing ? (alongX ? y : x) : z;
    const tile = presentation?.tileMm;
    const swap = presentation?.grain === "ACROSS";
    const u = across / (tile ?? GRAIN_ACROSS_MM);
    const v = along / (tile ?? GRAIN_ALONG_MM);
    uv[index * 2] = swap ? v : u;
    uv[index * 2 + 1] = swap ? u : v;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
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
  const faces = [finish.base ?? finish.exterior, finish.interior, finish.exterior];
  if (faces.some((color) => color.texture_path || woodLike(color)))
    applyGrainUv(geometry, faces.map(presentationOf).find(Boolean));
  return faces.map(finishFaceMaterial);
}

export function disposeFinishMaterials(materials: THREE.MeshStandardMaterial[]): void {
  for (const material of materials) {
    material.map?.dispose();
    material.dispose();
  }
}

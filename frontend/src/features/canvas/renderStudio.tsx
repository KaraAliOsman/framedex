import { useEffect, useMemo, useState } from "react";
import * as THREE from "three";

import type { PlanGeometry } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";
import { buildScene3D, type Scene3D, type Solid3D } from "./Product3DScene";
import { solidToGeometry, mapFinishUvs } from "./scene3dGeometry";
import { finishGeometryMaterials, prepareFinishTextures } from "./finishMaterials3d";
import { solidMaterial } from "./materials3d";
import type { OpeningLeafFact } from "./physicalOpenings";
import { explodeDistance, explodeLayer, moduleLeafPoses, type LeafPoseState } from "./poses3d";
import {
  cameraShot,
  poseMatrix,
  STUDIO_LIGHTS,
  STUDIO_BACKGROUND,
  STUDIO_GROUND,
  STUDIO_TONE_MAPPING,
  STUDIO_WALL,
  studioColor,
  studioEnvironment,
  wallBoxes,
  type CameraPreset,
  type CameraShot,
} from "./studioRig3d";
import type { MemberGeometry } from "./members";
import { webglAvailable } from "./webglAvailable";

/** §05-F commercial renderer — the same ProductModel scene the orbit view
 * shows, rendered offscreen under studio lighting to a PNG data URL for
 * project cards, quotation positions, portal and AI alternatives. One
 * shared WebGL context serves every thumbnail; the scene disposes its
 * geometries after each render. No geometry is ever synthesized for the
 * render that the editor didn't already declare. */

export type StudioOptions = {
  width?: number;
  height?: number;
  /** Interior/exterior face — matches the orbit view's inside toggle. */
  inside?: boolean;
  preset?: CameraPreset;
  camera?: CameraShot;
  openingFacts?: Record<string, OpeningLeafFact[]>;
  states?: Record<string, Record<string, LeafPoseState>>;
  explode?: boolean;
  wall?: boolean;
};

const RENDER_W = 640;
const RENDER_H = 480;

let renderer: THREE.WebGLRenderer | null | "unavailable" = null;

function getRenderer(): THREE.WebGLRenderer | null {
  if (renderer === "unavailable") return null;
  if (renderer) return renderer;
  if (typeof document === "undefined") return null;
  if (!webglAvailable()) {
    renderer = "unavailable";
    return null;
  }
  try {
    const canvas = document.createElement("canvas");
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = STUDIO_TONE_MAPPING;
  } catch {
    renderer = "unavailable";
  }
  return renderer instanceof THREE.WebGLRenderer ? renderer : null;
}

function tokenColor(token: string, fallback: string): string {
  const value =
    typeof window === "undefined"
      ? ""
      : getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  return value || fallback;
}

function solidMesh(solid: Solid3D): THREE.Mesh | null {
  const material = solidMaterial(solid, "commercial");
  if (solid.finish) {
    const geometry =
      solid.kind === "box" ? new THREE.BoxGeometry(...solid.size) : solidToGeometry(solid);
    if (!geometry) return null;
    if (solid.kind === "box") geometry.translate(...solid.center);
    mapFinishUvs(geometry, solid);
    return withSchematicEdges(
      new THREE.Mesh(geometry, finishGeometryMaterials(geometry, solid.finish)),
      solid,
    );
  }
  const mat = new THREE.MeshStandardMaterial({
    color: solid.hardwareColor
      ? new THREE.Color().setRGB(
          ...(solid.hardwareColor.linear_rgb.map(Number) as [number, number, number]),
          THREE.LinearSRGBColorSpace,
        )
      : tokenColor(material.colorToken, material.colorFallback),
    roughness: material.roughness,
    metalness: material.metalness,
    transparent: material.transparent,
    opacity: material.opacity,
    depthWrite: !material.glass,
  });
  if (solid.kind === "box") {
    const geo = new THREE.BoxGeometry(solid.size[0], solid.size[1], solid.size[2]);
    geo.translate(solid.center[0], solid.center[1], solid.center[2]);
    return withSchematicEdges(new THREE.Mesh(geo, mat), solid);
  }
  const geo = solidToGeometry(solid);
  return geo ? withSchematicEdges(new THREE.Mesh(geo, mat), solid) : null;
}

function withSchematicEdges(mesh: THREE.Mesh, solid: Solid3D): THREE.Mesh {
  if (
    (solid.approximate && ["box", "profile", "shape"].includes(solid.kind)) ||
    (solid.kind === "profile" && solid.miter)
  ) {
    mesh.geometry.computeBoundingBox();
    const center = mesh.geometry.boundingBox!.getCenter(new THREE.Vector3());
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(mesh.geometry, 15),
      new THREE.LineBasicMaterial({ color: tokenColor("--model3d-edge", "gray") }),
    );
    edges.scale.setScalar(1.002);
    edges.position.copy(center.multiplyScalar(1 - 1.002));
    mesh.add(edges);
  }
  return mesh;
}

export function buildThreeScene(scene: Scene3D, options: StudioOptions = {}): THREE.Group {
  const root = new THREE.Group();
  const inner = new THREE.Group();
  inner.position.set(-scene.center[0], -scene.center[1], -scene.center[2]);
  for (const module of scene.modules) {
    const group = new THREE.Group();
    group.position.set(...module.position);
    group.rotation.y = module.rotationY;
    const poses = moduleLeafPoses(
      module,
      options.explode ? {} : (options.states?.[module.moduleId] ?? {}),
    );
    for (const solid of module.solids) {
      const mesh = solidMesh(solid);
      if (!mesh) continue;
      const pose = solid.leafId ? poses[solid.leafId] : null;
      if (pose) mesh.applyMatrix4(poseMatrix(pose));
      if (options.explode) mesh.position.z += explodeLayer(solid) * explodeDistance(module.depth);
      group.add(mesh);
    }
    inner.add(group);
  }
  for (const solid of scene.couplers) {
    const mesh = solidMesh(solid);
    if (mesh) inner.add(mesh);
  }
  if (options.wall)
    for (const box of wallBoxes(scene)) {
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(...box.size),
        new THREE.MeshStandardMaterial({ color: studioColor(STUDIO_WALL), roughness: 0.92 }),
      );
      mesh.position.set(...box.center);
      inner.add(mesh);
    }
  root.add(inner);
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(scene.radius * 5, scene.radius * 4),
    new THREE.MeshStandardMaterial({ color: studioColor(STUDIO_GROUND), roughness: 0.95 }),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = scene.bounds.min[1] - scene.center[1] - 2;
  root.add(ground);
  return root;
}

/** One observer serves every StudioImage on the page — a grid of N thumbs
 * used to register N MutationObservers on documentElement. */
const themeSubscribers = new Set<(theme: string | undefined) => void>();
let themeObserver: MutationObserver | null = null;

function subscribeTheme(notify: (theme: string | undefined) => void): () => void {
  themeSubscribers.add(notify);
  if (themeObserver === null && typeof document !== "undefined") {
    themeObserver = new MutationObserver(() => {
      const theme = document.documentElement.dataset.theme;
      themeSubscribers.forEach((subscriber) => subscriber(theme));
    });
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
  }
  return () => {
    themeSubscribers.delete(notify);
    if (themeSubscribers.size === 0) {
      themeObserver?.disconnect();
      themeObserver = null;
    }
  };
}

/** The PNG bakes resolved CSS tokens — a theme change must re-render. */
function useDocumentTheme(): string | undefined {
  const [theme, setTheme] = useState<string | undefined>(() =>
    typeof document === "undefined" ? undefined : document.documentElement.dataset.theme,
  );
  useEffect(() => subscribeTheme(setTheme), []);
  return theme;
}

const cache = new Map<string, string>();
const CACHE_LIMIT = 60;

function cacheKey(
  product: ProductJson,
  members: MemberGeometry,
  plan: PlanGeometry | null | undefined,
  options: StudioOptions,
): string {
  // The PNG bakes resolved CSS tokens — the active theme must key the
  // cache or a light-theme render would survive a dark-mode switch.
  const theme = typeof document === "undefined" ? null : document.documentElement.dataset.theme;
  return JSON.stringify({ product, members, plan, options, theme });
}

export function renderStudioImage(
  product: ProductJson,
  members: MemberGeometry,
  plan?: PlanGeometry | null,
  options: StudioOptions = {},
): string | null {
  const gl = getRenderer();
  if (!gl) return null;
  const width = options.width ?? RENDER_W;
  const height = options.height ?? RENDER_H;
  const key = cacheKey(product, members, plan, options);
  const hit = cache.get(key);
  if (hit !== undefined) {
    // Refresh recency so a visible card never ages out under the cap.
    cache.delete(key);
    cache.set(key, hit);
    return hit;
  }

  const scene3d = buildScene3D(product, members, plan, options.openingFacts);
  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  for (const source of STUDIO_LIGHTS) {
    const light = new THREE.DirectionalLight(0xffffff, source.intensity);
    light.position.set(...source.position);
    scene.add(light);
  }
  const disposeEnvironment = studioEnvironment(gl, scene);
  const root = buildThreeScene(scene3d, options);
  scene.add(root);
  scene.background = new THREE.Color(studioColor(STUDIO_BACKGROUND));
  const shot =
    options.camera ??
    cameraShot(
      scene3d,
      options.preset ?? (options.inside === false ? "exterior" : "interior"),
      width / height,
      options.explode,
      options.states,
    );
  const camera = new THREE.PerspectiveCamera(shot.fov, width / height, 1, scene3d.radius * 30);
  camera.position.set(...shot.position);
  camera.lookAt(...shot.target);

  gl.setSize(width, height, false);
  gl.render(scene, camera);
  const url = gl.domElement.toDataURL("image/png");

  root.traverse((node) => {
    if (node instanceof THREE.Mesh || node instanceof THREE.LineSegments) {
      node.geometry.dispose();
      const materials = (
        Array.isArray(node.material) ? node.material : [node.material]
      ) as THREE.MeshStandardMaterial[];
      // Declared finish maps are cloned per material and disposed with it.
      for (const mat of materials) {
        mat.map?.dispose();
        mat.dispose();
      }
    }
  });
  disposeEnvironment();
  // LRU eviction — Map order is insertion order, so the first key is the
  // oldest render; clearing the whole map forces on-screen cards to re-render.
  while (cache.size >= CACHE_LIMIT) {
    const oldest = cache.keys().next().value;
    if (oldest === undefined) break;
    cache.delete(oldest);
  }
  cache.set(key, url);
  return url;
}

/** Cached commercial thumbnail — renders lazily on mount so a grid of
 * positions only pays WebGL once per product shape (the cache key is the
 * model itself). Renders a neutral panel until the first frame lands. */
export function StudioImage({
  product,
  members,
  plan,
  options,
  alt,
  className,
}: {
  product: ProductJson;
  members: MemberGeometry;
  plan?: PlanGeometry | null;
  options?: StudioOptions;
  alt: string;
  className?: string;
}): JSX.Element {
  const [url, setUrl] = useState<string | null>(null);
  const memoOptions = useMemo(
    () => options ?? {},
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [options],
  );
  const theme = useDocumentTheme();
  useEffect(() => {
    let alive = true;
    // Defer the WebGL pass until the browser is idle — a grid of cards
    // mounts first and renders scene-by-scene off the critical path.
    const schedule = (cb: () => void): (() => void) => {
      const idle = (window as { requestIdleCallback?: (cb: () => void) => number })
        .requestIdleCallback;
      if (idle) {
        const id = idle(cb);
        return () =>
          (window as { cancelIdleCallback?: (id: number) => void }).cancelIdleCallback?.(id);
      }
      const id = window.setTimeout(cb, 0);
      return () => window.clearTimeout(id);
    };
    const cancel = schedule(async () => {
      await prepareFinishTextures(members.finish);
      if (!alive) return;
      const rendered = renderStudioImage(product, members, plan, memoOptions);
      if (alive) setUrl(rendered);
    });
    return () => {
      alive = false;
      cancel();
    };
  }, [product, members, plan, memoOptions, theme]);
  if (url === null) {
    return <div className={className} aria-label={alt} role="img" />;
  }
  return <img className={className} src={url} alt={alt} />;
}

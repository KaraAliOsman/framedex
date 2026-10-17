import * as THREE from "three";
import { mergeVertices } from "three/examples/jsm/utils/BufferGeometryUtils.js";

import type { Solid3D } from "./Product3DScene";

/** Solid → ExtrudeGeometry — the one mapping shared by the live
 * Model3DView and the offscreen studio renderer, so the commercial
 * thumbnail and the orbit view can never disagree about shape.
 * Boxes stay declarative (`null` — callers use boxGeometry args). */
export function solidToGeometry(solid: Solid3D): THREE.ExtrudeGeometry | null {
  if (solid.kind === "shape") {
    const shape = new THREE.Shape(solid.outline.map(([x, y]) => new THREE.Vector2(x, y)));
    for (const hole of solid.holes) {
      shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
    }
    let geo = new THREE.ExtrudeGeometry(shape, {
      depth: solid.depth,
      bevelEnabled: false,
    });
    if (solid.smooth) {
      // ExtrudeGeometry is non-indexed — every arc chord owns its face
      // normal, so curves shade as facets. Welding duplicate vertices and
      // recomputing averages them back into a smooth run (render P2-5).
      geo = mergeVertices(geo, 1e-3) as THREE.ExtrudeGeometry;
      geo.computeVertexNormals();
    }
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
  if (solid.kind === "profile") {
    // Declared section (u face direction, v interior-positive) extruded
    // along the member run axis: a vertical post maps (u,v,a)→(u,a,v),
    // a horizontal rail →(a,u,v). `mirrorU` reflects the section inside its
    // own u-extent so asymmetric sections face the aperture consistently.
    const span = solid.a1 - solid.a0;
    if (span <= 0) return null;
    const flipped = solid.axis === "y";
    let outline = solid.outline;
    if (solid.mirrorU) {
      const us = outline.map(([u]) => u);
      const lo = Math.min(...us);
      const hi = Math.max(...us);
      outline = outline.map(([u, v]) => [lo + hi - u, v] as [number, number]);
    }
    const shape = new THREE.Shape(outline.map(([u, v]) => new THREE.Vector2(u, flipped ? -v : v)));
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: span,
      bevelEnabled: false,
    });
    if (solid.miter) {
      const positions = geo.getAttribute("position");
      const us = outline.map(([u]) => u),
        lo = Math.min(...us),
        hi = Math.max(...us);
      for (let index = 0; index < positions.count; index += 1) {
        const u = positions.getX(index),
          along = positions.getZ(index);
        const inset = solid.mirrorU ? hi - u : u - lo;
        positions.setZ(index, along + inset * (1 - (2 * along) / span));
      }
      geo.computeVertexNormals();
    }
    if (flipped) {
      geo.rotateX(-Math.PI / 2);
      geo.translate(solid.u0, solid.a0, solid.v0);
    } else {
      geo.rotateY(Math.PI / 2);
      geo.rotateX(Math.PI / 2);
      geo.translate(solid.a0, solid.u0, solid.v0);
    }
    return geo;
  }
  return null;
}

/** Grain follows each member's run. Repeat size is a drawing convention,
 * not a measured manufacturer sample or an engineering dimension. */
export function mapFinishUvs(geometry: THREE.BufferGeometry, solid: Solid3D): void {
  const positions = geometry.getAttribute("position");
  const uv = new Float32Array(positions.count * 2);
  geometry.computeBoundingBox();
  const bounds = geometry.boundingBox!;
  const size = bounds.getSize(new THREE.Vector3());
  const vertical = solid.kind === "profile" ? solid.axis === "y" : size.y >= size.x;
  for (let index = 0; index < positions.count; index += 1) {
    const x = positions.getX(index) - bounds.min.x,
      y = positions.getY(index) - bounds.min.y;
    uv[index * 2] = (vertical ? x : y) / 120;
    uv[index * 2 + 1] = (vertical ? y : x) / 900;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

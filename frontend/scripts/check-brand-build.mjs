import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";

const dist = path.resolve("dist");
const html = await readFile(path.join(dist, "index.html"), "utf8");
for (const asset of ["favicon.svg", "icon-32.png", "icon-180.png", "manifest.webmanifest"])
  assert.ok(html.includes(asset), `Production entry is missing ${asset}`);
const manifest = JSON.parse(await readFile(path.join(dist, "manifest.webmanifest"), "utf8"));
assert.equal(manifest.name, "DEKOPEN");
assert.equal(manifest.theme_color.toLowerCase(), "#075f5a");
assert.equal(manifest.background_color.toLowerCase(), "#f5f7f6");
for (const theme of ["light", "dark"]) {
  const favicon = await readFile(path.join(dist, `favicon-${theme}.svg`), "utf8");
  assert.match(favicon, /<svg/);
  assert.match(favicon, /viewBox="0 0 24 24"/);
  for (const size of [16, 32, 180, 192, 512]) {
    const png = await readFile(path.join(dist, `icon-${theme}-${size}.png`));
    assert.equal(png.subarray(1, 4).toString(), "PNG");
    assert.equal(png.readUInt32BE(16), size);
    assert.equal(png.readUInt32BE(20), size);
  }
}
for (const icon of manifest.icons) {
  const size = Number(icon.sizes.split("x")[0]);
  const png = await readFile(path.join(dist, icon.src.replace(/^\//, "")));
  assert.equal(png.readUInt32BE(16), size);
  assert.equal(png.readUInt32BE(20), size);
}
console.log("Brand production assets: entry, manifest and both icon families PASS");

import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const assets = path.resolve("dist/assets");
const forbiddenCopy = /Devin|Test Org|Próximamente|\blorem\b/i;
// Spanish “todo” is ordinary product copy. Only the unfinished-work marker
// is forbidden; model enums are covered by the rendered-route text detector.
const unfinishedCopy = /\bTODO\b/;
const developmentRoutes = /\/dev\/(?:ui|marca|correos)|\/projects\/demo\//;
for (const name of await readdir(assets)) {
  if (!name.endsWith(".js") && !name.endsWith(".css")) continue;
  let code = await readFile(path.join(assets, name), "utf8");
  // PDF.js ships this upstream renderer diagnostic. It is neither product copy
  // nor unfinished DEKOPEN work. Allow only that exact literal in its own chunk;
  // all other TODO markers and all application chunks remain subject to the gate.
  if (/^pdfjs-vendor-[\w-]+\.js$/.test(name)) {
    code = code.replaceAll("TODO: Fully support non-isolated non-knockout groups.", "");
  }
  assert.ok(
    !forbiddenCopy.test(code) && !unfinishedCopy.test(code) && !developmentRoutes.test(code),
    `Production artifact contains a demo residue: ${name}`,
  );
}
console.log("Production product assets: no demo copy or development routes PASS");

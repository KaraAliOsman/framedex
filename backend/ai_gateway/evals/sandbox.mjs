// Apply proposals through precisely the registry used by the live canvas.
// The caller sends only a product copy; no API client or save path exists here.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const root = fileURLToPath(new URL("../../..", import.meta.url));
const { build } = createRequire(resolve(root, "frontend/package.json"))("esbuild");
const built = await build({
  entryPoints: [resolve(root, "frontend/src/features/canvas/designOps.ts")],
  bundle: true,
  write: false,
  platform: "node",
  format: "esm",
  logLevel: "silent",
});
const registry = await import(
  `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString("base64")}`
);
const input = JSON.parse(readFileSync(0, "utf8"));
const product = registry.applyOperationEffects(structuredClone(input.product), input.ops ?? []);
process.stdout.write(JSON.stringify({ product, wire: registry.designAssistProduct(product) }));

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const src = path.join(root, "frontend/src");
const base = process.argv[2] ?? "7e98f71d02f31949def1383766eb2b6ee53e156c";
const entrypoints = ["index.css", "ui/ui.css", "features/canvas/canvas.css"];
const addedPrimitives = new Set([
  "ui/Controls.css",
  "ui/Structure.css",
  "ui/States.css",
  "ui/Overlays.css",
  "ui/Signature.css",
  "ui/DataTable.css",
]);
const files = new Map<string, number>();
function lines(source: string): number {
  return source.replaceAll("\r\n", "\n").replace(/\n$/, "").split("\n").length;
}
function visit(file: string): void {
  if (files.has(file)) return;
  const source = readFileSync(path.join(src, file), "utf8");
  files.set(file, lines(source));
  for (const match of source.matchAll(/@import\s+["']([^"']+)["'];/g)) {
    const target = path.posix.normalize(path.posix.join(path.posix.dirname(file), match[1]!));
    if (target.startsWith("../")) throw new Error("CSS import leaves source tree");
    visit(target);
  }
}
for (const file of entrypoints) visit(file);
const before = Object.fromEntries(
  entrypoints.map((file) => [
    file,
    lines(
      execFileSync("git", ["show", `${base}:frontend/src/${file}`], {
        cwd: root,
        encoding: "utf8",
      }),
    ),
  ]),
);
const originalLines = Object.values(before).reduce((sum, count) => sum + count, 0);
const allAfterLines = [...files.values()].reduce((sum, count) => sum + count, 0);
const addedLines = [...files]
  .filter(([file]) => addedPrimitives.has(file))
  .reduce((sum, [, count]) => sum + count, 0);
const migratedLines = allAfterLines - addedLines;
const result = {
  baseRef: base,
  method:
    "Prettier-formatted physical lines; recursively includes import entrypoints. Legacy migration and new primitive stylesheet cost are reported separately.",
  before,
  originalLines,
  migratedLegacyLinesIncludingImports: migratedLines,
  legacyReductionPercent: Number(((1 - migratedLines / originalLines) * 100).toFixed(2)),
  addedPrimitiveStylesheetLines: addedLines,
  completeScopedGraphAfterLines: allAfterLines,
  netReductionPercentIncludingPrimitives: Number(
    ((1 - allAfterLines / originalLines) * 100).toFixed(2),
  ),
  afterFiles: Object.fromEntries(files),
};
writeFileSync(
  path.join(root, "docs/redesign/captures/sistema-diseno/css-metrics.json"),
  JSON.stringify(result, null, 2),
);
console.log(JSON.stringify(result));

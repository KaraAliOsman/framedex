import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, expect, test } from "vitest";

const script = path.resolve("scripts/check-product-build.mjs");
const prefix = path.join(tmpdir(), "dekopen-product-guard-");
const temporary: string[] = [];
const diagnostic = "TODO: Fully support non-isolated non-knockout groups.";

afterEach(() => {
  for (const directory of temporary.splice(0)) {
    if (!path.resolve(directory).startsWith(prefix)) throw Error("Unexpected fixture path");
    rmSync(directory, { recursive: true });
  }
});

function check(filename: string, code: string): void {
  const directory = mkdtempSync(prefix);
  temporary.push(directory);
  const assets = path.join(directory, "dist/assets");
  mkdirSync(assets, { recursive: true });
  writeFileSync(path.join(assets, filename), code);
  execFileSync(process.execPath, [script], { cwd: directory, stdio: "pipe" });
}

test("accepts only the upstream PDF.js diagnostic in its vendor chunk", () => {
  expect(() => check("pdfjs-vendor-abc123.js", `console.info('${diagnostic}')`)).not.toThrow();
});

test.each([
  ["PdfPreview-abc123.js", `console.info('${diagnostic}')`],
  ["pdfjs-vendor-abc123.js", "console.info('TODO: finish this screen')"],
  ["pdfjs-vendor-abc123.js", "console.info('Test Org')"],
  ["pdfjs-vendor-abc123.js", "const route = '/dev/ui'"],
])("still rejects product residue in %s", (filename, code) => {
  expect(() => check(filename, code)).toThrow();
});

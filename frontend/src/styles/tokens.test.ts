/// <reference types="node" />
import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import unusedBaseline from "./unused-token-baseline.json";

const sourceRoot = path.resolve(process.cwd(), "src");
function cssFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? cssFiles(path.join(directory, entry.name))
      : entry.name.endsWith(".css")
        ? [readFileSync(path.join(directory, entry.name), "utf8")]
        : [],
  );
}
const tokens = readFileSync(path.join(sourceRoot, "styles/tokens.css"), "utf8");
const styles = cssFiles(sourceRoot);
const code = Object.values(
  import.meta.glob(["../**/*.ts", "../**/*.tsx", "!../**/*.test.*", "!../api/generated/**"], {
    query: "?raw",
    import: "default",
    eager: true,
  }),
) as string[];
const definitions = (source: string) =>
  new Set(Array.from(source.matchAll(/(--[\w-]+)\s*:/g), (match) => match[1]!));
const references = (source: string) =>
  new Set(Array.from(source.matchAll(/var\(\s*(--[\w-]+)/g), (match) => match[1]!));
const allCss = styles.join("\n");

describe("constitution tokens", () => {
  it("defines every CSS and code variable reference", () => {
    const defined = definitions(allCss);
    expect([...references(allCss + code.join("\n"))].filter((name) => !defined.has(name))).toEqual(
      [],
    );
    expect(
      [...references(".sample { color: var(--ghost); }")].filter((name) => !defined.has(name)),
    ).toEqual(["--ghost"]);
  });
  it("ratchets unused variables without hiding newly dead tokens", () => {
    const used = references(allCss + code.join("\n"));
    for (const match of code
      .join("\n")
      .matchAll(/(?:getPropertyValue|setProperty)\(["'](--[\w-]+)/g))
      used.add(match[1]!);
    const unused = [...definitions(allCss)].filter((name) => !used.has(name));
    expect(unused.filter((name) => !unusedBaseline.includes(name)).sort()).toEqual([]);
  });
  it("retains the prescribed ramps and density controls", () => {
    for (const family of [
      "g-950",
      "g-25",
      "teal-950",
      "teal-50",
      "orange-700",
      "orange-100",
      "canvas-handle",
      "t-max",
      "z-palette",
    ])
      expect(tokens).toContain(`--${family}:`);
    expect(tokens).toMatch(/\[data-density="workshop"\][\s\S]*?--control-height:\s*44px/);
    expect(tokens).toContain("font-display: swap");
  });
});

function roles(dark: boolean): Record<string, string> {
  const result: Record<string, string> = {};
  for (const match of tokens.matchAll(/([^{}]+)\{([^{}]+)\}/g)) {
    const selector = match[1]!;
    if (
      selector.includes("@") ||
      (selector.includes("data-density") &&
        !selector.includes(":root") &&
        !selector.includes('data-theme="dark"'))
    )
      continue;
    if (selector.includes('data-theme="dark"') && !dark) continue;
    if (
      selector.includes("data-theme") &&
      !selector.includes(":root") &&
      !selector.includes('data-theme="dark"')
    )
      continue;
    for (const declaration of match[2]!.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g))
      result[declaration[1]!] = declaration[2]!.trim();
  }
  return result;
}
function rgb(name: string, map: Record<string, string>): number[] {
  const value = map[name]!;
  if (value.startsWith("var(")) return rgb(value.match(/--[\w-]+/)![0], map);
  if (!/^#[\da-f]{6}$/i.test(value))
    throw new Error(`Missing opaque contrast token ${name}: ${value}`);
  return [1, 3, 5].map((index) => parseInt(value.slice(index, index + 2), 16) / 255);
}
function contrast(fg: string, bg: string, map: Record<string, string>): number {
  const luminance = (color: number[]) =>
    color
      .map((component) =>
        component <= 0.04045 ? component / 12.92 : ((component + 0.055) / 1.055) ** 2.4,
      )
      .reduce((sum, component, index) => sum + component * [0.2126, 0.7152, 0.0722][index]!, 0);
  const a = luminance(rgb(fg, map)),
    b = luminance(rgb(bg, map));
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
describe.each([false, true])("AA roles (dark=%s)", (dark) => {
  const map = roles(dark);
  for (const foreground of ["text-primary", "text-secondary", "text-small-muted", "interactive"]) {
    for (const background of [
      "bg-app",
      "surface-panel",
      "surface-card",
      "surface-sheet",
      "surface-selected",
    ]) {
      it(`${foreground} on ${background} >= 4.5`, () =>
        expect(contrast(`--${foreground}`, `--${background}`, map)).toBeGreaterThanOrEqual(4.5));
    }
  }
  for (const state of ["success", "warning", "danger", "info", "person"])
    it(`${state} label on its soft surface >= 4.5`, () =>
      expect(contrast(`--state-${state}-ink`, `--state-${state}-soft`, map)).toBeGreaterThanOrEqual(
        4.5,
      ));
  for (const background of ["interactive-fill", "interactive-hover", "interactive-pressed"])
    it(`button label on ${background} >= 4.5`, () =>
      expect(contrast("--text-on-fill", `--${background}`, map)).toBeGreaterThanOrEqual(4.5));
  // The exact g-500 ramp is retained for large annotations and drawing guides.
  // Small UI text and units use text-small-muted, checked above at 4.5.
  it("large muted annotations >= 3", () =>
    expect(contrast("--text-muted", "--surface-sheet", map)).toBeGreaterThanOrEqual(3));
  it("focus indicator >= 3", () =>
    expect(contrast("--border-focus", "--surface-sheet", map)).toBeGreaterThanOrEqual(3));
});

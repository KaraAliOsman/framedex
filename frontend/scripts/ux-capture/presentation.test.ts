import { describe, expect, it } from "vitest";
import { contrastRatio, detectPresentationFindings, type Observation } from "./presentation";

const clean: Observation = {
  sample: "Guardar",
  fontSize: 13,
  radius: 2,
  shadow: "none",
  allowedShadows: ["none", "scale"],
  backgroundImage: "none",
  filter: "none",
  backdropFilter: "none",
  textColor: "rgb(22, 28, 31)",
  backgroundColor: "rgb(255, 255, 255)",
  hasText: true,
  largeText: false,
  interactive: true,
  disabled: false,
  hasEffect: true,
  width: 44,
  height: 44,
  statusDot: false,
  primary: false,
  region: "panel",
};
describe("rendered design detectors", () => {
  it("accepts a canonical control in every density", () =>
    expect(detectPresentationFindings([clean], true)).toEqual([]));
  it.each<[Partial<Observation>, string]>([
    [{ fontSize: 10 }, "font-under-11"],
    [{ radius: 8 }, "radius-over-4"],
    [{ shadow: "outside" }, "shadow-outside-scale"],
    [{ backgroundImage: "linear-gradient(red,blue)" }, "gradient"],
    [{ backgroundImage: "conic-gradient(red,blue)" }, "gradient"],
    [{ filter: "blur(2px)" }, "blur"],
    [{ backdropFilter: "blur(2px)" }, "blur"],
    [{ textColor: "rgb(190, 190, 190)" }, "contrast-under-aa"],
    [{ width: 43 }, "touch-target-under-44"],
    [{ height: 43 }, "touch-target-under-44"],
    [{ hasEffect: false }, "interactive-without-effect"],
  ])("detects %j", (patch, kind) =>
    expect(
      detectPresentationFindings([{ ...clean, ...patch }], true).map((finding) => finding.kind),
    ).toContain(kind),
  );
  it("recognizes licensed elevation and status dots; disabled controls need no effect", () => {
    expect(
      detectPresentationFindings(
        [
          {
            ...clean,
            shadow: "scale",
            radius: 999,
            statusDot: true,
            disabled: true,
            hasEffect: false,
          },
        ],
        false,
      ),
    ).toEqual([]);
  });
  it("counts primaries within each region", () => {
    expect(
      detectPresentationFindings(
        [
          { ...clean, primary: true },
          { ...clean, primary: true },
        ],
        false,
      )[0]?.kind,
    ).toBe("multiple-primary");
    expect(
      detectPresentationFindings(
        [
          { ...clean, primary: true },
          { ...clean, primary: true, region: "other" },
        ],
        false,
      ),
    ).toEqual([]);
  });
  it("computes reference WCAG ratios", () => {
    expect(contrastRatio("#000000", "#ffffff")).toBe(21);
    expect(contrastRatio("#ffffff", "#ffffff")).toBe(1);
  });
});

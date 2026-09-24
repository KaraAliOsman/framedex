import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ProfileSection } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { SectionPreviewSvg } from "./SectionPreviewSvg";

const SECTION: ProfileSection = {
  source: "POLYGON",
  polygon: [
    { x_mm: "0", y_mm: "0" },
    { x_mm: "60", y_mm: "0" },
    { x_mm: "60", y_mm: "18" },
    { x_mm: "42", y_mm: "18" },
    { x_mm: "42", y_mm: "60" },
    { x_mm: "0", y_mm: "60" },
  ],
  depth_mm: "60.00",
  axes: [{ name: "GLAZING", y_mm: "24.00" }],
};

describe("SectionPreviewSvg", () => {
  it("draws a declared polygon with its axes and provenance label", () => {
    const { container } = render(
      <SectionPreviewSvg section={SECTION} faceWidthMm={60} material="PVC" />,
    );
    expect(container.querySelector("polygon")).not.toBeNull();
    expect(container.querySelector(".section-preview__shape--approx")).toBeNull();
    expect(container.querySelector("figure")?.getAttribute("data-provenance")).toBe("POLYGON");
    expect(screen.getByText(t("assembly.sectionDeclared"))).toBeTruthy();
    expect(screen.getByText("GLAZING")).toBeTruthy();
    expect(screen.getByText("60 × 60 mm")).toBeTruthy();
  });

  it("falls back to a dashed box labeled approximate when no section exists", () => {
    const { container } = render(
      <SectionPreviewSvg section={null} faceWidthMm={60} material="ALUMINIUM" />,
    );
    expect(container.querySelector("polygon")).toBeNull();
    expect(container.querySelector(".section-preview__shape--approx")).not.toBeNull();
    expect(container.querySelector("figure")?.getAttribute("data-provenance")).toBe("APPROXIMATE");
    expect(screen.getByText(t("assembly.sectionApproximate"))).toBeTruthy();
  });

  it("marks a manufacturer-drawing reference as exact", () => {
    render(
      <SectionPreviewSvg
        section={{ ...SECTION, source: "DXF_REFERENCE", drawing_ref: "catalog.pdf#p4" }}
        faceWidthMm={60}
        material="PVC"
      />,
    );
    expect(screen.getByText(t("assembly.sectionExact"))).toBeTruthy();
  });
});

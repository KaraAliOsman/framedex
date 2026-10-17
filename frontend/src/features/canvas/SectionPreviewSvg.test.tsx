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
    expect(screen.getByText("Vidrio")).toBeTruthy();
    expect(screen.getByText("24 mm")).toBeTruthy();
    expect(container.querySelector("svg text")).toBeNull();
    expect(screen.getByText("60 × 60 mm")).toBeTruthy();
  });

  it("shows a family illustration without invented dimensions when no section exists", () => {
    const { container } = render(
      <SectionPreviewSvg section={null} faceWidthMm={60} material="ALUMINIUM" />,
    );
    expect(container.querySelector("polygon")).toBeNull();
    expect(screen.getByRole("img", { name: "Ilustración de familia · marco" })).toBeInTheDocument();
    expect(container.querySelector("figure")?.getAttribute("data-provenance")).toBe("APPROXIMATE");
    expect(screen.getByText("Ilustración de familia · sección por confirmar")).toBeInTheDocument();
    expect(container.querySelector(".section-preview__dims")).toBeNull();
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

  it("keeps the declared section behind the catalogue recognition aid", () => {
    const { container } = render(
      <SectionPreviewSvg recognition section={SECTION} faceWidthMm={60} profileRole="SASH" />,
    );
    expect(screen.getByRole("img", { name: "Ilustración de familia · hoja" })).toBeVisible();
    expect(screen.getByText("Ilustración de familia")).toBeVisible();
    const detail = container.querySelector("details");
    expect(detail).not.toHaveAttribute("open");
    expect(detail?.querySelector(".section-preview__shape")).not.toBeNull();
    expect(screen.getByText("60 × 60 mm")).toBeInTheDocument();
  });
});

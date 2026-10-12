import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CncMemberDrawing } from "./CncMemberDrawing";
import type { CncOp, CncPreviewGeometry } from "./cncTypes";

const operation: CncOp = {
  operation_id: "end",
  kind: "END_MACHINING",
  u_mm: "1000",
  x_mm: "500",
  y_mm: "250",
  reference: "member_end",
  face: "END_EDGE",
  depth_mm: "5",
  tool_id: "end_mill",
  basis: "member_end_overlap",
  detail: {},
};
const preview: CncPreviewGeometry = {
  datum: "member_start",
  length_mm: "1000",
  section: null,
  section_fingerprint: null,
  marks: [{ operation_id: "end", x_mm: "1000", face: "END_EDGE", section_coverage: "END_PLANE" }],
};

describe("physical CNC preview", () => {
  it("places end work at the end from START and lets a keyboard control select it", () => {
    const select = vi.fn();
    const { container } = render(
      <CncMemberDrawing
        preview={preview}
        label="P01-U01-M17"
        operations={[operation]}
        selectedOp={null}
        onSelectOp={select}
      />,
    );
    expect(container.querySelector(".cnc-mark line")?.getAttribute("x1")).toBe("870");
    fireEvent.click(screen.getByRole("button", { name: /Mecanizado de extremo/ }));
    expect(select).toHaveBeenCalledWith("end");
    expect(screen.getByText(/la revisión no selló esta sección/)).toBeDefined();
    expect(container.querySelector(".cnc-section-polygon")).toBeNull();
  });

  it("does not fabricate a longitudinal coordinate or use plan XY as tool coordinates", () => {
    const { container } = render(
      <CncMemberDrawing
        preview={{ ...preview, length_mm: null }}
        label="P01-U01-M17"
        operations={[{ ...operation, u_mm: null, face: "INSIDE_FACE" }]}
        selectedOp={null}
        onSelectOp={() => {}}
      />,
    );
    expect(container.querySelector(".cnc-mark")).toBeNull();
    expect(screen.getByText(/falta el largo físico sellado/)).toBeDefined();
    expect(screen.getByRole("button", { name: /X Sin dato/ })).toBeDefined();
  });
});

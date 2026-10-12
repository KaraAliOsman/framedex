import { fireEvent, render, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { resolveMembers } from "./members";
import { makeBayTree, makeBowProduct } from "./productEditing";
import { ProductFrontSvg } from "./ProductFrontSvg";

const members = resolveMembers({
  profiles: [
    { role: "MULLION_H", sku: "POSTE-H", face_width_mm: "44.00", material: "PVC" },
    { role: "MULLION_V", sku: "POSTE-V", face_width_mm: "44.00", material: "PVC" },
  ],
} as never);

function transomProduct() {
  const product = makeBowProduct({
    moduleCount: 1,
    widthMm: 1000,
    heightMm: 1400,
    angleDeg: 0,
  });
  product.assembly.modules[0]!.tree = {
    id: "root",
    type: "SPLIT_H",
    width_mm: "1000.00",
    height_mm: "1400.00",
    split_offset_mm: "400.00",
    mullion_profile_sku: "POSTE-H",
    children: [
      makeBayTree("top", "FIXED", "4.00", "4"),
      makeBayTree("bottom", "TILT_TURN_RIGHT", "24.00", "24"),
    ],
  };
  return product;
}

describe("division grips", () => {
  it("a module groups accessible leaf controls and keeps their keyboard activation independent", () => {
    const onSelectModule = vi.fn(),
      onSelectBay = vi.fn();
    const view = render(
      <ProductFrontSvg
        product={transomProduct()}
        members={members}
        selectedId="m1"
        issues={[]}
        disabled={false}
        onSelectModule={onSelectModule}
        onSelectBay={onSelectBay}
        onAddUnit={vi.fn()}
        onCommitModuleWidth={vi.fn()}
        onCommitTotalWidth={vi.fn()}
        onCommitHeight={vi.fn()}
      />,
    );
    const module = view.getByRole("group", { name: "Módulo 1" });
    expect(module).toHaveAttribute("aria-current", "true");
    fireEvent.keyDown(module, { key: "Enter" });
    expect(onSelectModule).toHaveBeenCalledWith("m1");
    onSelectModule.mockClear();
    const leaf = within(module).getAllByRole("button")[0]!;
    fireEvent.keyDown(leaf, { key: "Enter" });
    expect(onSelectBay).toHaveBeenCalled();
    expect(onSelectModule).not.toHaveBeenCalled();
  });
  it("clicking the horizontal mullion grip selects the division, not a bay", () => {
    const onSelectDivision = vi.fn();
    const onSelectBay = vi.fn();
    const { container } = render(
      <ProductFrontSvg
        product={transomProduct()}
        members={members}
        selectedId={null}
        issues={[]}
        disabled={false}
        onSelectModule={vi.fn()}
        onSelectBay={onSelectBay}
        onSelectDivision={onSelectDivision}
        onAddUnit={vi.fn()}
        onCommitModuleWidth={vi.fn()}
        onCommitTotalWidth={vi.fn()}
        onCommitHeight={vi.fn()}
      />,
    );
    const grip = container.querySelector("rect.divider-grip.is-horizontal");
    expect(grip).not.toBeNull();
    fireEvent.click(grip!);
    expect(onSelectDivision).toHaveBeenCalledWith("m1", "root");
    expect(onSelectBay).not.toHaveBeenCalled();
  });
});

import { useState } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogDoubleReadReview } from "./CatalogDoubleReadReview";
import type { CatalogReviewRow } from "./catalogDoubleReadModel";

const row = (): CatalogReviewRow => ({
  key: "dual0",
  sheet: "Perfiles",
  row: 1,
  method: "AI",
  confidence: "REVIEW_REQUIRED",
  include: false,
  errors: [],
  warnings: [],
  double_read: { identity_unique: true },
  values: { sku: "001", depth_mm: null },
  fields: {
    sku: { comparison: "AGREED", readings: [{ value: "001" }, { value: "001" }] },
    depth_mm: {
      comparison: "REVIEW",
      readings: [
        {
          value: "60.00",
          ref: "manual.pdf · página 2",
          quote: "Profundidad 60,00 mm",
          confidence: "HIGH",
        },
        {
          value: "62.00",
          ref: "manual.pdf · página 8",
          quote: "Profundidad 62,00 mm",
          confidence: "HIGH",
        },
      ],
    },
  },
});
const sheets = [
  {
    name: "Perfiles",
    columns: [
      { key: "depth_mm", label: "Profundidad", kind: "positive", required: true, choices: null },
    ],
  },
];

function Harness({
  initial = [row()],
  disabled = false,
}: {
  initial?: CatalogReviewRow[];
  disabled?: boolean;
}) {
  const [rows, setRows] = useState(initial);
  return (
    <CatalogDoubleReadReview
      rows={rows}
      sheets={sheets}
      disabled={disabled}
      onPatch={(key, field, value) =>
        setRows((current) =>
          current.map((item) =>
            item.key === key ? { ...item, values: { ...item.values, [field]: value } } : item,
          ),
        )
      }
      onInclude={(key, include) =>
        setRows((current) =>
          current.map((item) => (item.key === key ? { ...item, include } : item)),
        )
      }
      onOpenRow={() => {}}
    />
  );
}

describe("CatalogDoubleReadReview", () => {
  it("concentrates review on disagreements while preserving both citations and exact chosen values", () => {
    render(<Harness />);
    expect(screen.getByText(/1 campo coincide/)).toBeVisible();
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
    expect(screen.getByText("manual.pdf · página 2")).toBeVisible();
    expect(screen.getByText("Profundidad 62,00 mm")).toBeVisible();
    const include = screen.getByRole("checkbox", { name: /Incluir 001/ });
    expect(include).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Usar lectura 2" }));
    expect(screen.getByRole("textbox")).toHaveValue("62.00");
    expect(screen.getAllByText("62,00")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Lectura 2 elegida" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(include).toBeEnabled();
    expect(include).not.toBeChecked();
    fireEvent.click(include);
    expect(include).toBeChecked();
  });
  it("keeps manual edits as text, including leading zeroes, and does not silently include the row", () => {
    render(<Harness />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "001.0001" } });
    expect(screen.getByRole("textbox")).toHaveValue("001.0001");
    expect(screen.getByRole("checkbox")).not.toBeChecked();
    expect(screen.getByText(/No quedan diferencias/)).toBeVisible();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "" } });
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });
  it("labels uncertain choices as workshop data and keeps the missing reading unavailable", () => {
    const initial = row();
    initial.fields.depth_mm!.readings = [{ value: "60", confidence: "LOW" }, { value: null }];
    render(<Harness initial={[initial]} />);
    expect(screen.getAllByText(/queda como dato del taller/)).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Usar lectura 2" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Usar lectura 1" })).toBeEnabled();
  });
  it("does not allow edits or inclusion in a read-only publication", () => {
    render(<Harness disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Usar lectura 1" })).toBeDisabled();
  });
  it("lets the reviewer exclude an included row after clearing its disputed value", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Usar lectura 1" }));
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "" } });
    expect(screen.getByRole("checkbox")).toBeEnabled();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });
  it("paginates 500 disagreements without mounting every editor", () => {
    render(
      <Harness
        initial={Array.from({ length: 500 }, (_, index) => ({
          ...row(),
          key: String(index),
          row: index + 1,
        }))}
      />,
    );
    expect(screen.getAllByRole("article")).toHaveLength(10);
    expect(screen.getByText("Página 1 de 50 · 500 filas")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByText("Página 2 de 50 · 500 filas")).toBeVisible();
    expect(
      within(screen.getAllByRole("article")[0]!).getByText("Perfiles · fila 11"),
    ).toBeVisible();
  });
  it("explains identity ambiguity instead of silently matching different part codes", () => {
    const initial = row();
    initial.double_read = { identity_unique: false };
    render(<Harness initial={[initial]} />);
    expect(screen.getByText(/no identifican la misma pieza/)).toBeVisible();
  });
  it("supports false as an explicit reading and structured corrections through the full editor", () => {
    const initial = row();
    initial.fields.depth_mm!.readings = [{ value: false }, { value: { clearance_mm: "0.00" } }];
    const onPatch = vi.fn(),
      onOpenRow = vi.fn();
    render(
      <CatalogDoubleReadReview
        rows={[initial]}
        sheets={sheets}
        disabled={false}
        onPatch={onPatch}
        onInclude={() => {}}
        onOpenRow={onOpenRow}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Usar lectura 1" }));
    expect(onPatch).toHaveBeenCalledWith("dual0", "depth_mm", false);
    expect(screen.getByText("0.00")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Corregir en la fila completa" }));
    expect(onOpenRow).toHaveBeenCalledWith(initial);
  });
  it("shows the empty review and keeps unknown manual data pending", () => {
    render(<Harness initial={[]} />);
    expect(screen.getByText(/Ambas lecturas coinciden/)).toBeVisible();
    expect(screen.getByText(/siguen pendientes de completar/)).toBeVisible();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});

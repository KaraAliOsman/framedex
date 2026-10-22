import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { SeriesSheet } from "../../api/generated/models";
import { CellOrigin, SeriesSheetView } from "./SeriesSheetView";
import { cell, sheetFixture } from "./seriesSheet.test.fixtures";

vi.mock("../../api/generated/dekopen", () => ({
  catalogSeriesSheet: vi.fn(),
  catalogSeriesEditCells: vi.fn(),
  catalogSeriesConfirmCells: vi.fn(),
  catalogSeriesCellHistory: vi.fn(),
  catalogSeriesEditPrices: vi.fn(),
  catalogSeriesPriceHistory: vi.fn(),
}));
const ok = <T,>(data: T) => ({ status: 200 as const, data, headers: new Headers() });
afterEach(cleanup);
beforeEach(() => vi.resetAllMocks());

async function mount(sheet: SeriesSheet, canEdit = true) {
  vi.mocked(api.catalogSeriesSheet).mockResolvedValue(ok(sheet));
  const onChanged = vi.fn();
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <SeriesSheetView
          orgId="org"
          systemId="system"
          canEdit={canEdit}
          onBack={vi.fn()}
          onChanged={onChanged}
          onAdvanced={vi.fn()}
          onTrial={vi.fn()}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  await screen.findByRole("heading", { name: sheet.tabs.rules.name });
  return onChanged;
}

describe("series sheet actions", () => {
  it("addresses a server rejection next to the exact cell and keeps the draft until corrected", async () => {
    vi.mocked(api.catalogSeriesEditCells).mockRejectedValue(
      new ApiError(400, {
        error: {
          resource: "systems",
          row_id: "system",
          fields: { rebate_depth_mm: ["Revisa este valor con el manual."] },
        },
      }),
    );
    await mount(
      sheetFixture([cell("rebate_depth_mm", "3.00"), cell("end_milling_overlap_mm", "5.00")]),
    );
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    const inputs = screen.getAllByRole("textbox").filter((item) => !item.hasAttribute("readonly"));
    fireEvent.change(inputs[0]!, { target: { value: "4,25" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("Revisa este valor con el manual.");
    expect(inputs[0]).toHaveValue("4,25");
    expect(inputs[0]).toHaveAttribute("aria-invalid", "true");
    expect(inputs[1]).not.toHaveAttribute("aria-invalid");
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeDisabled();
    fireEvent.change(inputs[0]!, { target: { value: "4,00" } });
    expect(inputs[0]).not.toHaveAttribute("aria-invalid");
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeEnabled();
  });

  it("confirms exactly the two selected suggested cells and refreshes the banner and level", async () => {
    const sheet = sheetFixture([
      cell("rebate_depth_mm", "3.00"),
      cell("end_milling_overlap_mm", "5.00"),
    ]);
    const next = {
      ...sheet,
      revision: "r2",
      cells: sheet.cells.map((item) => ({ ...item, origin: "WORKSHOP" as const })),
      usage: { ...sheet.usage, level: "QUOTABLE" as const, suggested_count: 0 },
    };
    vi.mocked(api.catalogSeriesConfirmCells).mockResolvedValue(ok(next));
    const changed = await mount(sheet);
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    for (const checkbox of screen.getAllByRole("checkbox")) fireEvent.click(checkbox);
    fireEvent.click(screen.getByRole("button", { name: "Confirmar 2 valores" }));
    await screen.findByText("Lista para cotizar");
    expect(
      screen.getByText("Verifica una ventana de prueba antes de fabricar."),
    ).toBeInTheDocument();
    expect(api.catalogSeriesConfirmCells).toHaveBeenCalledWith(
      "system",
      {
        revision: "revision-1",
        cells: sheet.cells.map(({ resource, row_id, field }) => ({ resource, row_id, field })),
      },
      { headers: { "X-Organization-ID": "org" } },
    );
    expect(changed).toHaveBeenCalledWith(next);
    expect(api.catalogSeriesSheet).toHaveBeenCalledOnce();
  });

  it("confirms one cell without confirming another suggestion", async () => {
    const sheet = sheetFixture([
      cell("rebate_depth_mm", "3.00"),
      cell("end_milling_overlap_mm", "5.00"),
    ]);
    const next = structuredClone(sheet);
    next.revision = "r2";
    next.cells[0]!.origin = "WORKSHOP";
    vi.mocked(api.catalogSeriesConfirmCells).mockResolvedValue(ok(next));
    await mount(sheet);
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    const row = screen.getAllByRole("row")[1]!;
    fireEvent.click(within(row).getByRole("button", { name: "Confirmar" }));
    await screen.findByText(/1 valor sugerido por confirmar/);
    expect(vi.mocked(api.catalogSeriesConfirmCells).mock.calls[0]![1].cells).toHaveLength(1);
  });

  it.each(["estimator", "example"])("keeps %s consultation readonly", async (mode) => {
    const sheet = sheetFixture([cell("rebate_depth_mm", "3.00")]);
    sheet.usage.is_example = mode === "example";
    await mount(sheet, mode !== "estimator");
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    expect(screen.getAllByRole("textbox").every((input) => input.hasAttribute("readonly"))).toBe(
      true,
    );
    expect(screen.queryByRole("button", { name: "Confirmar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guardar cambios" })).not.toBeInTheDocument();
    expect(api.catalogSeriesEditCells).not.toHaveBeenCalled();
  });

  it("retains a conflicting draft and prevents a tab change until the draft is resolved", async () => {
    vi.mocked(api.catalogSeriesEditCells).mockRejectedValue(new ApiError(409, {}));
    await mount(sheetFixture([cell("rebate_depth_mm", "3.00")]));
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    const input = screen.getAllByRole("textbox").find((item) => !item.hasAttribute("readonly"))!;
    fireEvent.change(input, { target: { value: "4,25" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() =>
      expect(screen.getAllByRole("alert")[0]).toHaveTextContent("La serie cambió"),
    );
    expect(input).toHaveValue("4,25");
    expect(screen.getByRole("tab", { name: "Perfiles" })).toBeDisabled();
    expect(api.catalogSeriesEditCells).toHaveBeenCalledOnce();
    expect(api.catalogSeriesSheet).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Deshacer" }));
    await waitFor(() => expect(screen.getByRole("tab", { name: "Perfiles" })).toBeEnabled());
  });

  it("opens history for the active rule and shows exact previous and current values", async () => {
    vi.mocked(api.catalogSeriesCellHistory).mockResolvedValue(
      ok({
        items: [
          {
            id: "history",
            version: 2,
            previous_id: null,
            previous_value: "3.00",
            value: "4.25",
            origin: "WORKSHOP",
            set_by: "juan",
            actor_name: "Juan",
            set_at: "2026-10-21T18:00:00Z",
            source_ref: "Comprobado en taller",
          },
        ],
      }),
    );
    await mount(sheetFixture([cell("rebate_depth_mm", "4.25")]));
    fireEvent.click(screen.getByRole("tab", { name: "Reglas" }));
    fireEvent.click(screen.getByRole("button", { name: /Historial de/ }));
    const dialog = await screen.findByRole("dialog");
    await within(dialog).findByText("Anterior: 3,00");
    expect(within(dialog).getByText("4,25")).toBeInTheDocument();
    expect(within(dialog).getByText("Juan")).toBeInTheDocument();
    expect(vi.mocked(api.catalogSeriesCellHistory).mock.calls[0]![1]).toEqual({
      resource: "systems",
      row_id: "system",
      field: "rebate_depth_mm",
    });
  });

  it("goes to the first pending value in another tab", async () => {
    await mount(sheetFixture([cell("rebate_depth_mm", "3.00")]));
    fireEvent.click(screen.getByRole("button", { name: "Ir al primero" }));
    await waitFor(() =>
      expect(screen.getByRole("tab", { name: "Reglas" })).toHaveAttribute("aria-selected", "true"),
    );
    await waitFor(() =>
      expect(
        screen.getAllByRole("textbox").find((input) => !input.hasAttribute("readonly")),
      ).toHaveFocus(),
    );
  });
});

describe("cell origin", () => {
  it("shows a manual page and the workshop actor without exposing IDs", () => {
    const { rerender } = render(
      <CellOrigin cell={cell("x", "4", { origin: "MANUAL", source_ref: "Manual · pág. 14" })} />,
    );
    expect(screen.getByText("Del manual · pág. 14")).toBeInTheDocument();
    rerender(
      <CellOrigin
        cell={cell("x", "4", {
          origin: "WORKSHOP",
          actor_name: "Juan",
          set_by: "private-id",
          set_at: "2026-10-21T18:00:00Z",
        })}
      />,
    );
    expect(screen.getByText(/Taller · Juan/)).toBeInTheDocument();
    expect(screen.queryByText(/private-id/)).not.toBeInTheDocument();
  });
});

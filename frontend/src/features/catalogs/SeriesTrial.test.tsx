import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { TrialMeasurement } from "../../api/generated/models";
import { SeriesTrial } from "./SeriesTrial";
import { cell, sheetFixture } from "./seriesSheet.test.fixtures";

vi.mock("../../api/generated/dekopen", () => ({
  catalogSeriesSheet: vi.fn(),
  catalogSeriesTrial: vi.fn(),
  catalogSeriesTrialProposals: vi.fn(),
  catalogSeriesTrialVerify: vi.fn(),
  catalogSeriesEditCells: vi.fn(),
  projectDesignOptions: vi.fn(),
}));
const ok = <T,>(data: T) => ({ status: 200 as const, data, headers: new Headers() });
const row: TrialMeasurement = {
  key: "profile_cuts:0:length_mm",
  group: "profile_cuts",
  index: 0,
  field: "length_mm",
  sku: "MARCO",
  role: "FRAME",
  quantity: 2,
  value_mm: "1206.00",
  angle_left: "45",
  angle_right: "45",
  manual_mm: null,
  difference_mm: null,
  matches: null,
};
const compared = (rows = [row]) =>
  ok({ measurements: rows, calculation_token: "server-token", result: {} });
const draft = () => screen.getByRole("textbox", { name: /Marco.*según tu manual/ });
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.projectDesignOptions).mockResolvedValue(
    ok({
      compatible_openings: ["FIXED", "TURN_LEFT"],
      colors: ["WHITE"],
      glass_specs: [{ sku: "G24", spec: "4-16-4", total_thickness_mm: "24", compatible: true }],
    }) as never,
  );
  vi.mocked(api.catalogSeriesTrial).mockResolvedValue(compared());
  vi.mocked(api.catalogSeriesSheet).mockResolvedValue(ok(sheetFixture()));
});
function mount(suggested = false) {
  const onSaved = vi.fn(),
    onVerified = vi.fn();
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <SeriesTrial
        orgId="org"
        sheet={sheetFixture(suggested ? [cell("sash_overlap_mm", "8")] : [])}
        onSaved={onSaved}
        onVerified={onVerified}
        onComplete={vi.fn()}
      />
    </QueryClientProvider>,
  );
  return { onSaved, onVerified };
}

describe("workshop trial", () => {
  it("does not verify an empty result or reuse a previous confirmation after a failed refresh", async () => {
    mount();
    vi.mocked(api.catalogSeriesTrial).mockResolvedValueOnce(compared([]));
    fireEvent.click(await screen.findByRole("button", { name: "Calcular ventana" }));
    await screen.findByText(/El motor no devolvió piezas/);
    expect(screen.getByRole("checkbox", { name: /He revisado/ })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Comparar medidas" }));
    await screen.findByRole("textbox", { name: /Marco.*según tu manual/ });
    fireEvent.click(screen.getByRole("checkbox", { name: /He revisado/ }));
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeEnabled();
    vi.mocked(api.catalogSeriesTrial).mockRejectedValueOnce(new Error("offline"));
    fireEvent.click(screen.getByRole("button", { name: "Comparar medidas" }));
    await screen.findByRole("alert");
    expect(screen.getByRole("checkbox", { name: /He revisado/ })).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeDisabled();
    expect(api.catalogSeriesTrialVerify).not.toHaveBeenCalled();
  });
  it("starts with the declared defaults and obtains every measured value from the server", async () => {
    mount();
    await screen.findByRole("button", { name: "Calcular ventana" });
    expect(screen.getByRole("combobox", { name: "Apertura" })).toHaveValue("TURN_LEFT");
    expect(api.catalogSeriesTrial).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Calcular ventana" }));
    await screen.findByRole("textbox", { name: /Marco.*según tu manual/ });
    expect(api.catalogSeriesTrial).toHaveBeenCalledWith(
      "system",
      expect.objectContaining({
        nominal_width_mm: "1200",
        nominal_height_mm: "1100",
        parametric_tree: expect.objectContaining({
          opening_type: "TURN_LEFT",
          glass_thickness_mm: "24",
        }),
      }),
      expect.anything(),
    );
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeDisabled();
  });
  it("requires explicit review and confirmation of the suggested values, and invalidates on changed input", async () => {
    const { onVerified } = mount(true);
    fireEvent.click(await screen.findByRole("button", { name: "Calcular ventana" }));
    await screen.findByRole("checkbox", { name: /He revisado/ });
    fireEvent.click(screen.getByRole("checkbox", { name: /He revisado/ }));
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: /Confirmo como datos del taller/ }));
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeEnabled();
    fireEvent.change(draft(), { target: { value: "1206,00" } });
    expect(screen.getByRole("checkbox", { name: /He revisado/ })).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeDisabled();
    vi.mocked(api.catalogSeriesTrial).mockResolvedValue(
      compared([{ ...row, manual_mm: "1206.00", difference_mm: "0", matches: true }]),
    );
    fireEvent.click(screen.getByRole("button", { name: "Comparar medidas" }));
    await screen.findByText("Coincide");
    fireEvent.click(screen.getByRole("checkbox", { name: /He revisado/ }));
    vi.mocked(api.catalogSeriesTrialVerify).mockResolvedValue({
      status: 201,
      data: {
        id: "ref",
        technical_hash: "hash",
        verified_by: "owner",
        verified_at: "2026-10-21T12:00:00Z",
      },
      headers: new Headers(),
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar ventana de prueba" }));
    await screen.findByRole("status");
    expect(api.catalogSeriesTrialVerify).toHaveBeenCalledWith(
      "system",
      expect.objectContaining({
        calculation_token: "server-token",
        confirm_suggested: true,
        confirmed: true,
        manual_values: { [row.key]: "1206" },
      }),
      expect.anything(),
    );
    expect(onVerified).toHaveBeenCalledOnce();
  });
  it("keeps a discrepant manual value and never confirms after a rejected calculation", async () => {
    mount();
    fireEvent.click(await screen.findByRole("button", { name: "Calcular ventana" }));
    await screen.findByRole("textbox", { name: /Marco.*según tu manual/ });
    fireEvent.change(draft(), { target: { value: "1208,01" } });
    vi.mocked(api.catalogSeriesTrial).mockRejectedValue(
      new ApiError(422, { error: { detail: "Revisa la medida del manual." } }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Comparar medidas" }));
    await screen.findByRole("alert");
    expect(draft()).toHaveValue("1208,01");
    expect(screen.getByRole("button", { name: "Confirmar ventana de prueba" })).toBeDisabled();
  });
  it("applies only the human-selected exact proposal and recalculates the whole window", async () => {
    mount();
    fireEvent.click(await screen.findByRole("button", { name: "Calcular ventana" }));
    await screen.findByRole("textbox", { name: /Marco.*según tu manual/ });
    fireEvent.change(draft(), { target: { value: "1208,00" } });
    const changes = ["welding_loss_per_end_mm", "joint_deduction_per_end_mm"].map((field) => ({
      resource: "articles" as const,
      row_id: "frame",
      field,
      value: "4.00",
    }));
    vi.mocked(api.catalogSeriesTrialProposals).mockResolvedValue(
      ok({
        revision: "r2",
        items: changes.map((change, index) => ({
          change,
          label: `Regla ${index + 1}`,
          previous: "3",
          value: "4",
          measurements: [{ ...row, value_mm: "1208" }],
          result: {},
        })),
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Ajustar regla" }));
    await screen.findByRole("radio", { name: /Regla 2/ });
    expect(api.catalogSeriesEditCells).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("radio", { name: /Regla 2/ }));
    vi.mocked(api.catalogSeriesEditCells).mockResolvedValue(ok(sheetFixture()));
    vi.mocked(api.catalogSeriesTrial).mockResolvedValue(
      compared([
        { ...row, value_mm: "1208", manual_mm: "1208.00", difference_mm: "0", matches: true },
      ]),
    );
    fireEvent.click(screen.getByRole("button", { name: "Aplicar y recalcular" }));
    await screen.findByText("Coincide");
    expect(api.catalogSeriesEditCells).toHaveBeenCalledWith(
      "system",
      { revision: "r2", changes: [changes[1]] },
      expect.anything(),
    );
    await waitFor(() => expect(api.catalogSeriesTrial).toHaveBeenCalledTimes(2));
  });
});

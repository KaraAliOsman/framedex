import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { positionsDesignAlternatives } from "../../api/generated/dekopen";
import { AlternativesPanel } from "./AlternativesPanel";
import { resolveMembers } from "./members";
import type { Opening } from "./intentEditing";
import { makeBayTree, type ProductJson } from "./productEditing";

vi.mock("../../api/generated/dekopen", () => ({ positionsDesignAlternatives: vi.fn() }));
const alternativesMock = vi.mocked(positionsDesignAlternatives);

const MEMBERS = resolveMembers(undefined);

function candidateProduct(opening: string, modules = 1): ProductJson {
  return {
    version: "product-v2",
    assembly: {
      modules: Array.from({ length: modules }, (_, index) => ({
        id: `m${index + 1}`,
        width_mm: "1200",
        height_mm: "1500",
        tree: makeBayTree(`m${index + 1}`, opening as Opening, "4.00", "4", "GLASS-4MM"),
      })),
      couplings: [],
    },
  };
}

function renderPanel(overrides: Partial<Parameters<typeof AlternativesPanel>[0]> = {}) {
  const onUse = vi.fn();
  const props = {
    organizationId: "org-1",
    positionId: "pos-1",
    systemId: "system-a",
    product: candidateProduct("FIXED"),
    members: MEMBERS,
    disabled: false,
    onUse,
    catalogKey: "G4|C1|5",
    ...overrides,
  };
  return { props, onUse, ...render(<AlternativesPanel {...props} />) };
}

function successResponse() {
  return {
    status: 200,
    headers: new Headers(),
    data: {
      audit_id: "a1",
      model: "mimo",
      credits_debited: 3,
      alternatives: [
        {
          label: "Paño fijo",
          rationale: "simple",
          product: candidateProduct("FIXED"),
          metrics: {
            module_count: 1,
            openings: ["FIXED"],
            glass_area_m2: "2.80",
            leaf_weight_kg: "34.00",
            status: "VALID",
            warnings: [] as string[],
          },
        },
      ],
      rejected: [{ label: "Imposible", reasons: ["aperturas_invalidas"] }],
      notes: "una opción",
    },
  };
}

describe("AlternativesPanel", () => {
  beforeEach(() => alternativesMock.mockReset());

  it("posts the brief and renders a usable candidate card", async () => {
    alternativesMock.mockResolvedValue(successResponse() as never);
    const { onUse } = renderPanel();
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "algo simple" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Generar alternativas/i }));
    await waitFor(() => expect(alternativesMock).toHaveBeenCalledTimes(1));
    const payload = alternativesMock.mock.calls[0]![1];
    expect(payload.brief).toBe("algo simple");
    expect(payload.system_id).toBe("system-a");
    expect(payload.operation_key).toBeTruthy();

    expect(await screen.findByText("Paño fijo")).toBeTruthy();
    expect(screen.getByText("simple")).toBeTruthy();
    expect(screen.getByText(/2\.80 m²/)).toBeTruthy();
    expect(screen.getByText(/Imposible: aperturas_invalidas/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Usar" }));
    expect(onUse).toHaveBeenCalledTimes(1);
    const adopted = onUse.mock.calls[0]![0];
    expect(adopted.assembly.modules[0]!.tree.opening_type).toBe("FIXED");
  });

  it("flags a manufacturing-incomplete candidate without blocking it", async () => {
    const response = successResponse();
    response.data.alternatives[0]!.metrics.status = "MANUFACTURING_INCOMPLETE";
    response.data.alternatives[0]!.metrics.warnings = ["coupler_profile_missing"];
    alternativesMock.mockResolvedValue(response as never);
    renderPanel();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "bow" } });
    fireEvent.click(screen.getByRole("button", { name: /Generar alternativas/i }));
    expect(await screen.findByText(/le faltan datos del catálogo/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Usar" })).toBeTruthy();
  });

  it("drops the result when the system changes mid-flight", async () => {
    let resolve!: (value: ReturnType<typeof successResponse>) => void;
    alternativesMock.mockReturnValue(new Promise((r) => (resolve = r)) as never);
    const { props, rerender } = renderPanel();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "corredera" } });
    fireEvent.click(screen.getByRole("button", { name: /Generar alternativas/i }));
    expect(alternativesMock).toHaveBeenCalledTimes(1);
    rerender(<AlternativesPanel {...props} systemId="system-b" />);
    resolve(successResponse());
    await waitFor(() => expect(screen.queryByText("Paño fijo")).toBeNull());
  });

  it("marks cards stale and disables Usar when the canvas changes", async () => {
    alternativesMock.mockResolvedValue(successResponse() as never);
    const { props, rerender } = renderPanel();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "fijo" } });
    fireEvent.click(screen.getByRole("button", { name: /Generar alternativas/i }));
    expect(await screen.findByText("Paño fijo")).toBeTruthy();

    rerender(<AlternativesPanel {...props} product={candidateProduct("AWNING")} />);
    expect(screen.getByText(/El producto cambió/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Usar" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("requires a saved position before generating", () => {
    renderPanel({ positionId: null });
    expect(screen.getByText(/Guarda el vano/)).toBeTruthy();
    expect(alternativesMock).not.toHaveBeenCalled();
  });
});

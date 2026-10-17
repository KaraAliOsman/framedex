import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type {
  AiAgentStep,
  ProjectResponse,
  PriceResponse,
  QuotationPreview,
} from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import {
  pricingApply,
  pricingPreview,
  projectsRetrieve,
  quotationPreparePreview,
} from "../../api/generated/dekopen";
import { QuotationStep, type Preparation } from "./QuotationStep";

vi.mock("../../api/generated/dekopen", () => ({
  pricingApply: vi.fn(),
  pricingPreview: vi.fn(),
  projectsRetrieve: vi.fn(),
  quotationPreparePreview: vi.fn(),
}));
afterEach(cleanup);
const date = "2026-10-17T10:00:00Z";
const position = {
  id: "position",
  position_index: 1,
  quantity: 2,
  location_tag: "Living",
  price_net: "100",
  updated_at: date,
};
const project = {
  id: "project",
  code: "P-1",
  name: "Casa",
  status: "DRAFT",
  current_revision: "REV-A",
  updated_at: date,
  pricing_current: false,
  current_pricing_operation_id: null,
  currency: "CLP",
  total_price_net: "100",
  total_price_tax: "19",
  total_price_gross: "119",
  positions: [position],
} as unknown as ProjectResponse;
const price = {
  id: "price",
  state: "PREVIEW",
  currency: "CLP",
  project_net: "100",
  project_tax: "19",
  project_gross: "119",
  lines: [{ position_index: 1, line_net: "100" }],
} as PriceResponse;
const pdf = { id: "pdf", pdf_url: "http://127.0.0.1/private-preview.pdf" } as QuotationPreview;
function preparation(): Preparation {
  return {
    valid: true,
    project_id: "project",
    project_code: "P-1",
    project_name: "Casa",
    currency: "CLP",
    totals: { net: "100", tax: "19", gross: "119" },
    lines: [{ index: 1, location: "Living", quantity: 2, net: "100" }],
    price_applied: false,
    request: {
      project_id: "project",
      currency: "CLP",
      pricing_mode: "COST_PLUS_MARGIN",
      effective_date: "2026-10-17",
      reason: "Preparación",
    },
    basis: {
      updated_at: date,
      revision: "REV-A",
      positions: [{ id: "position", updated_at: date }],
    },
    missing: [],
    scope: "Revisa la propuesta.",
  };
}
function show(value = preparation()) {
  const onOpen = vi.fn();
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <QuotationStep
        step={{ kind: "quotation", simulation: value } as unknown as AiAgentStep}
        organizationId="org"
        onOpen={onOpen}
      />
    </QueryClientProvider>,
  );
  return onOpen;
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(projectsRetrieve).mockResolvedValue({
    status: 200,
    data: project,
    headers: new Headers(),
  });
  vi.mocked(pricingPreview).mockResolvedValue({ status: 200, data: price, headers: new Headers() });
  vi.mocked(pricingApply).mockResolvedValue({
    status: 200,
    data: { ...price, state: "APPLIED" },
    headers: new Headers(),
  });
  vi.mocked(quotationPreparePreview).mockResolvedValue({
    status: 201,
    data: pdf,
    headers: new Headers(),
  });
});

it("confirms the reviewed price and prepares a private PDF without routing through pricing", async () => {
  const onOpen = show();
  expect(screen.getByText("Alcance: obra completa")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByRole("button", { name: "Ver el PDF preparado" });
  expect(pricingApply).toHaveBeenCalledWith("price", expect.objectContaining({ confirmed: true }), {
    headers: { "X-Organization-ID": "org" },
  });
  expect(quotationPreparePreview).toHaveBeenCalledWith(
    "project",
    { pricing_operation_id: "price" },
    expect.anything(),
  );
  expect(onOpen).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Revisar y emitir" }));
  expect(onOpen).toHaveBeenCalledWith("/projects/project?section=quote", {
    quotationPreview: { organizationId: "org", projectId: "project", previewId: "pdf" },
  });
});

it("requires a new review when a position changed even if the total stayed equal", async () => {
  vi.mocked(projectsRetrieve).mockResolvedValue({
    status: 200,
    data: {
      ...project,
      positions: [{ ...project.positions![0]!, updated_at: "2026-10-17T11:00:00Z" }],
    },
    headers: new Headers(),
  });
  show();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByText(/Revisa la muestra actualizada/);
  expect(pricingApply).not.toHaveBeenCalled();
  expect(quotationPreparePreview).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByRole("button", { name: "Ver el PDF preparado" });
  expect(pricingPreview).toHaveBeenCalledTimes(1);
});

it("recognizes the same reviewed basis after JSONB key ordering and datetime serialization", async () => {
  const value = preparation();
  value.basis = {
    positions: [{ updated_at: "2026-10-17 10:00:00+00:00", id: "position" }],
    revision: "REV-A",
    updated_at: "2026-10-17 10:00:00.000000+00:00",
  };
  show(value);
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByRole("button", { name: "Ver el PDF preparado" });
  expect(pricingApply).toHaveBeenCalledTimes(1);
  expect(screen.queryByText(/Revisa la muestra actualizada/)).not.toBeInTheDocument();
});

it("preserves microsecond differences when deciding whether the review is stale", async () => {
  const value = preparation();
  value.basis!.updated_at = "2026-10-17T10:00:00.000001Z";
  show(value);
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByText(/Revisa la muestra actualizada/);
  expect(pricingApply).not.toHaveBeenCalled();
});

it("shows a changed sale amount before applying it", async () => {
  vi.mocked(pricingPreview).mockResolvedValue({
    status: 200,
    data: { ...price, project_gross: "120" },
    headers: new Headers(),
  });
  show();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByText(/Revisa la muestra actualizada/);
  expect(screen.getByText("$120")).toBeInTheDocument();
  expect(pricingApply).not.toHaveBeenCalled();
});

it("keeps a required owner approval pending", async () => {
  vi.mocked(pricingPreview).mockResolvedValue({
    status: 200,
    data: { ...price, state: "PENDING" },
    headers: new Headers(),
  });
  show();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByRole("button", { name: "Abrir aprobación de precio" });
  expect(pricingApply).not.toHaveBeenCalled();
  expect(quotationPreparePreview).not.toHaveBeenCalled();
});

it("preserves the applied price and names a real missing field when PDF preparation fails", async () => {
  vi.mocked(quotationPreparePreview).mockRejectedValue(
    new ApiError(422, { error: { detail: "Falta la dirección de obra." } }),
  );
  show();
  fireEvent.click(screen.getByRole("button", { name: "Usar este precio y preparar PDF" }));
  await screen.findByText("Falta la dirección de obra.");
  expect(screen.getByRole("button", { name: "Preparar PDF" })).toBeEnabled();
  expect(pricingApply).toHaveBeenCalledTimes(1);
});

it("reuses the current applied operation and ignores a rapid second click", async () => {
  const value = { ...preparation(), price_applied: true };
  vi.mocked(projectsRetrieve).mockResolvedValue({
    status: 200,
    data: { ...project, pricing_current: true, current_pricing_operation_id: "applied-price" },
    headers: new Headers(),
  });
  show(value);
  const button = screen.getByRole("button", { name: "Preparar PDF" });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() => expect(quotationPreparePreview).toHaveBeenCalledTimes(1));
  expect(pricingPreview).not.toHaveBeenCalled();
  expect(pricingApply).not.toHaveBeenCalled();
});

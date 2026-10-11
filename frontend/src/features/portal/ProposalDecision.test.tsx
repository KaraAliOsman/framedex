import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  portalQuoteRetrieve,
  portalQuoteDecide,
  portalPaymentReturn,
  portalQuotePay,
} from "../../api/generated/dekopen";
import type { PortalOption, PortalQuote } from "../../api/generated/models";
import { PortalQuotePage } from "./PortalQuotePage";

vi.mock("../../api/generated/dekopen", () => ({
  portalQuoteRetrieve: vi.fn(),
  portalQuoteDecide: vi.fn(),
  portalQuotePay: vi.fn(),
  portalPaymentReturn: vi.fn(),
}));
afterEach(cleanup);
beforeEach(() => vi.resetAllMocks());

function option(revision: string, total: string): PortalOption {
  return {
    revision_code: revision,
    snapshot_sha256: revision === "REV-A" ? "a".repeat(64) : "b".repeat(64),
    currency: "CLP",
    total_price_gross: total,
    display_total_gross: total,
    rounding_adjustment: "0",
    price_cause: null,
    price_source: "Importe sellado de la prueba",
    quote_pdf_url: null,
    payment_terms: null,
    notes_commercial: null,
    consent_text: `Acepto ${revision} por $${total} y sus condiciones`,
    positions: [
      {
        id: revision === "REV-A" ? "chosen-position" : "base-position",
        position_index: 1,
        quantity: 2,
        typology: "FIXED",
        location_tag: "Living",
        width_mm: "1000",
        height_mm: "1000",
        color_interior: "WHITE",
        color_exterior: "WHITE",
        glass_specs: [],
        price_net: total,
        discount_pct: "0",
        parametric_tree: null,
        unit_price_gross: "50",
        line_price_gross: total,
        unit_rounding_adjustment: "0",
        finish: null,
      },
    ],
    extras: [],
    commercial_terms: {},
    payment_schedule: [],
  };
}
function proposal(changes: Partial<PortalQuote> = {}): PortalQuote {
  const main = option("REV-B", "200");
  return {
    schema: "portal_quote_v2",
    organization: {
      name: "Fabricante DEMO",
      commercial_name: "Ventanas del Sur",
      tax_id: null,
      brand_address: "Puerto Varas",
      brand_phone: "+56900000000",
      brand_email: "fabricante@example.test",
      brand_logo_url: null,
    },
    project_code: "P-000001",
    project_name: "Casa Los Robles",
    client_name: "Ana",
    revision_code: "REV-B",
    selected_revision: "REV-B",
    offering_sha256: "b".repeat(64),
    emitted_at: "2026-10-11T10:00:00Z",
    currency: "CLP",
    payment_terms: null,
    notes_commercial: null,
    total_price_net: "168",
    total_price_tax: "32",
    total_price_gross: "200",
    extras: [],
    positions: main.positions,
    options: [main, option("REV-A", "100")],
    display_total_gross: "200",
    payment: { status: "PENDING", collected: "0", balance: "200", simulated: false },
    payment_provider: null,
    payment_url: null,
    valid_until: "2026-10-23",
    validity_expired: false,
    superseded: false,
    expires_at: "2999-01-01T00:00:00Z",
    approval_status: "PENDING",
    decided_by: null,
    decided_at: null,
    decided_note: null,
    quote_pdf_url: null,
    ...changes,
  };
}
function show(quote: PortalQuote, url = "/cotizacion/test") {
  vi.mocked(portalQuoteRetrieve).mockResolvedValue({
    status: 200,
    data: quote,
    headers: new Headers(),
  });
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/cotizacion/:token" element={<PortalQuotePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test("selecting an alternative resets consent and submits its sealed identity", async () => {
  show(proposal());
  await screen.findByText("Su decisión");
  fireEvent.click(screen.getByRole("checkbox"));
  const alternative = screen
    .getByRole("heading", { name: "Revisión A · Alternativa" })
    .closest("article")!;
  fireEvent.click(within(alternative).getByRole("button", { name: "Elegir esta opción" }));
  expect(screen.getByRole("checkbox")).not.toBeChecked();
  fireEvent.change(screen.getByLabelText("Nombre completo"), { target: { value: "Ana Pérez" } });
  fireEvent.change(screen.getByLabelText("RUT", { exact: true }), {
    target: { value: "12.345.678-0" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Aprobar propuesta" }));
  expect(portalQuoteDecide).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("RUT", { exact: true }), {
    target: { value: "12.345.678-5" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  vi.mocked(portalQuoteDecide).mockResolvedValue({
    status: 200,
    data: proposal({ approval_status: "APPROVED", selected_revision: "REV-A" }),
    headers: new Headers(),
  });
  fireEvent.click(screen.getByRole("button", { name: "Aprobar propuesta" }));
  await waitFor(() =>
    expect(portalQuoteDecide).toHaveBeenCalledWith(
      "test",
      expect.objectContaining({
        selected_revision: "REV-A",
        expected_offering_sha256: "b".repeat(64),
        expected_selected_sha256: "a".repeat(64),
        consent_text: "Acepto REV-A por $100 y sus condiciones",
        confirmed: true,
      }),
    ),
  );
  expect(await screen.findByText("Propuesta aprobada")).toBeVisible();
  expect(screen.getByText(/Para Ana/)).toHaveTextContent("Oferta · Revisión B");
  expect(screen.getByRole("heading", { name: "Solución elegida · Revisión A" })).toBeVisible();
  expect(screen.queryByRole("button", { name: "Rechazar propuesta" })).not.toBeInTheDocument();
});

test("changes point to the selected sealed position and require a comment", async () => {
  show(proposal());
  const button = await screen.findByRole("button", { name: "Solicitar cambios" });
  fireEvent.click(button);
  expect(portalQuoteDecide).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Posición a revisar (opcional)"), {
    target: { value: "base-position" },
  });
  fireEvent.change(screen.getByLabelText("Comentario"), {
    target: { value: "Necesito otro vidrio en Living" },
  });
  vi.mocked(portalQuoteDecide).mockResolvedValue({
    status: 200,
    data: proposal({ approval_status: "CHANGES_REQUESTED" }),
    headers: new Headers(),
  });
  fireEvent.click(button);
  await waitFor(() =>
    expect(portalQuoteDecide).toHaveBeenCalledWith(
      "test",
      expect.objectContaining({
        decision: "CHANGES_REQUESTED",
        position_id: "base-position",
        note: "Necesito otro vidrio en Living",
      }),
    ),
  );
  expect(await screen.findByText("Cambios solicitados")).toBeVisible();
});

test.each([
  { superseded: true, approval_status: "APPROVED" },
  { validity_expired: true, approval_status: "APPROVED" },
  { approval_status: "PENDING" },
  { approval_status: "CHANGES_REQUESTED" },
  { approval_status: "DECLINED" },
  {
    approval_status: "APPROVED",
    payment: { status: "PAID", collected: "200", balance: "0", simulated: true },
  },
])("unavailable proposals have no pay action: %j", async (changes) => {
  show(proposal(changes));
  await screen.findByText("Ventanas del Sur");
  expect(screen.queryByRole("button", { name: /Pagar/ })).not.toBeInTheDocument();
});

test("a stale decision rereads the already decided proposal without another action", async () => {
  show(proposal());
  await screen.findByText("Su decisión");
  vi.mocked(portalQuoteDecide).mockResolvedValue({
    status: 409,
    data: { error: { code: "quote_already_decided", detail: "Ya respondida" } },
    headers: new Headers(),
  });
  vi.mocked(portalQuoteRetrieve).mockResolvedValue({
    status: 200,
    data: proposal({ approval_status: "DECLINED" }),
    headers: new Headers(),
  });
  fireEvent.click(screen.getByRole("button", { name: "Rechazar propuesta" }));
  expect(await screen.findByText("Propuesta rechazada")).toBeVisible();
  expect(screen.queryByText("Su decisión")).not.toBeInTheDocument();
  expect(portalQuoteDecide).toHaveBeenCalledTimes(1);
});

test("payment return reports rejection from verified status, never from navigation", async () => {
  vi.mocked(portalPaymentReturn).mockResolvedValue({
    status: 200,
    data: {
      status: "FAILED",
      portal_path: "/cotizacion/test?pago=context&access=access",
      simulated: true,
      amount: "100",
    },
    headers: new Headers(),
  });
  show(proposal({ approval_status: "APPROVED" }), "/cotizacion/test?pago=context&access=access");
  expect(await screen.findByText("El pago fue rechazado. El saldo no se descontó.")).toBeVisible();
  expect(portalPaymentReturn).toHaveBeenCalledWith("context", { access: "access" });
});

test("a sealed CLP balance with decimal scale prefills a payable integer", async () => {
  vi.mocked(portalQuotePay).mockRejectedValue(new Error("Proveedor de prueba no disponible"));
  show(
    proposal({
      approval_status: "APPROVED",
      payment_provider: "SIMULATED",
      payment: { status: "PENDING", collected: "0.0000", balance: "200.0000", simulated: false },
    }),
  );
  const amount = await screen.findByLabelText("Monto a pagar (CLP)");
  expect(amount).toHaveValue("200");
  fireEvent.change(screen.getByLabelText("Correo para el comprobante"), {
    target: { value: "ana@example.test" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Pagar en modo de prueba" }));
  await waitFor(() =>
    expect(portalQuotePay).toHaveBeenCalledWith(
      "test",
      expect.objectContaining({
        amount: "200",
        payer_email: "ana@example.test",
        operation_key: expect.stringMatching(/^[0-9a-f-]{36}$/),
      }),
    ),
  );
});

test("an existing charge resumes its capability without creating another payment", async () => {
  show(
    proposal({
      approval_status: "APPROVED",
      payment_provider: "SIMULATED",
      payment_url: "/pago/simulado/existing?token=capability",
    }),
  );
  const resume = await screen.findByRole("link", { name: "Continuar pago pendiente" });
  expect(resume).toHaveAttribute("href", "/pago/simulado/existing?token=capability");
  expect(screen.queryByLabelText("Monto a pagar (CLP)")).not.toBeInTheDocument();
  expect(portalQuotePay).not.toHaveBeenCalled();
});

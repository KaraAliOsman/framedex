import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { portalQuoteRetrieve } from "../../api/generated/dekopen";
import type { PortalQuote } from "../../api/generated/models";
import { PortalQuotePage } from "./PortalQuotePage";

vi.mock("../../api/generated/dekopen", () => ({
  portalQuoteRetrieve: vi.fn(),
  portalQuoteDecide: vi.fn(),
}));
afterEach(cleanup);

test.each(["APPROVED", "DECLINED", "PENDING"])(
  "a replaced %s proposal preserves its decision and cannot accept another",
  async (status) => {
    const quote: PortalQuote = {
      schema: "DOC-01",
      organization: {
        name: "Taller DEMO",
        tax_id: null,
        commercial_name: null,
        brand_address: null,
        brand_phone: null,
        brand_email: null,
        brand_logo_url: null,
      },
      project_code: "P-000001",
      project_name: "Obra DEMO",
      client_name: "Cliente",
      revision_code: "REV-A",
      emitted_at: "2026-10-09T15:00:00Z",
      currency: "CLP",
      payment_terms: null,
      notes_commercial: null,
      total_price_net: null,
      total_price_tax: null,
      total_price_gross: null,
      extras: [],
      positions: [],
      payment: null,
      payment_url: null,
      valid_until: null,
      validity_expired: false,
      superseded: true,
      expires_at: "2999-01-01T00:00:00Z",
      approval_status: status,
      decided_by: null,
      decided_at: null,
      decided_note: null,
      quote_pdf_url: null,
    };
    vi.mocked(portalQuoteRetrieve).mockResolvedValue({
      status: 200,
      data: quote,
      headers: new Headers(),
    });
    render(
      <MemoryRouter initialEntries={["/cotizacion/test"]}>
        <Routes>
          <Route path="/cotizacion/:token" element={<PortalQuotePage />} />
        </Routes>
      </MemoryRouter>,
    );
    await screen.findByText("Esta cotización fue reemplazada por una revisión nueva.");
    if (status === "APPROVED") expect(screen.getByText("Propuesta aprobada")).toBeVisible();
    if (status === "DECLINED") expect(screen.getByText("Propuesta rechazada")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Aprobar propuesta" })).not.toBeInTheDocument();
  },
);

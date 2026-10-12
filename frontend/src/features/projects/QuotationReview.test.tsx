import { webcrypto, createHash } from "node:crypto";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import type { QuotationPreview } from "../../api/generated/models";
import { focusQuotationField, QuotationReview } from "./QuotationReview";

const bytes = new TextEncoder().encode("%PDF-1.7\nreviewed quotation\n%%EOF");
const preview: QuotationPreview = {
  id: "review",
  revision_code: "REV-B",
  snapshot_sha256: "b".repeat(64),
  bom_hash: "c".repeat(64),
  file_sha256: createHash("sha256").update(bytes).digest("hex"),
  byte_size: bytes.byteLength,
  document_date: "2026-10-09T15:00:00Z",
  expires_at: "2999-01-01T00:00:00Z",
  recipient: "cliente@example.invalid",
  client_name: "Cliente",
  currency: "CLP",
  total_price_gross: "1435471",
  production_allowed: false,
  documentary_complete: false,
  valid_until: "2999-01-01",
  pdf_url: "https://example.invalid/private.pdf",
};
const ready = vi.fn(),
  confirmed = vi.fn(),
  issue = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("crypto", webcrypto);
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, arrayBuffer: async () => bytes.buffer }),
  );
  URL.createObjectURL = vi.fn().mockReturnValue("blob:reviewed");
  URL.revokeObjectURL = vi.fn();
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function mount(value: QuotationPreview | null = preview, accepted = true) {
  return render(
    <QuotationReview
      preview={value}
      previousRevision="REV-A"
      code="P-000123"
      busy={false}
      confirmed={accepted}
      onConfirmed={confirmed}
      onReady={ready}
      onIssue={issue}
    />,
  );
}

test("issue requires the exact verified PDF to load, then names its recipient and consequence", async () => {
  mount();
  const button = screen.getByRole("button", { name: "Emitir y enviar al cliente" });
  expect(button).toBeDisabled();
  const frame = await screen.findByTitle("Vista previa del PDF real");
  expect(frame).toHaveAttribute("src", "blob:reviewed#view=FitH");
  expect(button).toBeDisabled();
  fireEvent.load(frame);
  await waitFor(() => expect(button).toBeEnabled());
  fireEvent.click(button);
  expect(issue).toHaveBeenCalledOnce();
  expect(ready).toHaveBeenLastCalledWith(true);
  expect(screen.getByText(/quedará reemplazada y conservará su documento/)).toHaveTextContent(
    "cliente@example.invalid",
  );
  expect(screen.getByRole("link", { name: "Descargar PDF revisado" })).toHaveAttribute(
    "href",
    "blob:reviewed",
  );
});

test.each(["hash", "size", "format"])(
  "a mismatching PDF %s cannot be reviewed or issued",
  async (failure) => {
    if (failure === "format")
      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        arrayBuffer: async () => new TextEncoder().encode("html-error").buffer,
      } as Response);
    mount({
      ...preview,
      ...(failure === "hash"
        ? { file_sha256: "d".repeat(64) }
        : failure === "size"
          ? { byte_size: 1 }
          : {}),
    });
    await screen.findByRole("alert");
    expect(screen.queryByTitle("Vista previa del PDF real")).not.toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Emitir y enviar al cliente" })).toBeDisabled();
    expect(issue).not.toHaveBeenCalled();
  },
);

test("expired review requires a new preview even with prior confirmation", async () => {
  mount({ ...preview, expires_at: "2020-01-01T00:00:00Z" });
  await screen.findByText(/La revisión del PDF venció/);
  const frame = await screen.findByTitle("Vista previa del PDF real");
  fireEvent.load(frame);
  expect(screen.getByRole("button", { name: "Emitir y enviar al cliente" })).toBeDisabled();
});

test("a checklist target opens every disclosure and focuses the missing field", () => {
  const view = render(
    <details>
      <summary>Posición</summary>
      <details>
        <summary>Preparación</summary>
        <input id="missing-handle" />
      </details>
    </details>,
  );
  focusQuotationField("missing-handle");
  expect(screen.getByRole("textbox")).toHaveFocus();
  expect(screen.getByRole("textbox")).toHaveClass("quotation-field-target");
  expect([...view.container.querySelectorAll("details")].every((item) => item.open)).toBe(true);
  fireEvent.blur(screen.getByRole("textbox"));
  expect(screen.getByRole("textbox")).not.toHaveClass("quotation-field-target");
});

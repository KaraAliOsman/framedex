import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { mailList, paymentMailPreview, paymentMailSend } from "../../api/generated/dekopen";
import { PaymentMailComposer, MailHistory } from "./MailPanels";

vi.mock("../../api/generated/dekopen", () => ({
  mailList: vi.fn(),
  mailRecover: vi.fn(),
  mailIntegrationStatus: vi.fn(),
  paymentMailPreview: vi.fn(),
  paymentMailSend: vi.fn(),
}));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: { role: "ESTIMATOR" } } }),
}));
vi.mock("../../ui", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../ui")>()),
  useConfirm: () => vi.fn(),
}));

const projectId = "00112233-4455-6677-8899-aabbccddee00";
const sourceId = "00112233-4455-6677-8899-aabbccddeeff";
const ready = {
  status: 200 as const,
  headers: new Headers(),
  data: {
    source_id: sourceId,
    recipient: "cliente@example.invalid",
    reference: "P-000123 · Pago registrado",
    html: "<p>Su comprobante</p>",
    provider: "sandbox",
    document_url: "https://storage.example.invalid/sealed.pdf",
    document_sha256: "a".repeat(64),
    document_name: "comprobante.pdf",
  },
};
const sent = {
  status: 200 as const,
  headers: new Headers(),
  data: {
    id: sourceId,
    kind: "PAYMENT",
    recipient: "cliente@example.invalid",
    subject: "Su cotización",
    project_id: projectId,
    created_at: "2026-10-08T12:00:00Z",
    state: "QUEUED",
    attempt: 0,
    delivered_at: null,
    error_code: null,
  },
};
function mount(
  child = <PaymentMailComposer orgId="org" projectId={projectId} paymentId={sourceId} />,
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{child}</MemoryRouter>
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.clear();
  vi.mocked(paymentMailPreview).mockResolvedValue(ready);
  vi.mocked(paymentMailSend).mockResolvedValue(sent);
});
afterEach(cleanup);

test("missing payment PDF blocks confirmation and never fabricates a receipt", async () => {
  vi.mocked(paymentMailPreview).mockResolvedValueOnce({
    ...ready,
    data: { ...ready.data, document_url: null, document_sha256: null },
  });
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar comprobante por correo" }));
  await screen.findByText(/Falta el PDF de este comprobante/);
  expect(screen.getByRole("checkbox")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Enviar al cliente" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Cerrar vista previa" }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar comprobante por correo" }));
  expect(await screen.findByRole("link", { name: /Abrir PDF sellado/ })).toHaveAttribute(
    "href",
    ready.data.document_url,
  );
  await waitFor(() => expect(screen.getByRole("checkbox")).toBeEnabled());
  expect(paymentMailSend).not.toHaveBeenCalled();
});

test("lost response reuses the intent and reviewed PDF; another confirmed send uses a new intent", async () => {
  vi.mocked(paymentMailSend).mockRejectedValueOnce(new Error("offline"));
  const view = mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar comprobante por correo" }));
  await screen.findByRole("link", { name: /Abrir PDF sellado/ });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByRole("alert");
  view.unmount();
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar comprobante por correo" }));
  await screen.findByRole("link", { name: /Abrir PDF sellado/ });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByText(/Envío registrado/);
  const first = vi.mocked(paymentMailSend).mock.calls[0]![2];
  expect(vi.mocked(paymentMailSend).mock.calls[1]![2]).toEqual(first);
  expect(first.expected_document_sha256).toBe(ready.data.document_sha256);
  fireEvent.click(screen.getByRole("button", { name: "Cerrar vista previa" }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar comprobante por correo" }));
  await waitFor(() => expect(screen.getByRole("checkbox")).toBeEnabled());
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByText(/Envío registrado/);
  expect(vi.mocked(paymentMailSend).mock.calls[2]![2].operation_key).not.toBe(first.operation_key);
});

test("revoked-link mail preserves history and directs access control to the quotation", async () => {
  vi.mocked(mailList).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: [
      {
        ...sent.data,
        kind: "QUOTE",
        state: "FAILED",
        error_code: "mail_quote_link_inactive",
        attempt: 1,
      },
    ],
  });
  mount(<MailHistory orgId="org" />);
  const action = await screen.findByRole("link", { name: "Revisar enlace de cotización" });
  expect(action).toHaveAttribute("href", `/projects/${projectId}?section=quote`);
  expect(screen.queryByRole("button", { name: "Comprobar y reenviar" })).not.toBeInTheDocument();
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { mailList, quoteMailPreview, quoteMailSend } from "../../api/generated/dekopen";
import { runJob } from "../jobs/runJob";
import { MailComposer, MailHistory } from "./MailPanels";

vi.mock("../../api/generated/dekopen", () => ({
  mailList: vi.fn(),
  mailRecover: vi.fn(),
  mailIntegrationStatus: vi.fn(),
  quoteMailPreview: vi.fn(),
  quoteMailSend: vi.fn(),
  paymentMailPreview: vi.fn(),
  paymentMailSend: vi.fn(),
}));
vi.mock("../jobs/runJob", () => ({ runJob: vi.fn() }));
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
    reference: "P-000123 · REV-A",
    html: "<p>Su cotización</p>",
    provider: "sandbox",
    document_url: "https://storage.example.invalid/sealed.pdf",
    document_sha256: "a".repeat(64),
    document_name: "cotizacion.pdf",
  },
};
const sent = {
  status: 200 as const,
  headers: new Headers(),
  data: {
    id: sourceId,
    kind: "QUOTE",
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
function mount(child = <MailComposer orgId="org" projectId={projectId} />) {
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
  vi.mocked(quoteMailPreview).mockResolvedValue(ready);
  vi.mocked(quoteMailSend).mockResolvedValue(sent);
});
afterEach(cleanup);

test("missing PDF blocks confirmation until the exact emission is prepared", async () => {
  vi.mocked(quoteMailPreview).mockResolvedValueOnce({
    ...ready,
    data: { ...ready.data, document_url: null, document_sha256: null },
  });
  vi.mocked(runJob).mockResolvedValue({ state: "SUCCEEDED" } as Awaited<ReturnType<typeof runJob>>);
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar cotización por correo" }));
  await screen.findByRole("button", { name: "Preparar PDF de la cotización" });
  expect(screen.getByRole("checkbox")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Enviar al cliente" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Preparar PDF de la cotización" }));
  expect(await screen.findByRole("link", { name: /Abrir PDF sellado/ })).toHaveAttribute(
    "href",
    ready.data.document_url,
  );
  expect(vi.mocked(runJob).mock.calls[0]![0].payload).toMatchObject({
    project_version_id: sourceId,
    document_type: "DOC-01",
    format: "PDF",
  });
  await waitFor(() => expect(screen.getByRole("checkbox")).toBeEnabled());
  expect(quoteMailSend).not.toHaveBeenCalled();
});

test("lost response reuses the intent and reviewed PDF; another confirmed send uses a new intent", async () => {
  vi.mocked(quoteMailSend).mockRejectedValueOnce(new Error("offline"));
  const view = mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar cotización por correo" }));
  await screen.findByRole("link", { name: /Abrir PDF sellado/ });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByRole("alert");
  view.unmount();
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Enviar cotización por correo" }));
  await screen.findByRole("link", { name: /Abrir PDF sellado/ });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByText(/Envío registrado/);
  const first = vi.mocked(quoteMailSend).mock.calls[0]![1];
  expect(vi.mocked(quoteMailSend).mock.calls[1]![1]).toEqual(first);
  expect(first.expected_document_sha256).toBe(ready.data.document_sha256);
  fireEvent.click(screen.getByRole("button", { name: "Cerrar vista previa" }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar cotización por correo" }));
  await waitFor(() => expect(screen.getByRole("checkbox")).toBeEnabled());
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Enviar al cliente" }));
  await screen.findByText(/Envío registrado/);
  expect(vi.mocked(quoteMailSend).mock.calls[2]![1].operation_key).not.toBe(first.operation_key);
});

test("revoked-link mail preserves history and directs a new confirmation to the quotation", async () => {
  vi.mocked(mailList).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: [{ ...sent.data, state: "FAILED", error_code: "mail_quote_link_inactive", attempt: 1 }],
  });
  mount(<MailHistory orgId="org" />);
  const action = await screen.findByRole("link", { name: "Preparar nuevo correo" });
  expect(action).toHaveAttribute("href", `/projects/${projectId}?correo=cotizacion`);
  expect(screen.queryByRole("button", { name: "Comprobar y reenviar" })).not.toBeInTheDocument();
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  aiConnectionTest,
  aiModeGet,
  aiSettingsGet,
  aiSettingsSave,
  aiUsageList,
} from "../../api/generated/dekopen";
import { AiSettingsSection } from "./AiSettingsSection";
import { AiWorkList } from "./AiWorkList";
import { AiModeBadge } from "./AiModeBadge";

vi.mock("../../api/generated/dekopen", () => ({
  aiConnectionTest: vi.fn(),
  aiModeGet: vi.fn(),
  aiSettingsGet: vi.fn(),
  aiSettingsSave: vi.fn(),
  aiUsageList: vi.fn(),
}));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    me: {
      active_organization: { id: "org-fixture", role: "OWNER" },
      user: { id: "actor-fixture" },
    },
  }),
}));

function settings() {
  return {
    revision: 1,
    mock_available: false,
    routes: ["design_assist", "agent", "context_assist", "catalog_import"].map((capability) => ({
      capability,
      provider: "MIMO",
      provider_model: "chosen-model",
      timeout_s: 60,
      retries: 2,
      tools_mode: "AUTO",
      input_usd_per_million: null,
      output_usd_per_million: null,
      state: "UNTESTED",
      credential_configured: true,
      credits_cost: 5,
      test_mode: false,
      last_cause: null,
      checked_at: null,
    })),
    usage: {
      calls: 0,
      tokens_prompt: 0,
      tokens_completion: 0,
      estimated_cost_usd: null,
      capacity_credits: 0,
      credits_debited: 0,
      monthly_budget_credits: null,
      budget_blocked: false,
      budget_notice_at: null,
      month_start: "2026-10-01T00:00:00-03:00",
      users: [],
    },
  };
}

function mount(component: JSX.Element) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{component}</MemoryRouter>
    </QueryClientProvider>,
  );
  return client;
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(aiSettingsGet).mockResolvedValue({
    status: 200,
    data: settings(),
    headers: new Headers(),
  } as never);
});

describe("OWNER IA settings", () => {
  it("saves the monthly limit without sending credential fields and invalidates test mode", async () => {
    vi.mocked(aiSettingsSave).mockResolvedValue({
      status: 200,
      data: { ...settings(), revision: 2 },
      headers: new Headers(),
    } as never);
    const client = mount(<AiSettingsSection orgId="org-fixture" />);
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const budget = await screen.findByLabelText("Presupuesto mensual (créditos de solicitudes)");
    fireEvent.change(budget, { target: { value: "25" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar ajustes de IA" }));
    await screen.findByText(/Ajustes de IA guardados/);
    const request = vi.mocked(aiSettingsSave).mock.calls[0]![0];
    expect(request.monthly_budget_credits).toBe(25);
    expect(request.routes).toHaveLength(4);
    expect(JSON.stringify(request)).not.toMatch(/api_key|base_url|credential/);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["ai", "mode", "org-fixture"] });
  });

  it("blocks a partial tariff locally and gives an actionable error", async () => {
    mount(<AiSettingsSection orgId="org-fixture" />);
    const rates = await screen.findAllByLabelText("Tarifa de entrada (USD / millón de tokens)");
    fireEvent.change(rates[0]!, { target: { value: "1,25" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar ajustes de IA" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Declara ambas tarifas");
    expect(aiSettingsSave).not.toHaveBeenCalled();
  });

  it("probes the real E03 oracle only from saved settings", async () => {
    vi.mocked(aiConnectionTest).mockResolvedValue({
      status: 200,
      data: {
        passed: true,
        case_id: "E03",
        credits_debited: 5,
        tokens_prompt: 91,
        tokens_completion: 132,
        latency_ms: 20,
        test_mode: false,
      },
      headers: new Headers(),
    } as never);
    mount(<AiSettingsSection orgId="org-fixture" />);
    fireEvent.click(await screen.findByRole("button", { name: "Probar conexión" }));
    await screen.findByText(/Conexión verificada: la propuesta superó el caso mínimo/);
    expect(vi.mocked(aiConnectionTest).mock.calls[0]![0].operation_key).toMatch(/^connection:/);
  });

  it("presents missing credentials as a server activation action", async () => {
    const data = settings();
    data.routes[0]!.state = "MISSING_CREDENTIAL";
    data.routes[0]!.credential_configured = false;
    vi.mocked(aiSettingsGet).mockResolvedValue({
      status: 200,
      data,
      headers: new Headers(),
    } as never);
    mount(<AiSettingsSection orgId="org-fixture" />);
    expect(await screen.findByText("Sin credencial")).toBeVisible();
    expect(screen.getByText(/El dueño debe configurar la credencial/)).toBeVisible();
    expect(screen.queryByLabelText(/clave|api.?key/i)).toBeNull();
  });
});

it("loads all work pages while preserving capability and state filters", async () => {
  const work = {
    id: "work",
    job_id: null,
    ai_job_id: null,
    capability: "agent",
    user_id: "actor-fixture",
    user_label: "Persona de prueba",
    calls: 1,
    status: "SUCCEEDED",
    job_state: null,
    test_mode: false,
    tokens_prompt: 91,
    tokens_completion: 132,
    estimated_cost_usd: null,
    capacity_credits: 5,
    latency_ms: 20,
    retries: 0,
    fallback: false,
    tools: [],
    trace: [],
    last_cause: null,
    created_at: "2026-10-07T12:00:00Z",
  };
  vi.mocked(aiUsageList)
    .mockResolvedValueOnce({
      status: 200,
      data: Array.from({ length: 100 }, (_, i) => ({ ...work, id: String(i) })),
      headers: new Headers(),
    } as never)
    .mockResolvedValueOnce({
      status: 200,
      data: [{ ...work, id: "last", user_label: "Última persona" }],
      headers: new Headers(),
    } as never);
  mount(<AiWorkList capability="agent" state="SUCCEEDED" />);
  fireEvent.click(await screen.findByRole("button", { name: "Cargar más llamadas" }));
  await screen.findByText("Última persona");
  expect(vi.mocked(aiUsageList).mock.calls[1]![0]).toEqual({
    capability: "agent",
    state: "SUCCEEDED",
    limit: 100,
    offset: 100,
  });
  await waitFor(() =>
    expect(screen.queryByRole("button", { name: "Cargar más llamadas" })).toBeNull(),
  );
});

it("marks an explicitly enabled test provider", async () => {
  vi.mocked(aiModeGet).mockResolvedValue({
    status: 200,
    data: { test_mode: true },
    headers: new Headers(),
  } as never);
  mount(<AiModeBadge />);
  expect(await screen.findByText("Modo de prueba")).toBeVisible();
});

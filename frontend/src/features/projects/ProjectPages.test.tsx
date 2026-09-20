// frontend/src/features/projects/ProjectPages.test.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { ApiError, apiMutator } from "../../api/apiMutator";
import {
  positionsDestroy,
  projectsClone,
  projectsCreate,
  projectsList,
  projectsRetrieve,
  projectsUpdate,
} from "../../api/generated/dekopen";
import type {
  PositionResponse,
  ProjectResponse,
  ProjectWriteRequest,
} from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { ProjectPages } from "./ProjectPages";

vi.mock("../../api/apiMutator", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/apiMutator")>();
  return { ...actual, apiMutator: vi.fn() };
});

vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    status: "ready",
    session: { user: { id: "user-a" } },
    me: {
      active_organization: {
        id: "org-a",
        name: "Taller A",
        role: "OWNER",
      },
    },
  }),
}));

vi.mock("../../api/generated/dekopen", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/generated/dekopen")>();
  return {
    ...actual,
    projectsList: vi.fn(),
    projectsCreate: vi.fn(),
    projectsRetrieve: vi.fn(),
    projectsUpdate: vi.fn(),
    projectsClone: vi.fn(),
    positionsDestroy: vi.fn(),
  };
});

function response<S extends number, T>(status: S, data: T) {
  return { status, data, headers: new Headers() };
}

function makePosition(): PositionResponse {
  return {
    id: "position-a",
    project_id: "project-a",
    position_index: 1,
    location_tag: "Dormitorio principal",
    quantity: 2,
    typology: "FIXED",
    updated_at: "2026-09-18T12:01:02.123456Z",
    design: {
      system_id: "system-a",
      nominal_width_mm: "1234.50",
      nominal_height_mm: "987.60",
      color: "WHITE",
      parametric_tree: {
        id: "bay-a",
        type: "BAY",
        opening_type: "FIXED",
      },
    },
    bom: {
      profile_cuts: [],
      reinforcements: [],
      glasses: [],
      panels: [],
      hardware_items: [],
      leaf_weights: [],
      calculation_hash: `sha256:${"a".repeat(64)}`,
    },
  };
}

function makeProject(overrides: Partial<ProjectResponse> = {}): ProjectResponse {
  return {
    id: "project-a",
    code: "P-001",
    name: "Casa original",
    client_name: "Cliente original",
    client_rut: "",
    client_email: "",
    client_phone: "",
    delivery_address: "",
    notes_commercial: "",
    notes_internal: "",
    status: "DRAFT",
    current_revision: "REV-A",
    updated_at: "2026-09-18T12:00:00.654321Z",
    total_price_net: "0.00",
    total_price_tax: "0.00",
    total_price_gross: "0.00",
    pricing_current: false,
    current_pricing_operation_id: null,
    position_count: 0,
    positions: [],
    versions: [],
    ...overrides,
  };
}

function expectedMetadata(project: ProjectResponse): ProjectWriteRequest {
  return {
    name: project.name,
    client_name: project.client_name,
    client_rut: project.client_rut ?? "",
    client_email: project.client_email ?? "",
    client_phone: project.client_phone ?? "",
    delivery_address: project.delivery_address ?? "",
    notes_commercial: project.notes_commercial ?? "",
    notes_internal: project.notes_internal ?? "",
  };
}

const mounted: {
  router: ReturnType<typeof createMemoryRouter>;
  client: QueryClient;
}[] = [];

function mount(path = "/projects/project-a") {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  const router = createMemoryRouter(
    [
      { path: "/projects", element: <ProjectPages /> },
      { path: "/projects/:id", element: <ProjectPages /> },
    ],
    { initialEntries: [path] },
  );

  mounted.push({ router, client });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

function change(label: Parameters<typeof t>[0], value: string): void {
  fireEvent.change(screen.getByLabelText(t(label)), {
    target: { value },
  });
}

async function editMetadata(): Promise<void> {
  fireEvent.click(await screen.findByRole("button", { name: t("projects.edit") }));
}

function submit(): void {
  fireEvent.click(screen.getByRole("button", { name: t("projects.save") }));
}

function expectTenant(options: RequestInit | undefined): void {
  expect(new Headers(options?.headers).get("X-Organization-ID")).toBe("org-a");
  expect(options?.signal).toBeInstanceOf(AbortSignal);
}

beforeEach(() => {
  vi.resetAllMocks();
  // Browser dialog only; router, guard, query client and BOM remain real.
  vi.spyOn(window, "confirm").mockReturnValue(true);
  vi.mocked(projectsList).mockResolvedValue(response(200, { items: [] }));
  vi.mocked(projectsRetrieve).mockResolvedValue(response(200, makeProject()));
});

afterEach(() => {
  cleanup();
  for (const { router, client } of mounted.splice(0)) {
    router.dispose();
    client.clear();
  }
  vi.restoreAllMocks();
});

it("creates a project, navigates to the server ID and renders persisted metadata", async () => {
  const created = makeProject({
    id: "server-created-id",
    code: "P-1042",
    name: "Nombre confirmado por servidor",
    client_name: "Cliente persistido",
    client_email: "persistido@example.test",
    notes_internal: "Nota recuperada desde detalle",
  });
  vi.mocked(projectsCreate).mockResolvedValue(response(201, created));
  vi.mocked(projectsRetrieve).mockResolvedValue(response(200, created));

  const router = mount("/projects");
  fireEvent.click(await screen.findByRole("button", { name: t("projects.create") }));
  change("projects.name", "Nombre ingresado");
  change("projects.client", "Cliente ingresado");
  change("projects.email", "ingresado@example.test");
  change("projects.internalNotes", "Nota ingresada");
  submit();

  await screen.findByRole("heading", {
    level: 1,
    name: "P-1042 · Nombre confirmado por servidor",
  });
  expect(router.state.location.pathname).toBe("/projects/server-created-id");
  expect(screen.getByText("Cliente persistido")).toBeInTheDocument();
  expect(screen.getByText("persistido@example.test")).toBeInTheDocument();
  expect(screen.getByText("Nota recuperada desde detalle")).toBeInTheDocument();
  expect(screen.queryByDisplayValue("Nombre ingresado")).not.toBeInTheDocument();

  expect(projectsCreate).toHaveBeenCalledTimes(1);
  const [body, options] = vi.mocked(projectsCreate).mock.calls[0]!;
  expect(body).toEqual({
    name: "Nombre ingresado",
    client_name: "Cliente ingresado",
    client_rut: "",
    client_email: "ingresado@example.test",
    client_phone: "",
    delivery_address: "",
    notes_commercial: "",
    notes_internal: "Nota ingresada",
  });
  expectTenant(options);
  expect(projectsRetrieve).toHaveBeenCalledWith(
    created.id,
    expect.objectContaining({
      headers: { "X-Organization-ID": "org-a" },
    }),
  );
  // Successful creation must clear the real unsaved-change blocker.
  expect(window.confirm).not.toHaveBeenCalled();
});

it("PATCHes the exact original timestamp and reloads persisted metadata", async () => {
  const original = makeProject();
  const saved = makeProject({
    name: "Casa actualizada",
    client_phone: "+56 9 1234 5678",
    updated_at: "2026-09-18T13:00:00.111222Z",
  });
  vi.mocked(projectsRetrieve)
    .mockResolvedValueOnce(response(200, original))
    .mockResolvedValue(response(200, saved));
  vi.mocked(projectsUpdate).mockResolvedValue(response(200, saved));

  mount();
  await editMetadata();
  change("projects.name", saved.name);
  change("projects.phone", saved.client_phone!);
  submit();

  await screen.findByRole("heading", {
    level: 1,
    name: "P-001 · Casa actualizada",
  });
  expect(screen.getByText(saved.client_phone!)).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(t("projects.saved"));
  expect(screen.queryByLabelText(t("projects.name"))).not.toBeInTheDocument();

  expect(projectsUpdate).toHaveBeenCalledTimes(1);
  const [id, body, options] = vi.mocked(projectsUpdate).mock.calls[0]!;
  expect(id).toBe(original.id);
  expect(body).toEqual({
    ...expectedMetadata(saved),
    expected_updated_at: original.updated_at,
  });
  expectTenant(options);
  expect(projectsRetrieve).toHaveBeenCalledTimes(2);
});

it.each([
  [400, "projects.invalid", false],
  [409, "projects.conflict", true],
] as const)("retains entered metadata after API status %s", async (status, message, disabled) => {
  vi.mocked(projectsUpdate).mockRejectedValue(
    new ApiError(status, { error: { code: "private_backend_detail" } }),
  );

  mount();
  await editMetadata();
  change("projects.name", "Trabajo todavía sin guardar");
  change("projects.internalNotes", "Conservar esta nota");
  submit();

  expect(await screen.findByRole("alert")).toHaveTextContent(t(message));
  expect(screen.getByLabelText(t("projects.name"))).toHaveValue("Trabajo todavía sin guardar");
  expect(screen.getByLabelText(t("projects.internalNotes"))).toHaveValue("Conservar esta nota");
  expect(screen.queryByText("private_backend_detail")).not.toBeInTheDocument();

  const save = screen.getByRole("button", { name: t("projects.save") });
  if (disabled) {
    expect(save).toBeDisabled();
    expect(screen.getByRole("button", { name: t("projects.reload") })).toBeEnabled();
  } else {
    expect(save).toBeEnabled();
  }
  expect(projectsRetrieve).toHaveBeenCalledTimes(1);
});

it("clones a draft to the returned ID without mutating the source", async () => {
  const source = makeProject();
  const originalSnapshot = structuredClone(source);
  const copy = makeProject({
    id: "copy-server-id",
    code: "P-002",
    name: "Copia de Casa original",
    updated_at: "2026-09-18T14:00:00.000001Z",
  });

  vi.mocked(projectsRetrieve).mockImplementation(async (id) => {
    if (id === source.id) return response(200, source);
    if (id === copy.id) return response(200, copy);
    throw new Error(`Unexpected project ID: ${id}`);
  });
  vi.mocked(projectsClone).mockResolvedValue(response(201, copy));

  const router = mount();
  fireEvent.click(await screen.findByRole("button", { name: t("projects.cloneDraft") }));
  await screen.findByRole("heading", {
    level: 1,
    name: "P-002 · Copia de Casa original",
  });

  expect(router.state.location.pathname).toBe("/projects/copy-server-id");
  expect(projectsClone).toHaveBeenCalledTimes(1);
  const [id, body, options] = vi.mocked(projectsClone).mock.calls[0]!;
  expect(id).toBe(source.id);
  expect(body).toEqual({ expected_updated_at: source.updated_at });
  expectTenant(options);
  expect(source).toEqual(originalSnapshot);
  expect(projectsUpdate).not.toHaveBeenCalled();
  expect(projectsCreate).not.toHaveBeenCalled();
  expect(positionsDestroy).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: t("projects.edit") }));
  change("projects.name", "Cambio local de la copia");
  expect(source).toEqual(originalSnapshot);
});

it("deletes using the exact position timestamp and renders the refreshed project", async () => {
  const position = makePosition();
  const original = makeProject({
    position_count: 1,
    positions: [position],
  });
  const emptied = makeProject({
    updated_at: "2026-09-18T15:00:00.000001Z",
  });

  vi.mocked(projectsRetrieve)
    .mockResolvedValueOnce(response(200, original))
    .mockResolvedValue(response(200, emptied));
  vi.mocked(positionsDestroy).mockResolvedValue(response(204, undefined));

  mount();
  await screen.findByText("1. Dormitorio principal");
  fireEvent.click(screen.getByRole("button", { name: t("projects.deletePosition") }));

  expect(await screen.findByText(t("projects.noPositions"))).toBeInTheDocument();
  expect(screen.queryByText("1. Dormitorio principal")).not.toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(t("projects.deleted"));
  expect(window.confirm).toHaveBeenCalledWith(t("projects.deleteConfirm"));

  expect(positionsDestroy).toHaveBeenCalledTimes(1);
  const [id, params, options] = vi.mocked(positionsDestroy).mock.calls[0]!;
  expect(id).toBe(position.id);
  expect(params).toEqual({ expected_updated_at: position.updated_at });
  expectTenant(options);
  expect(projectsRetrieve).toHaveBeenCalledTimes(2);
});

it.each([
  [409, "projects.conflict"],
  [503, "projects.saveError"],
] as const)(
  "keeps the position row when deletion fails with status %s",
  async (status, message) => {
    const position = makePosition();
    vi.mocked(projectsRetrieve).mockResolvedValue(
      response(
        200,
        makeProject({
          position_count: 1,
          positions: [position],
        }),
      ),
    );
    vi.mocked(positionsDestroy).mockRejectedValue(
      new ApiError(status, { error: { code: "delete_rejected" } }),
    );

    mount();
    await screen.findByText("1. Dormitorio principal");
    fireEvent.click(screen.getByRole("button", { name: t("projects.deletePosition") }));

    expect(await screen.findByRole("alert")).toHaveTextContent(t(message));
    expect(screen.getByText("1. Dormitorio principal")).toBeInTheDocument();
    expect(screen.queryByText(t("projects.noPositions"))).not.toBeInTheDocument();
    expect(screen.queryByText(t("projects.deleted"))).not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: t("projects.deletePosition") })).toBeEnabled();
    });

    expect(positionsDestroy).toHaveBeenCalledWith(
      position.id,
      { expected_updated_at: position.updated_at },
      expect.objectContaining({
        headers: { "X-Organization-ID": "org-a" },
      }),
    );
    expect(projectsRetrieve).toHaveBeenCalledTimes(1);
  },
);

it("prepares and explicitly emits the current priced revision", async () => {
  const position = makePosition();
  const priced = makeProject({
    pricing_current: true,
    current_pricing_operation_id: "operation-a",
    total_price_gross: "1190.00",
    position_count: 1,
    positions: [position],
  });
  const quoted = makeProject({
    ...priced,
    status: "QUOTED",
    versions: [
      {
        id: "version-a",
        revision_code: "REV-A",
        authority_version: "SHOT10_V1",
        bom_hash: "a".repeat(64),
        snapshot_sha256: "b".repeat(64),
        production_allowed: true,
        documentary_complete: false,
        emitted_at: "2026-09-19T12:00:00Z",
      },
    ],
  });
  vi.mocked(projectsRetrieve)
    .mockResolvedValueOnce(response(200, priced))
    .mockResolvedValue(response(200, quoted));
  vi.mocked(apiMutator).mockImplementation(async (url, options) => {
    if (url.endsWith("/inputs/") && options.method === "GET")
      return response(200, {
        project_id: priced.id,
        revision_code: "REV-A",
        payment_terms: "",
        quotation_valid_until: null,
        positions: [
          {
            position_id: position.id,
            calculation_hash: "sha256:" + "a".repeat(64),
            location_tag: position.location_tag,
            system_name: "Demo 60",
            manufacturing_placement_policy_id: "placement-a",
            handle_requirement_policy_id: "handle-a",
            reinforcement_cut_policy_id: "reinforcement-a",
            placement_options: [{ id: "placement-a", label: "Fabricación v1", version: 1 }],
            handle_options: [{ id: "handle-a", label: "Manillas v1", version: 1 }],
            reinforcement_options: [{ id: "reinforcement-a", label: "Refuerzos v1", version: 1 }],
            workshop_annotations: [],
            structural_inputs: [],
            glass_polishing: [],
            handle_intents: [],
            accessory_schedule: { schema_version: 1, coverage: "NONE_REQUIRED", items: [] },
            legacy_handle_migration_confirmed: false,
          },
        ],
      }) as never;
    if (url.endsWith("/inputs/") && options.method === "PUT")
      return response(200, { project_id: priced.id, positions_saved: 1 }) as never;
    if (url.endsWith("/freeze/") && options.method === "POST")
      return response(201, { revision_code: "REV-A" }) as never;
    throw new Error(`Unexpected lifecycle request ${options.method} ${url}`);
  });

  mount();
  fireEvent.click(await screen.findByRole("button", { name: t("quotation.prepare") }));
  await screen.findByLabelText(t("quotation.paymentTerms"));
  change("quotation.paymentTerms", "50% anticipo");
  change("quotation.validUntil", "2026-10-19");
  fireEvent.click(screen.getByLabelText(t("quotation.confirm")));
  fireEvent.click(screen.getByRole("button", { name: t("quotation.emit") }));

  await screen.findByText(t("projects.quoted"));
  expect(screen.getAllByText("REV-A")).toHaveLength(2);
  expect(apiMutator).toHaveBeenCalledTimes(3);
  const saveRequest = vi.mocked(apiMutator).mock.calls[1]!;
  expect(JSON.parse(String((saveRequest[1] as RequestInit).body))).toMatchObject({
    payment_terms: "50% anticipo",
    quotation_valid_until: "2026-10-19",
    positions: [{ location_tag: "Dormitorio principal" }],
  });
});

it("guards unsaved quotation preparation edits against navigation and cancel", async () => {
  const position = makePosition();
  const priced = makeProject({
    pricing_current: true,
    current_pricing_operation_id: "operation-a",
    total_price_gross: "1190.00",
    position_count: 1,
    positions: [position],
  });
  vi.mocked(projectsRetrieve).mockResolvedValue(response(200, priced));
  vi.mocked(apiMutator).mockImplementation(async (url, options) => {
    if (url.endsWith("/inputs/") && options.method === "GET")
      return response(200, {
        project_id: priced.id,
        revision_code: "REV-A",
        payment_terms: "",
        quotation_valid_until: null,
        positions: [
          {
            position_id: position.id,
            calculation_hash: "sha256:" + "a".repeat(64),
            location_tag: position.location_tag,
            system_name: "Demo 60",
            manufacturing_placement_policy_id: "placement-a",
            handle_requirement_policy_id: "handle-a",
            reinforcement_cut_policy_id: "reinforcement-a",
            placement_options: [{ id: "placement-a", label: "Fabricación v1", version: 1 }],
            handle_options: [{ id: "handle-a", label: "Manillas v1", version: 1 }],
            reinforcement_options: [{ id: "reinforcement-a", label: "Refuerzos v1", version: 1 }],
            workshop_annotations: [],
            structural_inputs: [],
            glass_polishing: [],
            handle_intents: [],
            accessory_schedule: { schema_version: 1, coverage: "NONE_REQUIRED", items: [] },
            legacy_handle_migration_confirmed: false,
          },
        ],
      }) as never;
    throw new Error(`Unexpected lifecycle request ${options.method} ${url}`);
  });

  const router = mount();
  const confirm = vi.mocked(window.confirm);
  fireEvent.click(await screen.findByRole("button", { name: t("quotation.prepare") }));
  await screen.findByLabelText(t("quotation.paymentTerms"));
  change("quotation.paymentTerms", "50% anticipo");

  confirm.mockReturnValue(false);
  fireEvent.click(screen.getByRole("link", { name: t("projects.back") }));
  await waitFor(() => expect(confirm).toHaveBeenCalledWith(t("projects.leaveUnsaved")));
  expect(router.state.location.pathname).toBe("/projects/project-a");
  expect(screen.getByLabelText(t("quotation.paymentTerms"))).toHaveValue("50% anticipo");

  fireEvent.click(screen.getByRole("button", { name: t("projects.cancel") }));
  expect(confirm).toHaveBeenCalledWith(t("projects.discard"));
  expect(screen.getByLabelText(t("quotation.paymentTerms"))).toHaveValue("50% anticipo");

  confirm.mockReturnValue(true);
  fireEvent.click(screen.getByRole("button", { name: t("projects.cancel") }));
  await waitFor(() =>
    expect(screen.queryByLabelText(t("quotation.paymentTerms"))).not.toBeInTheDocument(),
  );

  fireEvent.click(screen.getByRole("button", { name: t("quotation.prepare") }));
  await screen.findByLabelText(t("quotation.paymentTerms"));
  change("quotation.validUntil", "2026-10-19");
  confirm.mockReturnValue(false);
  fireEvent.click(screen.getByRole("link", { name: t("projects.back") }));
  await waitFor(() => expect(confirm).toHaveBeenCalledWith(t("projects.leaveUnsaved")));
  expect(router.state.location.pathname).toBe("/projects/project-a");

  confirm.mockReturnValue(true);
  fireEvent.click(screen.getByRole("link", { name: t("projects.back") }));
  await waitFor(() => expect(router.state.location.pathname).toBe("/projects"));
});

it("opens one idempotent editable successor from a quoted revision", async () => {
  const quoted = makeProject({ status: "QUOTED", versions: [] });
  const successor = makeProject({ current_revision: "REV-B" });
  vi.mocked(projectsRetrieve)
    .mockResolvedValueOnce(response(200, quoted))
    .mockResolvedValue(response(200, successor));
  vi.mocked(apiMutator).mockResolvedValue(
    response(201, { ...successor, successor_created: true }) as never,
  );

  mount();
  fireEvent.click(await screen.findByRole("button", { name: t("quotation.editQuoted") }));

  await screen.findByText("REV-B");
  expect(apiMutator).toHaveBeenCalledTimes(1);
  expect(vi.mocked(apiMutator).mock.calls[0]?.[0]).toBe("/api/v1/projects/project-a/successor/");
  expect(window.confirm).toHaveBeenCalledWith(t("quotation.successorConfirm"));
});

it("explicitly retires current draft pricing with an audit reason before editing", async () => {
  const priced = makeProject({
    pricing_current: true,
    current_pricing_operation_id: "operation-a",
    position_count: 1,
    positions: [makePosition()],
  });
  vi.mocked(projectsRetrieve)
    .mockResolvedValueOnce(response(200, priced))
    .mockResolvedValue(
      response(200, makeProject({ position_count: 1, positions: [makePosition()] })),
    );
  vi.mocked(apiMutator).mockResolvedValue(response(200, {}) as never);
  vi.spyOn(window, "prompt").mockReturnValue("Corregir medidas");
  mount();
  fireEvent.click(await screen.findByRole("button", { name: t("quotation.resetPricing") }));
  await waitFor(() =>
    expect(apiMutator).toHaveBeenCalledWith(
      "/api/v1/projects/project-a/reset-pricing/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          expected_operation_id: "operation-a",
          reason: "Corregir medidas",
          confirmed: true,
        }),
      }),
    ),
  );
  expect(await screen.findByRole("link", { name: t("projects.addPosition") })).toBeInTheDocument();
});

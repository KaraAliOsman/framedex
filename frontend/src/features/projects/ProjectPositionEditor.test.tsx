// frontend/src/features/projects/ProjectPositionEditor.test.tsx
// Component tests only. Real router, query client, store and IntentEditor.
// Mocks are limited to authentication and generated API boundaries.
// Proposed code; not executed.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  engineLayout,
  engineCalculate,
  engineSystems,
  positionsCreate,
  positionsRetrieve,
  positionsUpdate,
  projectDesignOptions,
} from "../../api/generated/dekopen";
import type { EngineCalculateResponse, PositionResponse } from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { useCanvasStore } from "../canvas/canvasStore";
import { ProjectPositionEditor } from "./ProjectPositionEditor";
import { ApiError } from "../../api/apiMutator";

const identity = vi.hoisted(() => ({
  id: "org-a",
  role: "OWNER",
  listeners: new Set<() => void>(),
}));

vi.mock("../../auth/AuthSessionProvider", async () => {
  const { useSyncExternalStore } = await import("react");
  return {
    useAuthSession: () => {
      useSyncExternalStore(
        (listener) => {
          identity.listeners.add(listener);
          return () => identity.listeners.delete(listener);
        },
        () => identity.id + ":" + identity.role,
      );
      return { me: { active_organization: { id: identity.id, role: identity.role } } };
    },
  };
});

vi.mock("../../api/generated/dekopen", () => ({
  engineLayout: vi.fn().mockResolvedValue({ status: 200, data: { nodes: [] } }),
  engineCalculate: vi.fn(),
  engineSystems: vi.fn(),
  positionsCreate: vi.fn(),
  positionsRetrieve: vi.fn(),
  positionsUpdate: vi.fn(),
  projectDesignOptions: vi.fn(),
}));

const calculate = vi.mocked(engineCalculate);
const retrieve = vi.mocked(positionsRetrieve);
const update = vi.mocked(positionsUpdate);
const create = vi.mocked(positionsCreate);

function ok<T>(data: T) {
  return { status: 200 as const, headers: new Headers(), data };
}

function bom(sku: string): EngineCalculateResponse {
  return {
    profile_cuts: [
      {
        sku,
        role: "FRAME",
        material: "PVC",
        length_mm: "1234.25",
        angle_left: "45.0",
        angle_right: "45.0",
        qty: 2,
        bay_id: "bay-1",
        leaf_id: null,
      },
    ],
    reinforcements: [],
    glasses: [],
    panels: [],
    hardware_items: [],
    leaf_weights: [],
    calculation_hash: `sha256:${"a".repeat(64)}`,
  };
}

function position(
  id = "position-a",
  projectId = "project-a",
  location = "Cocina",
): PositionResponse {
  return {
    id,
    project_id: projectId,
    position_index: 3,
    location_tag: location,
    quantity: 4,
    typology: "FIXED",
    updated_at: "2026-09-18T15:00:00.123456Z",
    design: {
      system_id: "system-a",
      nominal_width_mm: "1234.25",
      nominal_height_mm: "987.50",
      color: "WHITE",
      parametric_tree: {
        id: "bay-1",
        type: "BAY",
        opening_type: "FIXED",
        glass_thickness_mm: "24.00",
        glass_spec: "4-16-4 transparente",
        glass_article_sku: "GLASS-A",
        hardware_set_sku: null,
      },
    },
    bom: bom("CUT-A"),
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

const clients: QueryClient[] = [];

function mount(path = "/projects/project-a/positions/position-a/edit") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
    },
  });
  clients.push(queryClient);
  const router = createMemoryRouter(
    [
      {
        path: "/projects/:id/positions/:posId/edit",
        element: <ProjectPositionEditor />,
      },
      {
        path: "/projects/:id/positions/new",
        element: <ProjectPositionEditor />,
      },
    ],
    { initialEntries: [path] },
  );

  const tree = () => (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
  const view = render(tree());
  return {
    ...view,
    router,
    refresh: () => act(() => identity.listeners.forEach((listener) => listener())),
  };
}

function change(key: TranslationKey, value: string) {
  fireEvent.change(screen.getByLabelText(t(key)), {
    target: { value },
  });
}

function save() {
  fireEvent.click(screen.getByRole("button", { name: t("projects.save") }));
}

function recalculate() {
  fireEvent.click(
    screen.getByRole("button", {
      name: t("projects.calculate"),
    }),
  );
}

async function ready(location = "Cocina") {
  await screen.findByRole("heading", { name: location });
  await screen.findByRole("option", { name: "GLASS-A" });
  await waitFor(() => {
    expect(screen.getByLabelText(t("projects.glassThickness"))).toHaveValue("24.00");
  });
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(engineLayout).mockResolvedValue(
    ok({ calculation_hash: "sha256:" + "a".repeat(64), nodes: [] }),
  );
  vi.spyOn(window, "confirm").mockReturnValue(true);
  identity.id = "org-a";
  identity.role = "OWNER";
  useCanvasStore.getState().reset();

  vi.mocked(engineSystems).mockResolvedValue(
    ok({
      systems: [
        {
          id: "system-a",
          code: "A",
          name: "Sistema A",
          is_demo: false,
          quote_ready: true,
          readiness_reasons: [],
        },
        {
          id: "system-b",
          code: "B",
          name: "Sistema B",
          is_demo: false,
          quote_ready: true,
          readiness_reasons: [],
        },
      ],
    }),
  );
  vi.mocked(projectDesignOptions).mockResolvedValue(
    ok({
      profiles: [],
      glazing_thicknesses: ["24.00", "28.00"],
      glass_skus: ["GLASS-A", "GLASS-B"],
      hardware_kits: [{ sku: "KIT-B", name: "Kit B", opening_type: "TURN" }],
      coupler_skus: [],
      colors: ["WHITE"],
    }),
  );
  retrieve.mockResolvedValue(ok(position()));
  calculate.mockResolvedValue(ok(bom("CUT-NEW")));
  update.mockResolvedValue(
    ok({
      ...position(),
      updated_at: "2026-09-18T15:01:00.123456Z",
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  clients.splice(0).forEach((client) => client.clear());
  useCanvasStore.getState().reset();
});

it("keeps the configurator available while creating a new position", async () => {
  mount("/projects/project-a/positions/new");

  const width = await screen.findByLabelText(t("intent.width"));
  expect(width).toBeEnabled();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
});

it("keeps a new design after an uncertain network response and prevents duplicate creation", async () => {
  create.mockRejectedValueOnce(new Error("connection lost after request"));
  mount("/projects/project-a/positions/new?copy=position-a");
  await ready();
  change("projects.location", "Copia pendiente");
  save();
  await screen.findByText(t("projects.uncertainPosition"));
  expect(screen.getByLabelText(t("projects.location"))).toHaveValue("Copia pendiente");
  expect(screen.getByText("CUT-A")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
  save();
  expect(create).toHaveBeenCalledOnce();
  expect(update).not.toHaveBeenCalled();
});
it("hides BOM on width draft, guards async validation, and preserves rejected width for retry", async () => {
  const first = deferred<Awaited<ReturnType<typeof engineCalculate>>>();
  const retry = deferred<Awaited<ReturnType<typeof engineCalculate>>>();
  calculate.mockReturnValueOnce(first.promise).mockReturnValueOnce(retry.promise);
  mount();
  await ready();

  const accepted = useCanvasStore.getState().inputs;
  change("intent.width", "1450.25");

  expect(calculate).not.toHaveBeenCalled();
  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
  expect(screen.getByText(t("projects.calculationRequired"))).toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
  expect(useCanvasStore.getState().inputs).toEqual(accepted);
  save();
  expect(update).not.toHaveBeenCalled();

  fireEvent.click(
    screen.getByRole("button", {
      name: t("intent.applyDimensions"),
    }),
  );

  expect(calculate).toHaveBeenCalledExactlyOnceWith(
    { ...position().design, nominal_width_mm: "1450.25" },
    { headers: { "X-Organization-ID": "org-a" } },
  );
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
  expect(screen.getByRole("button", { name: t("projects.calculate") })).toBeDisabled();
  expect(screen.getByLabelText(t("intent.width"))).toBeDisabled();
  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();

  const leaveWhilePending = new Event("beforeunload", { cancelable: true });
  window.dispatchEvent(leaveWhilePending);
  expect(leaveWhilePending.defaultPrevented).toBe(true);
  save();
  expect(update).not.toHaveBeenCalled();
  expect(create).not.toHaveBeenCalled();

  await act(async () => {
    first.reject(new Error("private validation trace"));
  });

  expect(screen.getByRole("alert")).toHaveTextContent(t("intent.rejected"));
  expect(screen.getByLabelText(t("intent.width"))).toHaveValue("1450.25");
  expect(screen.getByLabelText(t("intent.width"))).toBeEnabled();
  expect(useCanvasStore.getState().inputs).toEqual(accepted);
  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
  expect(screen.queryByText("private validation trace")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();

  fireEvent.click(
    screen.getByRole("button", {
      name: t("intent.applyDimensions"),
    }),
  );
  expect(calculate).toHaveBeenCalledTimes(2);
  expect(calculate.mock.calls[1]).toEqual(calculate.mock.calls[0]);
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();

  await act(async () => {
    retry.resolve(ok(bom("CUT-WIDTH")));
  });

  expect(screen.getByText("CUT-WIDTH")).toBeInTheDocument();
  expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1450.25");
  expect(screen.getByLabelText(t("intent.width"))).toHaveValue("1450.25");
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeEnabled();

  save();
  await waitFor(() => expect(update).toHaveBeenCalledOnce());
  expect(update).toHaveBeenCalledWith(
    "position-a",
    {
      location_tag: "Cocina",
      quantity: 4,
      design: { ...position().design, nominal_width_mm: "1450.25" },
      expected_updated_at: position().updated_at,
    },
    { headers: { "X-Organization-ID": "org-a" } },
  );
});

it("copies a position through create, preserves its exact design, and leaves the source untouched", async () => {
  const source = position();
  const sourceBefore = JSON.stringify(source);
  retrieve.mockResolvedValueOnce(ok(source));

  const pending = deferred<Awaited<ReturnType<typeof positionsCreate>>>();
  create.mockReturnValueOnce(pending.promise);
  const view = mount("/projects/project-a/positions/new?copy=position-a");
  await ready();

  expect(retrieve).toHaveBeenCalledExactlyOnceWith(source.id, {
    headers: { "X-Organization-ID": "org-a" },
  });
  expect(screen.getByText(t("projects.unsaved"))).toBeInTheDocument();
  expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue("4");
  expect(useCanvasStore.getState().inputs.parametricTree).toEqual(source.design.parametric_tree);

  change("projects.location", "Copia cocina");
  save();

  expect(create).toHaveBeenCalledExactlyOnceWith(
    source.project_id,
    {
      location_tag: "Copia cocina",
      quantity: source.quantity,
      design: source.design,
    },
    { headers: { "X-Organization-ID": "org-a" } },
  );
  expect(create.mock.calls[0]?.[1]).not.toHaveProperty("expected_updated_at");
  expect(update).not.toHaveBeenCalled();
  expect(calculate).not.toHaveBeenCalled();

  const copied: PositionResponse = {
    ...position("position-copy", "project-a", "Copia cocina"),
    position_index: 4,
    updated_at: "2026-09-18T16:00:00.123456Z",
  };
  retrieve.mockResolvedValueOnce(ok(copied));
  await act(async () => {
    pending.resolve({ ...ok(copied), status: 201 });
  });

  await waitFor(() => {
    expect(view.router.state.location.pathname).toBe(
      "/projects/project-a/positions/position-copy/edit",
    );
    expect(view.router.state.location.search).toBe("");
    expect(retrieve).toHaveBeenLastCalledWith(copied.id, {
      headers: { "X-Organization-ID": "org-a" },
    });
  });
  await ready("Copia cocina");
  expect(JSON.stringify(source)).toBe(sourceBefore);
  expect(create).toHaveBeenCalledOnce();
  expect(update).not.toHaveBeenCalled();

  // Reopen through the API mock; this asserts component isolation, not DB state.
  retrieve.mockResolvedValueOnce(ok(source));
  await act(async () => {
    await view.router.navigate("/projects/project-a/positions/position-a/edit");
  });
  await ready();
  expect(screen.getByLabelText(t("projects.location"))).toHaveValue("Cocina");
  expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue("4");
  expect(useCanvasStore.getState().inputs.parametricTree).toEqual(source.design.parametric_tree);
  expect(JSON.stringify(source)).toBe(sourceBefore);
  expect(update).not.toHaveBeenCalled();
});

it.each(["create", "update"] as const)(
  "sends only one %s for same-tick save clicks and unlocks after rejection",
  async (operation) => {
    const pendingCreate = deferred<Awaited<ReturnType<typeof positionsCreate>>>();
    const pendingUpdate = deferred<Awaited<ReturnType<typeof positionsUpdate>>>();
    const copied = position("position-copy");

    create.mockResolvedValue({ ...ok(copied), status: 201 });
    if (operation === "create") create.mockReturnValueOnce(pendingCreate.promise);
    else update.mockReturnValueOnce(pendingUpdate.promise);

    const view = mount(
      operation === "create"
        ? "/projects/project-a/positions/new?copy=position-a"
        : "/projects/project-a/positions/position-a/edit",
    );
    await ready();

    const button = screen.getByRole("button", { name: t("projects.save") });
    expect(button).toBeEnabled();

    // Both events run in one synchronous batch, before React commits busy state.
    act(() => {
      button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    const write = operation === "create" ? create : update;
    const otherWrite = operation === "create" ? update : create;
    expect(write).toHaveBeenCalledOnce();
    expect(otherWrite).not.toHaveBeenCalled();
    expect(button).toBeDisabled();

    await act(async () => {
      if (operation === "create")
        pendingCreate.reject(new ApiError(400, { error: { code: "validation_error" } }));
      else pendingUpdate.reject(new Error("write rejected"));
    });
    await screen.findByText(t("projects.saveError"));
    expect(screen.getByRole("button", { name: t("projects.save") })).toBeEnabled();

    if (operation === "create") retrieve.mockResolvedValueOnce(ok(copied));
    save();

    await waitFor(() => expect(write).toHaveBeenCalledTimes(2));
    expect(otherWrite).not.toHaveBeenCalled();
    if (operation === "create") {
      await waitFor(() =>
        expect(view.router.state.location.pathname).toBe(
          "/projects/project-a/positions/position-copy/edit",
        ),
      );
      await ready();
    } else {
      await screen.findByText(t("projects.saved"));
    }
    expect(write).toHaveBeenCalledTimes(2);
  },
);

it("hydrates exact saved fields and reopens the API-returned saved position", async () => {
  const original = position();
  const view = mount();
  await ready();

  expect(screen.getByLabelText(t("projects.location"))).toHaveValue("Cocina");
  expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue("4");
  expect(screen.getByLabelText(t("projects.system"))).toHaveValue("system-a");
  expect(screen.getByLabelText(t("intent.width"))).toHaveValue("1234.25");
  expect(screen.getByLabelText(t("intent.height"))).toHaveValue("987.50");
  expect(screen.getByLabelText(t("projects.glassComposition"))).toHaveValue("4-16-4 transparente");
  expect(screen.getByLabelText(t("projects.glassArticle"))).toHaveValue("GLASS-A");
  expect(screen.getByLabelText(t("projects.hardware"))).toHaveValue("");
  expect(useCanvasStore.getState().inputs).toEqual({
    systemId: original.design.system_id,
    nominalWidthMm: original.design.nominal_width_mm,
    nominalHeightMm: original.design.nominal_height_mm,
    color: original.design.color,
    parametricTree: original.design.parametric_tree,
    product: null,
  });
  expect(screen.getByText("CUT-A")).toBeInTheDocument();
  expect(calculate).not.toHaveBeenCalled();

  const saved: PositionResponse = {
    ...original,
    location_tag: "Dormitorio",
    quantity: 7,
    updated_at: "2026-09-18T15:01:00.123456Z",
  };
  update.mockResolvedValueOnce(ok(saved));
  change("projects.location", "Dormitorio");
  change("pricing.quantity", "7");
  save();

  await screen.findByText(t("projects.saved"));
  expect(update).toHaveBeenCalledExactlyOnceWith(
    original.id,
    {
      location_tag: "Dormitorio",
      quantity: 7,
      design: original.design,
      expected_updated_at: original.updated_at,
    },
    { headers: { "X-Organization-ID": "org-a" } },
  );
  expect(create).not.toHaveBeenCalled();
  expect(calculate).not.toHaveBeenCalled();

  view.unmount();
  retrieve.mockResolvedValueOnce(ok(saved));
  mount();
  await ready("Dormitorio");
  expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue("7");
  expect(useCanvasStore.getState().inputs.parametricTree).toEqual(saved.design.parametric_tree);
  expect(screen.getByText("CUT-A")).toBeInTheDocument();

  change("projects.location", "Dormitorio norte");
  save();
  await waitFor(() => expect(update).toHaveBeenCalledTimes(2));
  expect(update.mock.calls[1]?.[1].expected_updated_at).toBe(saved.updated_at);
});

it.each<[TranslationKey, string]>([
  ["projects.system", "system-b"],
  ["projects.glassThickness", "28.00"],
  ["projects.glassComposition", "Vidrio nuevo"],
  ["projects.glassArticle", "GLASS-B"],
  ["projects.hardware", "KIT-B"],
])("clears stale BOM immediately when %s changes", async (field, value) => {
  const pending = deferred<Awaited<ReturnType<typeof engineCalculate>>>();
  calculate.mockReturnValueOnce(pending.promise);
  mount();
  await ready();

  change(field, value);

  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
  expect(screen.getByText(t("projects.calculationRequired"))).toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
  expect(screen.getByText(t("projects.unsaved"))).toBeInTheDocument();

  recalculate();
  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
  expect(update).not.toHaveBeenCalled();

  await act(async () => {
    pending.resolve(ok(bom("CUT-NEW")));
  });

  expect(screen.getByText("CUT-NEW")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeEnabled();
  expect(calculate).toHaveBeenCalledWith(
    expect.objectContaining({
      system_id: field === "projects.system" ? "system-b" : "system-a",
      nominal_width_mm: "1234.25",
      nominal_height_mm: "987.50",
    }),
    { headers: { "X-Organization-ID": "org-a" } },
  );
});

it.each(["http", "network"] as const)(
  "preserves edited fields and concurrency token after %s save rejection",
  async (failure) => {
    if (failure === "network") {
      update.mockRejectedValueOnce(new Error("private backend trace"));
    } else {
      update.mockResolvedValueOnce({
        status: 409,
        headers: new Headers(),
        data: { error: { code: "stale_position", detail: "Rejected" } },
      });
    }
    mount();
    await ready();
    change("projects.location", "Entrada editada");
    change("pricing.quantity", "9");
    const designBefore = useCanvasStore.getState().inputs;

    save();
    await screen.findByText(t("projects.saveError"));

    expect(screen.getByLabelText(t("projects.location"))).toHaveValue("Entrada editada");
    expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue("9");
    expect(useCanvasStore.getState().inputs).toEqual(designBefore);
    expect(screen.getByText("CUT-A")).toBeInTheDocument();
    expect(screen.getByText(t("projects.unsaved"))).toBeInTheDocument();
    expect(screen.queryByText("private backend trace")).not.toBeInTheDocument();

    save();
    await waitFor(() => expect(update).toHaveBeenCalledTimes(2));
    expect(update.mock.calls[1]?.[1]).toEqual(update.mock.calls[0]?.[1]);
  },
);

it("preserves rejected material inputs for correction without restoring stale BOM", async () => {
  calculate.mockRejectedValueOnce(new Error("private calculation trace"));
  mount();
  await ready();
  const acceptedDesign = useCanvasStore.getState().inputs;

  change("projects.glassComposition", "Composición editada");
  change("projects.glassThickness", "28.00");
  recalculate();

  await screen.findByText(t("intent.rejected"));
  expect(screen.getByLabelText(t("projects.glassComposition"))).toHaveValue("Composición editada");
  expect(screen.getByLabelText(t("projects.glassThickness"))).toHaveValue("28.00");
  expect(useCanvasStore.getState().inputs).toEqual(acceptedDesign);
  expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: t("projects.save") })).toBeDisabled();
  expect(update).not.toHaveBeenCalled();

  recalculate();
  await screen.findByText("CUT-NEW");
  expect(calculate.mock.calls[1]?.[0].parametric_tree).toMatchObject({
    glass_spec: "Composición editada",
    glass_thickness_mm: "28.00",
  });
});

it.each(["", "0", "-1", "1.5", "1e2", "abc", "2147483648"])(
  "does not submit invalid quantity %j",
  async (quantity) => {
    // Includes the authoritative serializer's signed-int upper bound.
    // This case exposes a regression if UI validation checks only the regex.
    mount();
    await ready();
    change("pricing.quantity", quantity);
    save();

    expect(update).not.toHaveBeenCalled();
    expect(create).not.toHaveBeenCalled();
    expect(screen.getByLabelText(t("pricing.quantity"))).toHaveValue(quantity);
  },
);

it.each(["1", "12", "2147483647"])(
  "submits quantity %s as an integer without recalculating per-position BOM",
  async (quantity) => {
    mount();
    await ready();
    change("pricing.quantity", quantity);
    save();

    await waitFor(() => expect(update).toHaveBeenCalledOnce());
    expect(update.mock.calls[0]?.[1].quantity).toBe(Number(quantity));
    expect(update.mock.calls[0]?.[1].design).toEqual(position().design);
    expect(calculate).not.toHaveBeenCalled();
  },
);

it.each([
  ["organization", "retrieve"],
  ["navigation", "retrieve"],
  ["organization", "calculate"],
  ["navigation", "calculate"],
  ["organization", "save"],
  ["navigation", "save"],
] as const)(
  "ignores late %s-bound %s completion after the workspace changes",
  async (boundary, operation) => {
    const oldLoad = deferred<Awaited<ReturnType<typeof positionsRetrieve>>>();
    const oldCalculation = deferred<Awaited<ReturnType<typeof engineCalculate>>>();
    const oldSave = deferred<Awaited<ReturnType<typeof positionsUpdate>>>();

    if (operation === "retrieve") retrieve.mockReturnValueOnce(oldLoad.promise);
    if (operation === "calculate") calculate.mockReturnValueOnce(oldCalculation.promise);
    if (operation === "save") update.mockReturnValueOnce(oldSave.promise);

    const view = mount();
    if (operation === "retrieve") {
      await waitFor(() => expect(retrieve).toHaveBeenCalledOnce());
    } else {
      await ready();
      if (operation === "calculate") {
        change("projects.glassComposition", "Old pending material");
        recalculate();
        await waitFor(() => expect(calculate).toHaveBeenCalledOnce());
      } else {
        change("projects.location", "Old pending save");
        save();
        await waitFor(() => expect(update).toHaveBeenCalledOnce());
      }
    }

    const next =
      boundary === "organization"
        ? position("position-a", "project-a", "Tenant B")
        : position("position-b", "project-b", "Position B");
    next.design = { ...next.design, nominal_width_mm: "1555.75" };
    next.bom = bom("CUT-B");
    retrieve.mockResolvedValueOnce(ok(next));

    if (boundary === "organization") {
      identity.id = "org-b";
      view.refresh();
    } else {
      await act(async () => {
        await view.router.navigate("/projects/project-b/positions/position-b/edit");
      });
    }
    await ready(next.location_tag!);
    const currentInputs = useCanvasStore.getState().inputs;
    const currentPath = view.router.state.location.pathname;

    await act(async () => {
      if (operation === "retrieve") oldLoad.resolve(ok(position()));
      if (operation === "calculate") oldCalculation.resolve(ok(bom("CUT-LATE")));
      if (operation === "save") oldSave.resolve(ok(position()));
    });

    expect(useCanvasStore.getState().inputs).toEqual(currentInputs);
    expect(screen.getByLabelText(t("intent.width"))).toHaveValue("1555.75");
    expect(screen.getByLabelText(t("projects.location"))).toHaveValue(next.location_tag);
    expect(screen.getByText("CUT-B")).toBeInTheDocument();
    expect(screen.queryByText("CUT-A")).not.toBeInTheDocument();
    expect(screen.queryByText("CUT-LATE")).not.toBeInTheDocument();
    expect(screen.queryByText(t("projects.saved"))).not.toBeInTheDocument();
    expect(view.router.state.location.pathname).toBe(currentPath);
    expect(screen.getByRole("button", { name: t("projects.save") })).toBeEnabled();
    expect(retrieve).toHaveBeenLastCalledWith(next.id, {
      headers: {
        "X-Organization-ID": boundary === "organization" ? "org-b" : "org-a",
      },
    });
  },
);

it("refuses generic FOILED canvas state at the persisted project boundary", async () => {
  mount();
  await ready();
  act(() => {
    const inputs = useCanvasStore.getState().inputs;
    useCanvasStore.getState().loadDesign({ ...inputs, color: "FOILED" });
  });
  save();
  expect(update).not.toHaveBeenCalled();
  expect(create).not.toHaveBeenCalled();
});

it("does not offer FOILED or a catalog the backend marks incomplete", async () => {
  vi.mocked(engineSystems).mockResolvedValue(
    ok({
      systems: [
        {
          id: "system-a",
          code: "A",
          name: "Sistema A",
          is_demo: false,
          quote_ready: true,
          readiness_reasons: [],
        },
        {
          id: "system-b",
          code: "B",
          name: "Incomplete system",
          is_demo: false,
          quote_ready: false,
          readiness_reasons: ["manufacturing"],
        },
      ],
    }),
  );
  mount();
  await ready();
  expect(screen.queryByRole("option", { name: /FOILED|Foliado/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("option", { name: "Incomplete system" })).not.toBeInTheDocument();
});

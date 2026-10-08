import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import {
  catalogSystemList,
  engineSystems,
  clientsCreate,
  clientsList,
  projectsCreate,
  projectsList,
} from "../../api/generated/dekopen";
import { OnboardingPage } from "./OnboardingPage";
import { storageKey } from "./draft";

const scope = vi.hoisted(() => ({ org: "a" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    me: { active_organization: { id: scope.org, name: scope.org, role: "ESTIMATOR" } },
  }),
}));
vi.mock("../../api/generated/dekopen", () => ({
  catalogSystemList: vi.fn(),
  engineSystems: vi.fn(),
  clientsCreate: vi.fn(),
  clientsList: vi.fn(),
  projectsCreate: vi.fn(),
  projectsList: vi.fn(),
}));
const clientId = "00112233-4455-6677-8899-aabbccddeeff";
const projectId = "00112233-4455-6677-8899-aabbccddee00";

function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = () => (
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <OnboardingPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
  return { ...render(view()), view };
}
function draft(step = 1) {
  sessionStorage.setItem(
    storageKey(scope.org),
    JSON.stringify({
      schema: 2,
      step,
      clientName: "Fábrica Sur",
      clientId: step > 1 ? clientId : null,
      projectName: "Casa Sur",
    }),
  );
}
function clientRows(count: number) {
  return {
    status: 200,
    data: {
      items: Array.from({ length: count }, (_, i) => ({
        id: i ? projectId : clientId,
        name: "Fábrica Sur",
        rut: "",
        email: "",
        phone: "",
        updated_at: new Date().toISOString(),
      })),
    },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof clientsList>>;
}
beforeEach(() => {
  scope.org = "a";
  vi.resetAllMocks();
  sessionStorage.clear();
  vi.mocked(catalogSystemList).mockResolvedValue({
    status: 200,
    data: { items: [] },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof catalogSystemList>>);
  vi.mocked(engineSystems).mockResolvedValue({
    status: 200,
    data: { systems: [] },
    headers: new Headers(),
  });
});
afterEach(cleanup);

test("onboarding offers exactly the current series admitted by the engine", async () => {
  vi.mocked(catalogSystemList).mockResolvedValue({
    status: 200,
    data: {
      items: [
        { id: clientId, name: "Serie histórica", is_demo: true, readiness: { quote_ready: true } },
        { id: projectId, name: "Serie vigente", is_demo: true, readiness: { quote_ready: true } },
      ],
    },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof catalogSystemList>>);
  vi.mocked(engineSystems).mockResolvedValue({
    status: 200,
    data: {
      systems: [
        {
          id: projectId,
          name: "Serie vigente",
          code: "SUR",
          is_demo: true,
          quote_ready: true,
          system_family: "PVC_HINGED",
          readiness_reasons: [],
        },
      ],
    },
    headers: new Headers(),
  });
  mount();
  await screen.findByRole("button", { name: /Serie vigente/ });
  expect(screen.queryByRole("button", { name: /Serie histórica/ })).not.toBeInTheDocument();
});

test("adopts one fresh committed client after a lost response without repeating the create", async () => {
  draft();
  vi.mocked(clientsCreate).mockRejectedValue(new TypeError("connection lost"));
  vi.mocked(clientsList).mockResolvedValue(clientRows(1));
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Guardar cliente" }));
  await screen.findByRole("button", { name: "Crear obra" });
  expect(clientsCreate).toHaveBeenCalledTimes(1);
  expect(JSON.parse(sessionStorage.getItem(storageKey("a"))!)).toMatchObject({ clientId, step: 2 });
});

test("ambiguous fresh matches keep the draft and require a human retry", async () => {
  draft();
  vi.mocked(clientsCreate).mockRejectedValue(new TypeError("connection lost"));
  vi.mocked(clientsList).mockResolvedValue(clientRows(2));
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Guardar cliente" }));
  await screen.findByRole("alert");
  expect(screen.getByLabelText("Nombre del cliente")).toHaveValue("Fábrica Sur");
  expect(JSON.parse(sessionStorage.getItem(storageKey("a"))!).clientId).toBeNull();
});

test("a lost project response cannot adopt the same name for another client", async () => {
  draft(2);
  vi.mocked(projectsCreate).mockRejectedValue(new TypeError("connection lost"));
  vi.mocked(projectsList).mockResolvedValue({
    status: 200,
    data: {
      items: [
        {
          id: projectId,
          name: "Casa Sur",
          client_name: "Fábrica Sur",
          client_id: projectId,
          updated_at: new Date().toISOString(),
        },
      ],
    },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof projectsList>>);
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Crear obra" }));
  await screen.findByRole("alert");
  expect(JSON.parse(sessionStorage.getItem(storageKey("a"))!).projectId).toBeNull();
});

test("the first project preserves the client's contact for its later sealed quote", async () => {
  draft(2);
  const stored = JSON.parse(sessionStorage.getItem(storageKey("a"))!);
  stored.systemId = projectId;
  stored.clientExtra = {
    rut: " 1-9 ",
    email: " cliente@example.invalid ",
    phone: " +56912345678 ",
  };
  sessionStorage.setItem(storageKey("a"), JSON.stringify(stored));
  vi.mocked(catalogSystemList).mockResolvedValue({
    status: 200,
    data: {
      items: [
        { id: projectId, name: "Serie vigente", is_demo: true, readiness: { quote_ready: true } },
      ],
    },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof catalogSystemList>>);
  vi.mocked(engineSystems).mockResolvedValue({
    status: 200,
    data: {
      systems: [
        {
          id: projectId,
          code: "DEMO_60",
          name: "Serie vigente",
          system_family: "PVC",
          is_demo: true,
          quote_ready: true,
          readiness_reasons: [],
        },
      ],
    },
    headers: new Headers(),
  });
  vi.mocked(projectsCreate).mockResolvedValue({
    status: 201,
    data: { id: projectId },
    headers: new Headers(),
  } as Awaited<ReturnType<typeof projectsCreate>>);
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Crear obra" }));
  await screen.findByRole("link", { name: "Dibujar primera posición" });
  expect(projectsCreate).toHaveBeenCalledWith(
    expect.objectContaining({
      client_id: clientId,
      client_name: "Fábrica Sur",
      client_rut: "1-9",
      client_email: "cliente@example.invalid",
      client_phone: "+56912345678",
    }),
    expect.anything(),
  );
});

test("an old A request stays obsolete after switching from A to B and back to A", async () => {
  draft();
  let resolve!: (value: Awaited<ReturnType<typeof clientsCreate>>) => void;
  vi.mocked(clientsCreate).mockImplementation(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const mounted = mount();
  fireEvent.click(await screen.findByRole("button", { name: "Guardar cliente" }));
  scope.org = "b";
  mounted.rerender(mounted.view());
  await screen.findByRole("heading", { name: "Serie de perfiles" });
  scope.org = "a";
  mounted.rerender(mounted.view());
  await screen.findByRole("button", { name: "Guardar cliente" });
  await act(async () =>
    resolve({ status: 201, data: { id: clientId }, headers: new Headers() } as Awaited<
      ReturnType<typeof clientsCreate>
    >),
  );
  await waitFor(() =>
    expect(JSON.parse(sessionStorage.getItem(storageKey("a"))!).clientId).toBeNull(),
  );
  expect(screen.getByLabelText("Nombre del cliente")).toHaveValue("Fábrica Sur");
  expect(JSON.parse(sessionStorage.getItem(storageKey("b"))!).clientId).toBeNull();
});

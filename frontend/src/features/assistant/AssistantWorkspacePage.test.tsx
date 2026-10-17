import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { aiAgent, aiJobList, aiJobRetrieve, projectsList } from "../../api/generated/dekopen";
import { AssistantSurfaceProvider } from "./assistantContext";
import { AssistantWorkspacePage } from "./AssistantWorkspacePage";

vi.mock("../../api/generated/dekopen");
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    me: { user: { id: "user" }, active_organization: { id: "org", role: "ESTIMATOR" } },
  }),
}));

const job = {
  id: "job-1",
  state: "COMPLETED",
  goal: "Prepara una muestra",
  surface: "position",
  refs: { project_id: "project-1", position_id: "position-1" },
  updated_at: "2026-10-17T15:00:00Z",
  transcript: [
    { role: "user", text: "Prepara una muestra" },
    {
      role: "agent",
      reply: "Tu propuesta está lista.",
      artifacts: [
        {
          kind: "project_draft",
          title: "Ventana de cocina",
          payload: {
            positions: [{ label: "Cocina", width_mm: "1200", height_mm: "1000", quantity: 1 }],
          },
        },
      ],
    },
  ],
  outcomes: [
    { action: "applied", turn_index: 1, step_index: 0, created_at: "2026-10-17T15:00:00Z" },
  ],
};
const ok = (data: unknown) => ({ status: 200, headers: new Headers(), data }) as never;
beforeEach(() => {
  vi.mocked(aiJobList).mockResolvedValue(ok([job]));
  vi.mocked(aiJobRetrieve).mockResolvedValue(ok(job));
  vi.mocked(projectsList).mockResolvedValue(
    ok({ items: [{ id: "project-1", name: "Casa del lago", code: "P-000001" }] }),
  );
});

function room(entry: string | { pathname: string; state: unknown } = "/assistant") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>
        <AssistantSurfaceProvider>
          <AssistantWorkspacePage />
        </AssistantSurfaceProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

it("restores the conversation, selected artifact, decisions and the exact design context", async () => {
  room("/assistant?job=job-1&art=1:0&audit=1");
  expect(await screen.findByText("Tu propuesta está lista.")).toBeInTheDocument();
  expect(await screen.findByText("Ventana de cocina")).toBeInTheDocument();
  expect(document.getElementById("ai-artifact-1-0")).toHaveAttribute("open");
  expect(screen.getByText("Aplicado")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Abrir diseño" })).toHaveAttribute(
    "href",
    "/projects/project-1/positions/position-1/edit?assistant_job=job-1",
  );
  fireEvent.click(
    within(screen.getByRole("complementary", { name: "Tus conversaciones" })).getByRole("button", {
      name: "Nuevo encargo",
    }),
  );
  expect(await screen.findByText("De la idea a la ventana.")).toBeInTheDocument();
  expect(screen.queryByText("Tu propuesta está lista.")).not.toBeInTheDocument();
});

it("transfers an unsent dock draft without submitting or losing it", async () => {
  room({ pathname: "/assistant", state: { assistantDraft: "Haz las ventanas de esta casa" } });
  await waitFor(() =>
    expect(screen.getByRole("textbox")).toHaveValue("Haz las ventanas de esta casa"),
  );
  expect(aiAgent).not.toHaveBeenCalled();
});

it("delegates with the chosen work context and company preferences without technical selectors", async () => {
  const projectJob = { ...job, id: "job-2", surface: "project", refs: { project_id: "project-1" } };
  vi.mocked(aiAgent).mockResolvedValue({
    status: 202,
    headers: new Headers(),
    data: projectJob,
  } as never);
  vi.mocked(aiJobRetrieve).mockResolvedValue(ok(projectJob));
  room();
  await screen.findByRole("option", { name: "Casa del lago" });
  fireEvent.change(screen.getByRole("combobox", { name: "Obra para este encargo" }), {
    target: { value: "project-1" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Preparar una cotización/ }));
  await waitFor(() =>
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).value).toContain(
      "preferencias guardadas",
    ),
  );
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
  await waitFor(() => expect(aiAgent).toHaveBeenCalledOnce());
  expect(vi.mocked(aiAgent).mock.calls[0]?.[0]).toMatchObject({
    surface: "project",
    refs: { project_id: "project-1" },
  });
  expect(screen.queryByLabelText("Herramienta")).not.toBeInTheDocument();
});

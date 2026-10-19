import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { fieldWorkspace } from "../../api/generated/dekopen";
import { FieldPage } from "./FieldPage";

const auth = vi.hoisted(() => ({
  status: "ready",
  session: { user: { id: "actor" } },
  me: { active_organization: { id: "org", role: "WORKSHOP_MANAGER" } },
}));
vi.mock("../../auth/AuthSessionProvider", () => ({ useAuthSession: () => auth }));
vi.mock("../../api/generated/dekopen", () => ({
  fieldWorkspace: vi.fn(),
  fieldSchedule: vi.fn(),
  fieldAssetAccess: vi.fn(),
  fieldReview: vi.fn(),
  purchasingVersionState: vi.fn(),
}));
vi.mock("./outbox", () => ({
  detail: String,
  saveCopy: vi.fn(),
  pending: vi.fn().mockResolvedValue([]),
  readCopy: vi.fn(),
  discardRejected: vi.fn(),
  enqueue: vi.fn(),
  flush: vi.fn(),
}));
afterEach(cleanup);

it("keeps a measurement incident usable when its sealed evidence has no photograph", async () => {
  vi.mocked(fieldWorkspace).mockResolvedValue({
    data: {
      role: "WORKSHOP_MANAGER",
      projects: [],
      visits: [],
      assignees: [],
      incidents: [
        {
          id: "case",
          code: "INC-000001",
          visit_id: "visit",
          kind: "MEASURE",
          status: "OPEN",
          context: { project_code: "P-000001", project_name: "Casa", contact_name: "Cliente" },
          description: "Medición pendiente de revisión",
          evidence: { survey_id: "survey" },
          resolution: {},
          warranty: { reason: "Sin garantía declarada" },
        },
      ],
    },
  } as never);
  render(
    <MemoryRouter initialEntries={["/dispatch?view=cases"]}>
      <FieldPage office />
    </MemoryRouter>,
  );
  expect(await screen.findByText(/Sin fotografía en este registro/)).toBeTruthy();
  expect(screen.getByRole("button", { name: "Abrir ventana y visita de origen" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Guardar diagnóstico" })).toBeTruthy();
});

it("gives a historical visit with an empty project name a nonempty heading", async () => {
  vi.mocked(fieldWorkspace).mockResolvedValue({
    data: {
      role: "WORKSHOP_MANAGER",
      projects: [],
      incidents: [],
      assignees: [],
      visits: [
        {
          id: "visit",
          code: "VIS-000001",
          planned_on: "2026-10-12",
          team: "Sur",
          kind: "MEASUREMENT",
          status: "SCHEDULED",
          context: { project_name: "", project_code: "P-000002" },
        },
      ],
    },
  } as never);
  render(
    <MemoryRouter>
      <FieldPage office />
    </MemoryRouter>,
  );
  expect(await screen.findByRole("heading", { name: "P-000002" })).toBeTruthy();
});

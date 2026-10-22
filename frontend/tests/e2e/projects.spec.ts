import { expect, type Page, type Request, type TestInfo } from "@playwright/test";

import type {
  EngineAssemblyCalculateResponse,
  PositionResponse,
  ProjectResponse,
  WorksResponse,
} from "../../src/api/generated/models";
import { fmtMm } from "../../src/format";
import { test } from "./support/manual-project-fixture";

test.use({ viewport: { width: 1366, height: 768 }, actionTimeout: 15_000 });

async function responseTo<T>(
  page: Page,
  method: string,
  path: string,
  status: number,
  action: () => Promise<unknown>,
): Promise<T> {
  // Clone navigation can still have a GET in flight when reload starts.
  // Capture only new requests, then read their body before action() completes.
  const started = new Set<Request>();
  const remember = (request: Request) => {
    if (request.method() === method && new URL(request.url()).pathname === path) {
      started.add(request);
    }
  };
  page.on("request", remember);
  try {
    const [body] = await Promise.all([
      page
        .waitForResponse(
          (candidate) =>
            candidate.request().method() === method &&
            new URL(candidate.url()).pathname === path &&
            started.has(candidate.request()),
          { timeout: 20_000 },
        )
        .then(async (response) => {
          expect(response.status(), `${method} ${path}`).toBe(status);
          return (await response.json()) as T;
        }),
      action(),
    ]);
    return body;
  } finally {
    page.off("request", remember);
  }
}

async function screenshot(page: Page, info: TestInfo, name: string): Promise<void> {
  await page.evaluate(() => document.fonts.ready);
  expect(page.viewportSize()).toEqual({ width: 1366, height: 768 });
  const path = info.outputPath(`${name}-1366x768.png`);
  await page.screenshot({
    path,
    fullPage: false,
    animations: "disabled",
  });
  await info.attach(name, { path, contentType: "image/png" });
}

/** The project read adds the live engine price to the persisted window. */
function withWorkingPrice(project: ProjectResponse, position: PositionResponse): PositionResponse {
  expect(project.working_price?.state).toBe("READY");
  const line = project.working_price!.lines.find(
    (item) => item.position_index === position.position_index,
  );
  expect(line).toBeDefined();
  expect(line!.quantity).toBe(position.quantity);
  return {
    ...position,
    commercial: {
      unit_net: line!.unit_price,
      line_net: line!.line_net,
      source: "Precio de trabajo calculado con los datos vigentes.",
      ...("breakdown" in line! ? { breakdown: line!.breakdown } : {}),
      ...("catalog_use" in line! ? { catalog_use: line!.catalog_use } : {}),
    },
  };
}

/** Each window card opens the exact physical position in the editor. */
async function card(page: Page, location: string) {
  return page
    .getByRole("list", { name: "Ventanas" })
    .getByRole("button", { name: `Abrir ${location} en el editor`, exact: true })
    .first();
}

test("SHOT-10 real project core path and visual evidence", async ({ page, manual }, info) => {
  test.setTimeout(180_000);

  const projectName = `E2E sintético ${crypto.randomUUID()}`;
  const save = () => page.getByRole("button", { name: "Guardar", exact: true }).click();
  // Navigation uses the editor's accessible project backlink. React
  // Query may serve the project from its fresh cache without a fetch, so the
  // reload makes the backend round-trip (and in-memory reset) explicit.
  // Batch organization remains an explicit advanced destination in P06;
  // the default now opens the persistent list, drawing and inspector.
  const back = async () => {
    await page.locator(".project-head").getByRole("button", { name: "Más", exact: true }).click();
    await page.getByRole("menuitem", { name: "Organizar ventanas", exact: true }).click();
  };
  const toProjects = () =>
    page
      .getByRole("navigation", { name: "Ruta de navegación" })
      .getByRole("link", { name: "Obras", exact: true })
      .click();
  const freshRead = () => page.reload();

  // Obras reads its stage-aware projection since P05e. Keep the real GET
  // assertion on that endpoint before exercising the complete editing flow.
  const emptyProjects = await responseTo<WorksResponse>(
    page,
    "GET",
    "/api/v1/projects/works/",
    200,
    () => page.goto("/projects"),
  );
  expect(emptyProjects.items).toEqual([]);
  await expect(page.getByText("Aún no hay cotizaciones", { exact: true })).toBeVisible();
  // «Nueva cotización» creates the work at once and opens its first window;
  // the client and work data are completed from the work when needed.
  const created = await responseTo<ProjectResponse>(page, "POST", "/api/v1/projects/", 201, () =>
    page.getByRole("button", { name: "Nueva cotización", exact: true }).first().click(),
  );
  expect(created).toMatchObject({ status: "DRAFT", pricing_current: false });
  const projectPath = `/projects/${created.id}`;
  const projectApi = `/api/v1/projects/${created.id}/`;
  await expect(page).toHaveURL(new RegExp(`${projectPath}/positions/new`));
  await page.goto(projectPath);
  await page.locator(".project-head").getByRole("button", { name: "Más", exact: true }).click();
  await page.getByRole("menuitem", { name: "Datos de la obra y del cliente" }).click();
  const details = page.getByRole("group", { name: "Datos del proyecto", exact: true });
  const extra = details.locator("summary", { hasText: "Datos adicionales" });
  if (!(await details.locator("details[open]").count())) await extra.click();

  const metadata = [
    ["Nombre del proyecto", projectName],
    ["Cliente", "Cliente sintético E2E"],
    ["RUT", "1-9"],
    ["Correo", "cliente-e2e@example.test"],
    ["Teléfono", "+56900000000"],
    ["Dirección de entrega", "Dirección sintética; no despachar"],
    ["Notas comerciales", "Prueba automatizada; no emitir"],
    ["Notas internas", "DEMO_60 SYNTHETIC FIXTURE — tests only"],
  ] as const;
  for (const [label, value] of metadata) {
    await details.getByLabel(label, { exact: true }).fill(value);
  }

  const project = await responseTo<ProjectResponse>(page, "PATCH", projectApi, 200, () =>
    details.getByRole("button", { name: "Guardar", exact: true }).click(),
  );
  expect(project).toMatchObject({
    id: created.id,
    name: projectName,
    client_name: "Cliente sintético E2E",
    client_email: "cliente-e2e@example.test",
    notes_internal: "DEMO_60 SYNTHETIC FIXTURE — tests only",
    status: "DRAFT",
    pricing_current: false,
  });
  await expect(page).toHaveURL(new RegExp(`${projectPath}([?][^/]*)?$`));
  await expect(page.getByRole("heading", { level: 1 })).toContainText(projectName);
  await back();
  await expect(page.getByRole("link", { name: "Agregar ventanas", exact: true })).toBeVisible();
  await screenshot(page, info, "01-project-created");

  await page.getByRole("link", { name: "Agregar ventanas", exact: true }).click();
  await page.getByLabel("Ubicación de la ventana", { exact: true }).fill("Cocina original");
  await page.getByLabel("Cantidad", { exact: true }).fill("2");

  await page.locator(".editor-system-chip").click();
  await page.getByRole("checkbox", { name: "Mostrar ejemplos", exact: true }).check();
  await responseTo(page, "GET", `/api/v1/projects/design-options/${manual.systemId}/`, 200, () =>
    page
      .getByRole("combobox", { name: "Serie de perfiles", exact: true })
      .selectOption(manual.systemId),
  );

  // Choosing the catalog product derives thickness and evaluates the live canvas.
  await responseTo<EngineAssemblyCalculateResponse>(
    page,
    "POST",
    "/api/v1/engine/assembly/calculate/",
    200,
    () =>
      page
        .getByRole("combobox", { name: "Vidrio", exact: true })
        .selectOption("DEMO_60-VIDRIO-4-16-4"),
  );
  await expect(page.getByRole("combobox", { name: "Vidrio", exact: true })).toHaveValue(
    "DEMO_60-VIDRIO-4-16-4",
  );
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();

  const initial = await responseTo<PositionResponse>(
    page,
    "POST",
    `${projectApi}positions/`,
    201,
    save,
  );
  // Single-unit saves fold to the classic contract; the saved BOM is the
  // engine result for the folded design (bay ids are unnamespaced there).
  expect(initial.bom?.glasses?.[0]?.thickness_net_mm).toBe("8.00");
  expect(initial.bom?.profile_cuts?.length).toBeGreaterThan(0);
  expect(initial.quantity).toBe(2);
  const positionApi = `/api/v1/positions/${initial.id}/`;
  // The unified work selects the new saved window in its URL.
  await expect(page).toHaveURL(new RegExp(`${projectPath}\\?position=${initial.id}`));
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  // The shared registry refuses invalid edits atomically. The field returns
  // to the accepted design and a cause explains that the edit was not applied.
  await page.getByRole("textbox", { name: "Ancho", exact: true }).fill("10.00");
  const refused = await responseTo<{ error: { code: string } }>(
    page,
    "POST",
    "/api/v1/projects/operations/simulate/",
    422,
    () => page.getByRole("textbox", { name: "Ancho", exact: true }).press("Enter"),
  );
  expect(refused.error.code).toBe("dimension_invalid");
  await expect(page.getByRole("alert")).toContainText("Revisa el ancho y alto del marco.");
  await expect(page.getByRole("textbox", { name: "Ancho", exact: true })).toHaveValue("1000");
  expect(
    (await manual.readRows("project_positions", `id=eq.${initial.id}&select=width_mm::text`))[0]
      ?.width_mm,
  ).toBe("1000.00");

  // Exercise a real update, not only an unsaved creation preview.
  await page.getByRole("textbox", { name: "Ancho", exact: true }).fill("1100.25");
  await responseTo(page, "POST", "/api/v1/engine/assembly/calculate/", 200, () =>
    page.getByRole("textbox", { name: "Ancho", exact: true }).press("Enter"),
  );
  // Drafts are uncommitted until blur/Enter — the live model (and its
  // evaluation) is unchanged until the field commits.
  await page.getByRole("textbox", { name: "Alto", exact: true }).fill("1050.50");

  await responseTo(page, "POST", "/api/v1/engine/assembly/calculate/", 200, () =>
    page.getByRole("textbox", { name: "Alto", exact: true }).press("Enter"),
  );
  await page.locator(".editor-opening-trigger").click();
  const editedBom = (
    await responseTo<EngineAssemblyCalculateResponse>(
      page,
      "POST",
      "/api/v1/engine/assembly/calculate/",
      200,
      () =>
        page
          .locator(".opening-palette")
          .getByRole("button", {
            name: "Abatible hacia adentro — bisagras a la derecha",
            exact: true,
          })
          .click(),
    )
  ).bom!;
  expect(editedBom.hardware_items![0]!.kit_sku).toBe("DEMO_60-HW4-TURN-STANDARD");
  expect(editedBom.hardware_items![0]).toMatchObject({
    resolution: { class_name: "Estándar · DEMO", synthetic: true },
  });

  // Inject a transport failure only; successful writes still use the real backend.
  await page.route(`**${positionApi}`, async (route) => {
    if (route.request().method() === "PUT") await route.abort("failed");
    else await route.continue();
  });
  await save();
  await expect(page.getByText("Cambios sin guardar", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  await expect(page.getByRole("textbox", { name: "Ancho", exact: true })).toHaveValue("1100,25");
  const beforeRetry = await manual.readRows(
    "project_positions",
    `id=eq.${initial.id}&select=width_mm::text`,
  );
  expect(beforeRetry[0]?.width_mm).toBe("1000.00");
  await page.unroute(`**${positionApi}`);
  const saved = await responseTo<PositionResponse>(page, "PUT", positionApi, 200, save);
  expect(saved.design).toMatchObject({
    system_id: manual.systemId,
    nominal_width_mm: "1100.25",
    nominal_height_mm: "1050.50",
    parametric_tree: {
      type: "BAY",
      opening_use: "WINDOW",
      opening: {
        movement: "TURN",
        hinge_side: "RIGHT",
        direction: "INWARD",
        leaf_role: "SINGLE",
        fixed_in_sash: false,
      },
    },
  });
  expect(saved.bom?.hardware_items).toHaveLength(1);
  expect(saved.bom?.hardware_items?.[0]?.kit_sku).toBe("DEMO_60-HW4-TURN-STANDARD");
  expect(saved.bom?.hardware_items?.[0]).toMatchObject({
    resolution: { class_name: "Estándar · DEMO", synthetic: true },
  });
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Despiece y materiales", exact: true }).click();
  const bom = page.locator(".editor-bottom-panel .project-bom-content");
  const profileRows = bom.locator("table").first().locator("tbody tr");
  await expect(profileRows).toHaveCount(editedBom.profile_cuts.length);
  for (const [index, cut] of editedBom.profile_cuts.entries()) {
    await expect(profileRows.nth(index).locator("td")).toHaveText([
      cut.sku,
      fmtMm(cut.length_mm),
      String(cut.qty),
    ]);
  }
  // Top-of-editor composition at the requested real desktop viewport.
  // The editor names the window in its strip, not with a page heading.
  await page.evaluate(() => window.scrollTo(0, 0));
  await screenshot(page, info, "02-saved-configurator");
  await page.getByRole("button", { name: "Cerrar Despiece y materiales", exact: true }).click();

  const persisted = await manual.readRows(
    "project_positions",
    `id=eq.${saved.id}&org_id=eq.${manual.organizationId}` +
      "&select=id,width_mm::text,height_mm::text,parametric_tree,bom_snapshot",
  );
  expect(persisted).toHaveLength(1);
  expect(persisted[0]).toMatchObject({
    id: saved.id,
    width_mm: "1100.25",
    height_mm: "1050.50",
    parametric_tree: saved.design.parametric_tree,
    bom_snapshot: saved.bom,
  });

  // Leave both editor and project; full reload removes in-memory UI state.
  await back();
  await expect(page).toHaveURL(new RegExp(`${projectPath}([?][^/]*)?$`));
  const projectResponse = await responseTo<ProjectResponse>(
    page,
    "GET",
    projectApi,
    200,
    freshRead,
  );
  expect(projectResponse.status).toBe("DRAFT");
  expect(projectResponse.pricing_current).toBe(false);
  expect(projectResponse.position_count).toBe(1);
  await toProjects();
  await expect(page).toHaveURL(/\/projects$/);
  await page.reload();

  const reopenedProject = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, () =>
    // The work card reads status, name, client and total as one link.
    page.getByRole("link", { name: new RegExp(projectName) }).click(),
  );
  expect(reopenedProject.client_email).toBe("cliente-e2e@example.test");
  expect(reopenedProject.position_count).toBe(1);
  await back();

  // The one editor session survives the collection visit. Reload explicitly
  // to verify the persisted position rather than expecting a redundant GET.
  await (await card(page, "Cocina original")).click();
  const reopened = await responseTo<PositionResponse>(page, "GET", positionApi, 200, freshRead);
  expect(reopened).toEqual(saved);
  await expect(page.getByRole("textbox", { name: "Ancho", exact: true })).toHaveValue("1100,25");
  await expect(page.getByRole("textbox", { name: "Alto", exact: true })).toHaveValue("1050,5");
  await page.locator(".editor-opening-trigger").click();
  await expect(
    page.locator(".opening-palette").getByRole("button", {
      name: "Abatible hacia adentro — bisagras a la derecha",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Despiece y materiales", exact: true }).click();
  await bom.waitFor({ state: "visible" });
  await bom.scrollIntoViewIfNeeded();
  await screenshot(page, info, "03-reopened-bom");
  await page.getByRole("button", { name: "Cerrar Despiece y materiales", exact: true }).click();

  await back();
  await expect(page).toHaveURL(new RegExp(`${projectPath}([?][^/]*)?$`));
  await page.getByLabel("Seleccionar Cocina original", { exact: true }).check();
  // Duplicating is reversible: the engine previews and seals it, then it
  // applies at once and offers «Deshacer».
  const previewed = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      new URL(response.url()).pathname === `${projectApi}operations/preview/`,
  );
  const applied = await responseTo<{
    operation_id: string;
    state: string;
    project: ProjectResponse;
  }>(page, "POST", `${projectApi}operations/apply/`, 200, () =>
    page.getByRole("button", { name: "Duplicar", exact: true }).click(),
  );
  const proposal = (await (await previewed).json()) as { diff: { kind: string }[] };
  expect(proposal.diff).toHaveLength(1);
  expect(proposal.diff[0]!.kind).toBe("add");
  await expect(
    page.getByRole("button", { name: "Deshacer último cambio", exact: true }),
  ).toBeVisible();
  const copied = applied.project.positions!.find((item) => item.id !== saved.id)!;
  expect(copied.id).not.toBe(saved.id);
  expect(copied.design).toEqual(saved.design);
  expect(copied.bom).toEqual(saved.bom);
  expect(copied.measurements).toBeNull();
  expect(applied.state).toBe("APPLIED");
  const history = await manual.readRows(
    "project_edit_operations",
    `id=eq.${applied.operation_id}&org_id=eq.${manual.organizationId}` +
      "&select=id,org_id,project_id,state,request,before_state,after_state",
  );
  expect(history).toHaveLength(1);
  expect(history[0]).toMatchObject({
    id: applied.operation_id,
    org_id: manual.organizationId,
    project_id: project.id,
    state: "APPLIED",
    request: [{ op: "duplicate_positions", position_ids: [saved.id] }],
  });
  expect((history[0]!.before_state as { positions: unknown[] }).positions).toHaveLength(1);
  expect((history[0]!.after_state as { positions: unknown[] }).positions).toHaveLength(2);
  // The copy keeps the location and lands last in the work's order.
  const copyRow = page.getByRole("list", { name: "Ventanas" }).getByRole("listitem").nth(1);
  await responseTo(page, "GET", `/api/v1/positions/${copied.id}/`, 200, () =>
    copyRow.press("Enter"),
  );
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();
  await page.getByLabel("Ubicación de la ventana", { exact: true }).fill("Cocina duplicada");
  await expect(page.getByText("Cambios sin guardar", { exact: true })).toBeVisible();

  const duplicate = await responseTo<PositionResponse>(
    page,
    "PUT",
    `/api/v1/positions/${copied.id}/`,
    200,
    save,
  );
  expect(duplicate.id).not.toBe(saved.id);
  expect(duplicate.design).toEqual(saved.design);
  expect(duplicate.bom).toEqual(saved.bom);
  await expect(page).toHaveURL(
    new RegExp(`${projectPath}/positions/${duplicate.id}/edit(\\?view=\\w+)?$`),
  );
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  await back();
  await expect(page).toHaveURL(new RegExp(`${projectPath}([?][^/]*)?$`));
  const source = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, freshRead);
  expect(source.position_count).toBe(2);
  expect(source.positions!.find((item) => item.id === saved.id)).toEqual(
    withWorkingPrice(source, {
      ...saved,
      // Project collection metadata is separate from the persisted design/BOM.
      system_name: manual.systemName,
      system_demo: true,
    }),
  );

  // Work-level actions live in the header's «Más» menu.
  await page.locator(".project-head").getByRole("button", { name: "Más", exact: true }).click();
  const clone = await responseTo<ProjectResponse>(page, "POST", `${projectApi}clone/`, 201, () =>
    page.getByRole("menuitem", { name: "Duplicar proyecto", exact: true }).click(),
  );
  expect(clone.id).not.toBe(source.id);
  expect(clone).toMatchObject({
    status: "DRAFT",
    pricing_current: false,
    position_count: 2,
  });
  expect(clone.positions).toHaveLength(2);

  for (const copy of clone.positions!) {
    const original = source.positions!.find((item) => item.location_tag === copy.location_tag);
    expect(original).toBeDefined();
    expect(copy.id).not.toBe(original!.id);
    expect(copy.project_id).toBe(clone.id);
    expect(copy.design).toEqual(original!.design);
    expect(copy.bom).toEqual(original!.bom);
  }

  await expect(page).toHaveURL(new RegExp(`/projects/${clone.id}([?][^/]*)?$`));
  const reopenedClone = await responseTo<ProjectResponse>(
    page,
    "GET",
    `/api/v1/projects/${clone.id}/`,
    200,
    () => page.reload(),
  );
  expect(reopenedClone.positions).toEqual(
    clone.positions!.map((position) => withWorkingPrice(reopenedClone, position)),
  );
  await expect(page.getByRole("list", { name: "Ventanas" }).getByRole("listitem")).toHaveCount(2);
  await page.getByRole("heading", { level: 1 }).scrollIntoViewIfNeeded();
  await screenshot(page, info, "04-reopened-draft-clone");

  const unchangedSource = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, () =>
    page.goto(projectPath),
  );
  expect(unchangedSource).toEqual({
    ...source,
    working_price: { ...source.working_price, computed_at: expect.any(String) },
  });
  // The product keeps one light theme (constitution 2026-10): no theme switch.
  await expect(page.getByRole("button", { name: "Cambiar tema", exact: true })).toHaveCount(0);
  // Estimators can browse the catalog (and run supplier imports); structural
  // edits stay owner/manager-only.
  // A cold route first resolves the real catalog authority. Wait for that
  // request (with the same bounded API contract used above), then keep the
  // screen and permission assertions; a transport failure must still fail.
  const catalog = await responseTo<{ items: { id: string; is_demo: boolean }[] }>(
    page,
    "GET",
    "/api/v1/catalogs/systems/",
    200,
    () => page.goto("/catalogs/systems"),
  );
  expect(catalog.items.every((item) => !item.is_demo)).toBe(true);
  expect(catalog.items.some((item) => item.id === manual.systemId)).toBe(false);
  await expect(page.getByRole("heading", { name: "Catálogo", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Agregar serie", exact: true })).toHaveCount(0);
  await expect(page.locator(".series-catalog__examples")).not.toHaveAttribute("open");
  await page.locator(".series-catalog__examples > summary").click();
  await page.getByRole("button", { name: manual.systemName, exact: true }).click();
  await expect(page.getByRole("heading", { name: manual.systemName, exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar cambios", exact: true })).toHaveCount(0);
  await expect(page.getByRole("grid").locator("input[data-cell]").first()).toHaveAttribute(
    "readonly",
  );
});

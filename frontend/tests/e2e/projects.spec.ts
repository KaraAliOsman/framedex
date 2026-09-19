import { expect, type Page, type TestInfo } from "@playwright/test";

import type {
  EngineCalculateResponse,
  PositionResponse,
  ProjectResponse,
} from "../../src/api/generated/models";
import { test } from "./support/manual-project-fixture";

test.use({ viewport: { width: 1366, height: 768 }, actionTimeout: 15_000 });

async function responseTo<T>(
  page: Page,
  method: string,
  path: string,
  status: number,
  action: () => Promise<unknown>,
): Promise<T> {
  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) =>
        candidate.request().method() === method && new URL(candidate.url()).pathname === path,
      { timeout: 20_000 },
    ),
    action(),
  ]);
  expect(response.status(), `${method} ${path}`).toBe(status);
  return (await response.json()) as T;
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

function card(page: Page, location: string) {
  return page.locator("article.project-position").filter({
    has: page.locator("strong", { hasText: location }),
  });
}

test("SHOT-10 real project core path and visual evidence", async ({ page, manual }, info) => {
  test.setTimeout(180_000);

  const projectName = `E2E sintético ${crypto.randomUUID()}`;
  const save = () => page.getByRole("button", { name: "Guardar", exact: true }).click();
  const back = () => page.getByRole("link", { name: "Volver al proyecto", exact: true }).click();

  await page.goto("/projects");
  await expect(page.getByText("No hay proyectos que coincidan.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Crear proyecto", exact: true }).click();

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
    await page.getByLabel(label, { exact: true }).fill(value);
  }

  const project = await responseTo<ProjectResponse>(page, "POST", "/api/v1/projects/", 201, save);
  expect(project).toMatchObject({
    name: projectName,
    client_name: "Cliente sintético E2E",
    client_email: "cliente-e2e@example.test",
    notes_internal: "DEMO_60 SYNTHETIC FIXTURE — tests only",
    status: "DRAFT",
    pricing_current: false,
  });
  const projectPath = `/projects/${project.id}`;
  const projectApi = `/api/v1/projects/${project.id}/`;
  await expect(page).toHaveURL(new RegExp(`${projectPath}$`));
  await expect(page.getByRole("heading", { level: 1 })).toContainText(projectName);
  await expect(page.getByRole("link", { name: "Añadir vano" })).toBeVisible();
  await screenshot(page, info, "01-project-created");

  await page.getByRole("link", { name: "Añadir vano", exact: true }).click();
  await page.getByLabel("Ubicación del vano", { exact: true }).fill("Cocina original");
  await page.getByLabel("Cantidad", { exact: true }).fill("2");

  await responseTo(page, "GET", `/api/v1/projects/design-options/${manual.systemId}/`, 200, () =>
    page
      .getByRole("combobox", { name: "Serie de perfiles", exact: true })
      .selectOption(manual.systemId),
  );
  await page
    .getByRole("combobox", { name: "Espesor del vidrio (mm)", exact: true })
    .selectOption("20.00");
  await page.getByLabel("Composición del vidrio", { exact: true }).fill("4-12-4 Float Incoloro");

  const fixedBom = await responseTo<EngineCalculateResponse>(
    page,
    "POST",
    "/api/v1/engine/calculate/",
    200,
    () =>
      page
        .getByRole("button", {
          name: "Validar diseño y materiales",
          exact: true,
        })
        .click(),
  );
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();

  const initial = await responseTo<PositionResponse>(
    page,
    "POST",
    `${projectApi}positions/`,
    201,
    save,
  );
  expect(initial.bom).toEqual(fixedBom);
  expect(initial.quantity).toBe(2);
  const positionApi = `/api/v1/positions/${initial.id}/`;
  const editPath = `${projectPath}/positions/${initial.id}/edit`;
  await expect(page).toHaveURL(new RegExp(`${editPath}$`));
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  // Invalid intent cannot expose a previous result as the current calculation.
  await page.getByLabel("Ancho nominal (mm)", { exact: true }).fill("10.00");
  await responseTo(page, "POST", "/api/v1/engine/calculate/", 400, () =>
    page.getByRole("button", { name: "Aplicar medidas", exact: true }).click(),
  );
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("Ancho nominal (mm)", { exact: true })).toHaveValue("10.00");
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeDisabled();
  await expect(page.locator("details.project-bom")).toHaveCount(0);

  // Exercise a real update, not only an unsaved creation preview.
  await page.getByLabel("Ancho nominal (mm)", { exact: true }).fill("1100.25");
  await page.getByLabel("Alto nominal (mm)", { exact: true }).fill("1050.50");
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeDisabled();

  await responseTo(page, "POST", "/api/v1/engine/calculate/", 200, () =>
    page.getByRole("button", { name: "Aplicar medidas", exact: true }).click(),
  );
  const editedBom = await responseTo<EngineCalculateResponse>(
    page,
    "POST",
    "/api/v1/engine/calculate/",
    200,
    () =>
      page
        .getByRole("combobox", { name: "Apertura y sentido", exact: true })
        .selectOption("TURN_RIGHT"),
  );
  expect(editedBom.hardware_items).toHaveLength(1);
  expect(editedBom.hardware_items[0]!.kit_sku).toBe("KIT-TURN");

  // Inject a transport failure only; successful writes still use the real backend.
  await page.route(`**${positionApi}`, async (route) => {
    if (route.request().method() === "PUT") await route.abort("failed");
    else await route.continue();
  });
  await save();
  await expect(page.getByText("Cambios sin guardar", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  await expect(page.getByLabel("Ancho nominal (mm)", { exact: true })).toHaveValue("1100.25");
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
    parametric_tree: { type: "BAY", opening_type: "TURN_RIGHT" },
  });
  expect(saved.bom).toEqual(editedBom);
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  const bom = page.locator("details.project-bom");
  await bom.locator("summary").click();
  const profileRows = bom.locator("table").first().locator("tbody tr");
  await expect(profileRows).toHaveCount(editedBom.profile_cuts.length);
  for (const [index, cut] of editedBom.profile_cuts.entries()) {
    await expect(profileRows.nth(index).locator("td")).toHaveText([
      cut.sku,
      cut.length_mm,
      String(cut.qty),
    ]);
  }
  // Top-of-editor composition at the requested real desktop viewport.
  await page.getByRole("heading", { level: 1 }).scrollIntoViewIfNeeded();
  await screenshot(page, info, "02-saved-configurator");

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
    bom_snapshot: editedBom,
  });

  // Leave both editor and project; full reload removes in-memory UI state.
  await responseTo(page, "GET", projectApi, 200, back);
  await back();
  await expect(page).toHaveURL(/\/projects$/);
  await page.reload();

  const reopenedProject = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, () =>
    page
      .getByRole("link", {
        name: `${project.code} · ${projectName}`,
        exact: true,
      })
      .click(),
  );
  expect(reopenedProject.client_email).toBe("cliente-e2e@example.test");
  expect(reopenedProject.position_count).toBe(1);

  const reopened = await responseTo<PositionResponse>(page, "GET", positionApi, 200, () =>
    card(page, "Cocina original").getByRole("link", { name: "Abrir diseño", exact: true }).click(),
  );
  expect(reopened).toEqual(saved);
  await expect(page.getByLabel("Ancho nominal (mm)", { exact: true })).toHaveValue("1100.25");
  await expect(page.getByLabel("Alto nominal (mm)", { exact: true })).toHaveValue("1050.50");
  await expect(page.getByRole("combobox", { name: "Apertura y sentido", exact: true })).toHaveValue(
    "TURN_RIGHT",
  );
  await bom.locator("summary").click();
  await bom.scrollIntoViewIfNeeded();
  await screenshot(page, info, "03-reopened-bom");

  await responseTo(page, "GET", projectApi, 200, back);
  await responseTo(page, "GET", positionApi, 200, () =>
    card(page, "Cocina original").getByRole("link", { name: "Duplicar vano", exact: true }).click(),
  );
  await expect(page.getByText("Cambios sin guardar", { exact: true })).toBeVisible();
  await page.getByLabel("Ubicación del vano", { exact: true }).fill("Cocina duplicada");

  const duplicate = await responseTo<PositionResponse>(
    page,
    "POST",
    `${projectApi}positions/`,
    201,
    save,
  );
  expect(duplicate.id).not.toBe(saved.id);
  expect(duplicate.design).toEqual(saved.design);
  expect(duplicate.bom).toEqual(saved.bom);
  await expect(page).toHaveURL(new RegExp(`${projectPath}/positions/${duplicate.id}/edit$`));
  await expect(page.getByText("Guardado", { exact: true })).toBeVisible();

  const source = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, back);
  expect(source.position_count).toBe(2);
  expect(source.positions!.find((item) => item.id === saved.id)).toEqual(saved);

  const clone = await responseTo<ProjectResponse>(page, "POST", `${projectApi}clone/`, 201, () =>
    page
      .getByRole("button", {
        name: "Duplicar proyecto",
        exact: true,
      })
      .click(),
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

  await expect(page).toHaveURL(new RegExp(`/projects/${clone.id}$`));
  const reopenedClone = await responseTo<ProjectResponse>(
    page,
    "GET",
    `/api/v1/projects/${clone.id}/`,
    200,
    () => page.reload(),
  );
  expect(reopenedClone.positions).toEqual(clone.positions);
  await expect(page.locator("article.project-position")).toHaveCount(2);
  await page.getByRole("heading", { level: 1 }).scrollIntoViewIfNeeded();
  await screenshot(page, info, "04-reopened-draft-clone");

  const unchangedSource = await responseTo<ProjectResponse>(page, "GET", projectApi, 200, () =>
    page.goto(projectPath),
  );
  expect(unchangedSource).toEqual(source);
  await page.getByRole("button", { name: "Cambiar tema", exact: true }).click();
  await screenshot(page, info, "05-project-dark");
  await page.goto("/catalogs/systems");
  await expect(page.getByRole("alert")).toContainText("propietario y el jefe de taller");
});

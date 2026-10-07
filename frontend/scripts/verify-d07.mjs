import { collectPresentationFindings } from "./ux-capture/collect.ts";
import { chromium, expect } from "@playwright/test";
import * as OTPAuth from "otpauth";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { detectTextFindings } from "./ux-capture/detectors.ts";
const base = "http://127.0.0.1:5173",
  api = "http://127.0.0.1:8000/api/v1";
const supa = process.env.SUPABASE_URL,
  anon = process.env.SUPABASE_ANON_KEY;
const org = "548b9ce5-746b-5a4a-9127-733c4dcd0582";
const out = fileURLToPath(
  new URL("../../docs/redesign/captures/vano-fabricacion/recorrido", import.meta.url),
);
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("D07 verification requires the owned local Supabase stack.");
const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const sessions = new Map();
let factor, lastPage;
const records = [];
async function auth(role) {
  if (sessions.has(role)) return sessions.get(role);
  const r = await fetch(supa + "/auth/v1/token?grant_type=password", {
    method: "POST",
    headers: { apikey: anon, "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `demo-${role}@fixture.dekopen.local`,
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!r.ok) throw new Error("Login " + r.status);
  let session = await r.json();
  if (role === "owner") {
    const h = {
      apikey: anon,
      Authorization: "Bearer " + session.access_token,
      "Content-Type": "application/json",
    };
    const en = await fetch(supa + "/auth/v1/factors", {
      method: "POST",
      headers: h,
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d07-" + Date.now() }),
    });
    if (!en.ok) throw new Error("MFA enroll " + en.status);
    factor = await en.json();
    const ch = await fetch(supa + `/auth/v1/factors/${factor.id}/challenge`, {
      method: "POST",
      headers: h,
      body: "{}",
    });
    const challenge = await ch.json();
    const code = new OTPAuth.TOTP({
      secret: OTPAuth.Secret.fromBase32(factor.totp.secret),
      algorithm: "SHA1",
      digits: 6,
      period: 30,
    }).generate();
    const vr = await fetch(supa + `/auth/v1/factors/${factor.id}/verify`, {
      method: "POST",
      headers: h,
      body: JSON.stringify({ challenge_id: challenge.id, code }),
    });
    if (!vr.ok) throw new Error("MFA verify " + vr.status);
    session = { ...session, ...(await vr.json()) };
  }
  sessions.set(role, session);
  return session;
}
async function request(role, path, body, method) {
  const a = await auth(role);
  const r = await fetch(api + path, {
    method: method ?? (body ? "POST" : "GET"),
    headers: {
      Authorization: "Bearer " + a.access_token,
      "X-Organization-ID": org,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json();
  if (!r.ok) throw new Error(path + " " + r.status + " " + JSON.stringify(data));
  return data;
}
async function pageFor(role, theme = "light", size = { width: 1440, height: 900 }) {
  const a = await auth(role);
  const context = await browser.newContext({
    viewport: size,
    storageState: {
      cookies: [],
      origins: [
        {
          origin: base,
          localStorage: [
            { name: "sb-127-auth-token", value: JSON.stringify(a) },
            { name: `dekopen.active_org.${a.user.id}`, value: org },
            { name: "dekopen.theme", value: theme },
          ],
        },
      ],
    },
  });
  const page = await context.newPage();
  lastPage = page;
  page.on("dialog", (d) => d.accept());
  page.errors = [];
  page.on("pageerror", (e) => page.errors.push(e.message));
  return page;
}
async function capture(page, name, scope) {
  await page.waitForLoadState("networkidle");
  const file = name + ".png";
  await page.mouse.move(12, 12);
  await page.screenshot({ path: out + "/" + file });
  const text = await page.locator("body").innerText();
  const scopeText = scope
    ? (await page.locator(scope).allInnerTexts()).join(" ")
    : name.startsWith("catalogo-")
      ? await page.locator(".catalog-editor").innerText()
      : text;
  records.push({
    name,
    screenshot: file,
    width: await page.evaluate(() => innerWidth),
    overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    errors: page.errors,
    findings: detectTextFindings(scopeText),
    pageFindings: detectTextFindings(text),
    presentation: await collectPresentationFindings(
      page,
      name.startsWith("pedido-"),
      ".mounting-inspector *, .mounting-chip *, .measurement-panel *, .mounting-settings *, .rectification-panel *",
    ),
  });
  const record = records.at(-1);
  if (record.overflow)
    record.overflowElements = await page.locator("body").evaluate((body) =>
      [...body.querySelectorAll("*")]
        .filter((element) => {
          const rect = element.getBoundingClientRect();
          return rect.width && rect.right > innerWidth + 1;
        })
        .map((element) => ({
          tag: element.tagName,
          className: element.className?.toString(),
          text: element.textContent?.slice(0, 80),
        }))
        .slice(-25),
    );
  if (record.overflow || page.errors.length || record.findings.length || record.presentation.length)
    throw new Error(name + " " + JSON.stringify(record));
  console.log("PASA", name);
}

async function verifySettings(state) {
  const page = await pageFor("owner");
  await page.goto(base + "/settings/general");
  const panel = page.getByRole("region", { name: "Vano y montaje", exact: true });
  await panel.getByLabel("Serie de perfiles").selectOption(state.system);
  const row = panel.locator(".mounting-rule-row").filter({ hasText: "En vano con holgura" });
  await row.getByRole("button", { name: "Revisar regla" }).click();
  await panel
    .locator(".mounting-rule-sides label")
    .filter({ hasText: "Holgura (mm)" })
    .first()
    .locator("input")
    .fill("12");
  await panel
    .locator(".mounting-rule-sides label")
    .filter({ hasText: "Ensanche (mm)" })
    .first()
    .locator("input")
    .fill("20");
  await panel.getByText("Ensanches y accesorios de fijación", { exact: true }).click();
  const catalog = await request("owner", `/projects/design-options/${state.system}/`);
  const extension = catalog.extra_definitions.find(
    (item) => item.profile_role === "FRAME_EXTENSION",
  );
  await panel.getByRole("checkbox", { name: extension.name, exact: false }).check();
  const accessorySides = panel.getByRole("group", {
    name: `Lados de ${extension.name}`,
    exact: true,
  });
  for (const name of ["Derecho", "Inferior", "Superior"]) {
    const checkbox = accessorySides.getByLabel(name, { exact: true });
    if (await checkbox.count()) await checkbox.uncheck();
  }
  await panel
    .getByLabel("Motivo del cambio")
    .fill("Ensayo DEMO de autoridad nueva y restauración explícita");
  await panel.getByRole("button", { name: "Revisar cambios", exact: true }).click();
  await panel
    .getByRole("button", { name: "Guardar autoridad de montaje" })
    .scrollIntoViewIfNeeded();
  await capture(page, "ajustes-diff-fuente", ".mounting-settings");
  await panel.getByRole("button", { name: "Guardar autoridad de montaje" }).click();
  await expect(panel.getByRole("button", { name: "Deshacer último cambio" })).toBeVisible();
  const changedRules = await request("estimator", `/organization/mounting/${state.system}/`);
  const changed = changedRules.items.find((item) => item.rule.code === "IN_OPENING").rule;
  expect(changed.left.extension_mm).toBe("20");
  expect(changed.extras.find((item) => item.code === extension.code).sides).toEqual(["LEFT"]);
  await panel.getByRole("button", { name: "Deshacer último cambio" }).click();
  await expect(panel.getByRole("button", { name: "Deshacer último cambio" })).toBeVisible();
  const saved = await request("estimator", `/positions/${state.position.id}/`);
  expect(saved.measurements.measurements[0].rule.left.clearance_mm).toBe("10");
  await page.context().close();
  const reader = await pageFor("estimator");
  await reader.goto(base + "/settings/general");
  const readPanel = reader.getByRole("region", { name: "Vano y montaje", exact: true });
  await readPanel.getByLabel("Serie de perfiles").selectOption(state.system);
  await expect(readPanel).toContainText("El dueño o encargado declara");
  await expect(readPanel.getByRole("button", { name: "Revisar regla" })).toHaveCount(0);
  await readPanel.scrollIntoViewIfNeeded();
  await capture(reader, "ajustes-consulta-estimador", ".mounting-settings");
  await reader.context().close();
}

async function seal(projectId) {
  const prepared = await request("estimator", `/documents/projects/${projectId}/inputs/`);
  const positions = prepared.positions.map((pos) => {
    const annotations = new Map();
    for (const row of pos.workshop_suggestions) {
      const key = JSON.stringify([row.bay_id, row.leaf_id]);
      annotations.set(key, {
        ...(annotations.get(key) ?? {}),
        ...Object.fromEntries(Object.entries(row).filter(([, value]) => value != null)),
      });
    }
    return {
      position_id: pos.position_id,
      calculation_hash: pos.calculation_hash,
      location_tag: pos.location_tag,
      manufacturing_placement_policy_id: pos.placement_options[0].id,
      handle_requirement_policy_id: pos.handle_options[0].id,
      reinforcement_cut_policy_id: pos.reinforcement_options[0].id,
      workshop_annotations: [...annotations.values()],
      structural_inputs: [],
      glass_polishing: pos.polishing_suggestions,
      handle_intents: [],
      accessory_schedule: { schema_version: 1, coverage: "NONE_REQUIRED", items: [] },
      legacy_handle_migration_confirmed: true,
    };
  });
  await request(
    "estimator",
    `/documents/projects/${projectId}/inputs/`,
    {
      payment_terms: "Anticipo 50 %, saldo al entregar",
      quotation_valid_until: "2026-11-06",
      positions,
    },
    "PUT",
  );
  const priced = await request("estimator", "/pricing/preview/", {
    project_id: projectId,
    pricing_mode: "COST_PLUS_MARGIN",
    context_code: "DEFAULT",
    currency: "CLP",
    effective_date: "2026-10-07",
    discount_pct: "0",
    target_margin: "0.35",
    segment: "RETAIL",
    confirmed: false,
    reason: "Medidas de obra DEMO revisadas antes de emisión",
  });
  await request("estimator", `/pricing/operations/${priced.id}/apply/`, {
    reason: "Venta revisada en ensayo D07",
    confirmed: true,
  });
  return request("estimator", `/documents/projects/${projectId}/freeze/`, {
    pricing_operation_id: priced.id,
    confirmed: true,
  });
}

async function artifact(version, type, name, orderId) {
  const created = await request(
    type === "DOC-03" ? "manager" : "estimator",
    "/documents/artifacts/",
    {
      document_type: type,
      format: "PDF",
      project_version_id: version.id,
      ...(orderId ? { order_id: orderId } : {}),
    },
  );
  const access = await request(
    type === "DOC-03" ? "manager" : "estimator",
    `/documents/artifacts/${created.id}/access/`,
    {},
    "POST",
  );
  const pdf = await fetch(access.signed_url);
  expect(pdf.ok).toBe(true);
  const bytes = Buffer.from(await pdf.arrayBuffer());
  expect(bytes.subarray(0, 4).toString()).toBe("%PDF");
  await fs.writeFile(out + "/" + name, bytes);
  return created.id;
}

async function verifyMatrix(state) {
  const route = `/projects/${state.project.id}/positions/${state.position.id}/edit`;
  for (const theme of ["light", "dark"]) {
    for (const size of [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 1024, height: 768 },
    ]) {
      const page = await pageFor("estimator", theme, size);
      await page.goto(base + route);
      const panel = page.locator(".mounting-inspector");
      await expect(panel.locator(".mounting-chip")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const useCurrent = panel.getByRole("button", { name: "Usar regla actual", exact: true });
      if (await useCurrent.count()) await useCurrent.click();
      const dimension = page.locator(".mounting-dimensions");
      await expect(dimension).toBeVisible();
      const clipped = await dimension.evaluate((element) => {
        const sheet = element.closest("svg").getBoundingClientRect();
        return [...element.querySelectorAll("text")].some((label) => {
          const box = label.getBoundingClientRect();
          return (
            box.top < sheet.top ||
            box.bottom > sheet.bottom ||
            box.left < sheet.left ||
            box.right > sheet.right
          );
        });
      });
      expect(clipped, "las cotas del vano y fabricación caben en la hoja").toBe(false);
      await panel.evaluate((element) => element.scrollIntoView({ block: "start" }));
      const visibleFields = await panel.evaluate((element) => {
        const rail = element.closest(".assembly-side").getBoundingClientRect();
        return [...element.querySelectorAll("select, input:not([type=checkbox])")].filter(
          (field) => {
            const rect = field.getBoundingClientRect();
            return rect.height && rect.top >= rail.top && rect.bottom <= rail.bottom;
          },
        ).length;
      });
      expect(visibleFields, "ocho campos de montaje caben en el inspector").toBeGreaterThanOrEqual(
        8,
      );
      await capture(page, `inspector-${theme}-${size.width}`, ".mounting-inspector");
      await page.context().close();
      const settings = await pageFor("owner", theme, size);
      await settings.goto(base + "/settings/general");
      const authority = settings.getByRole("region", { name: "Vano y montaje", exact: true });
      await authority.getByLabel("Serie de perfiles").selectOption(state.system);
      await expect(authority.locator(".mounting-rule-row").first()).toBeVisible();
      await authority.scrollIntoViewIfNeeded();
      await capture(settings, `montajes-${theme}-${size.width}`, ".mounting-settings");
      await settings.context().close();
    }
  }
  const systems = await request("estimator", "/engine/systems/");
  const other = systems.systems.find((item) => item.id !== state.system);
  const empty = await pageFor("estimator");
  await empty.goto(base + route);
  await empty.getByLabel("Serie de perfiles", { exact: true }).selectOption(other.id);
  await expect(empty.locator(".mounting-inspector")).toContainText("no tiene montaje declarado");
  await empty.locator(".mounting-inspector").scrollIntoViewIfNeeded();
  await capture(empty, "estado-sin-montaje", ".mounting-inspector");
  await empty.context().close();
  const error = await pageFor("estimator");
  await error.route("**/api/v1/organization/mounting/**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: { code: "fixture", detail: "Fuente temporalmente fuera de servicio; ensayo" },
      }),
    }),
  );
  await error.goto(base + route);
  await expect(error.locator(".mounting-inspector")).toContainText(
    "No pudimos cargar los montajes",
    { timeout: 30000 },
  );
  await error.locator(".mounting-inspector").scrollIntoViewIfNeeded();
  await capture(error, "estado-error-reintento", ".mounting-inspector");
  await error.unroute("**/api/v1/organization/mounting/**");
  await error.locator(".mounting-inspector").getByRole("button", { name: "Reintentar" }).click();
  await expect(error.locator(".mounting-inspector .mounting-chip")).toBeVisible();
  await error.context().close();
  const loading = await pageFor("estimator");
  let release;
  await loading.route("**/api/v1/organization/mounting/**", async (route) => {
    await new Promise((resolve) => {
      release = resolve;
    });
    await route.continue();
  });
  await loading.goto(base + route, { waitUntil: "domcontentloaded" });
  await expect(loading.locator(".mounting-inspector")).toContainText("Cargando reglas");
  await loading.locator(".mounting-inspector").scrollIntoViewIfNeeded();
  await loading.mouse.move(12, 12);
  await loading.screenshot({ path: out + "/estado-carga.png" });
  release();
  await expect(loading.locator(".mounting-inspector .mounting-chip")).toBeVisible();
  await loading.context().close();
  const denied = await pageFor("installer");
  await denied.goto(base + route);
  await expect(denied.getByText("Sin acceso", { exact: true })).toBeVisible();
  await capture(denied, "estado-sin-permiso", "main");
  await denied.context().close();
  const chain = JSON.parse(await fs.readFile(".run/d07-chain-state.json", "utf8"));
  const blocked = await pageFor("estimator");
  await blocked.goto(base + `/projects/${chain.project.id}/positions/${chain.position.id}/edit`);
  await expect(blocked.getByText("Revisión cerrada para edición", { exact: true })).toBeVisible();
  await capture(blocked, "estado-revision-cerrada", "main");
  await blocked.context().close();
  console.log(
    "PASA tres anchos y dos temas; vacío, carga, error/reintento, sin permiso y revisión bloqueada",
  );
}

async function verifyChain(state) {
  const latestRules = await request("estimator", `/organization/mounting/${state.system}/`);
  const sourcePosition = state.position;
  state.project = await request("estimator", "/projects/", {
    name: "D07 · revisión de medición DEMO",
    client_name: "Cliente de ensayo",
    client_email: "d07@example.test",
    delivery_address: "Valdivia",
  });
  state.position = await request("estimator", `/projects/${state.project.id}/positions/`, {
    location_tag: "Fachada medida · DEMO",
    quantity: 1,
    design: sourcePosition.design,
    measurements: sourcePosition.measurements.measurements.map((item) => ({
      ...item.survey,
      rule_revision: latestRules.items.find((rule) => rule.rule.code === item.survey.rule_code)
        .revision,
    })),
  });
  await request("estimator", `/positions/${state.position.id}/measurements/confirm/`, {
    expected_updated_at: state.position.updated_at,
    expected_generation: state.position.measurements.generation,
    confirmed: true,
    acknowledge_warnings: true,
    reason: "Estimador verificó antecedente de ensayo D07",
  });
  await verifySettings(state);
  const versionA = await seal(state.project.id);
  expect(versionA.production_allowed).toBe(true);
  const artifactA = await artifact(versionA, "DOC-01", "cotizacion-revision-a.pdf");
  const link = await request("estimator", `/projects/${state.project.id}/quote-link/`, {});
  const portal = await browser.newPage({ viewport: { width: 390, height: 844 } });
  portal.errors = [];
  portal.on("pageerror", (error) => portal.errors.push(error.message));
  await portal.goto(base + link.path);
  await expect(portal.locator(".portal-position__facts")).toContainText("Vano");
  await portal.locator(".portal-position__facts").scrollIntoViewIfNeeded();
  await capture(portal, "portal-vano-producto-390", ".portal-position__facts");
  await portal.close();
  await request("estimator", `/projects/${state.project.id}/approve/`, {
    note: "Cliente aprobó revisión A; ensayo DEMO",
  });
  const page = await pageFor("estimator");
  await page.goto(base + `/projects/${state.project.id}`);
  await page.locator(".position-row").first().click();
  const panel = page.locator(".rectification-panel");
  await panel.locator(":scope > summary").click();
  await panel.getByLabel("Medir en tres puntos").uncheck();
  await panel.getByLabel("Ancho (mm)", { exact: true }).fill("1620");
  await panel.getByLabel("Alto (mm)", { exact: true }).fill("1220");
  await panel.getByText("Avanzado · escuadra y fijación manual", { exact: true }).click();
  await panel.getByLabel("Fijar fabricación manualmente").uncheck();
  await panel
    .getByLabel("Antecedente de la rectificación")
    .fill("Medidor verificó la fachada después de aprobación; ensayo DEMO");
  await panel.getByRole("button", { name: "Revisar rectificación y precio" }).click();
  await expect(
    panel.getByRole("button", { name: "Aplicar rectificación y abrir revisión" }),
  ).toBeVisible();
  await expect(panel).toContainText("Venta neta del proyecto");
  await panel
    .getByRole("button", { name: "Aplicar rectificación y abrir revisión" })
    .scrollIntoViewIfNeeded();
  await capture(page, "rectificacion-aprobada-diff-precio", ".rectification-panel");
  await panel.getByRole("button", { name: "Aplicar rectificación y abrir revisión" }).click();
  await expect(page.locator(".measurement-panel")).toContainText(
    "Rectificada en obra · falta confirmar",
  );
  state.project = await request("estimator", `/projects/${state.project.id}/`);
  state.position = await request("estimator", `/positions/${state.position.id}/`);
  expect(state.project.current_revision).toBe("REV-B");
  expect(state.position.design.nominal_width_mm).toBe("1600.00");
  expect(state.position.measurements.price_change.delta_net).not.toBe("0");
  await page.reload();
  await page.locator(".position-row").first().click();
  const measures = page.locator(".measurement-panel");
  await expect(measures).toContainText("Rectificación: venta neta");
  await measures
    .getByLabel("Responsabilidad de la confirmación")
    .fill("Técnico volvió a confirmar medidas rectificadas para fabricación DEMO");
  await measures.getByRole("button", { name: "Confirmar medidas para producción" }).click();
  await expect(measures).toContainText("Confirmada para producción");
  await measures.scrollIntoViewIfNeeded();
  await capture(page, "reapertura-delta-y-confirmacion", ".measurement-panel");
  const versionB = await seal(state.project.id);
  expect(versionB.production_allowed).toBe(true);
  await artifact(versionB, "DOC-01", "cotizacion-revision-b.pdf");
  const released = await request(
    "manager",
    `/production/versions/${versionB.id}/release/`,
    {},
    "POST",
  );
  expect(released.orders.length).toBeGreaterThan(0);
  await artifact(versionB, "DOC-03", "taller-fabricacion.pdf");
  const order = await request("manager", `/production/orders/${released.orders[0].id}/`);
  expect(Number(order.making.width_mm)).toBe(1600);
  expect(Number(order.making.height_mm)).toBe(1200);
  const restored = await request(
    "estimator",
    `/documents/artifacts/${artifactA}/access/`,
    {},
    "POST",
  );
  const originalBytes = Buffer.from(await (await fetch(restored.signed_url)).arrayBuffer());
  expect(originalBytes.equals(await fs.readFile(out + "/cotizacion-revision-a.pdf"))).toBe(true);
  // An independent quote with pending measurements is sellable but cannot release an OT.
  const pending = await request("estimator", "/projects/", {
    name: "D07 · gate medidas pendientes DEMO",
    client_name: "Ensayo",
    delivery_address: "Valdivia",
  });
  const pendingRules = await request("estimator", `/organization/mounting/${state.system}/`);
  await request("estimator", `/projects/${pending.id}/positions/`, {
    location_tag: "Fachada pendiente · DEMO",
    quantity: 1,
    design: state.position.design,
    measurements: state.position.measurements.measurements.map((item) => ({
      ...item.survey,
      rule_revision: pendingRules.items.find((rule) => rule.rule.code === item.survey.rule_code)
        .revision,
      origin: "CUSTOMER",
    })),
  });
  const pendingVersion = await seal(pending.id);
  expect(pendingVersion.production_allowed).toBe(false);
  const manager = await auth("manager");
  const refused = await fetch(api + `/production/versions/${pendingVersion.id}/release/`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + manager.access_token,
      "X-Organization-ID": org,
      "Content-Type": "application/json",
    },
    body: "{}",
  });
  expect(refused.status).toBe(422);
  expect((await refused.json()).error.code).toBe("production_measurements_unconfirmed");
  await fs.writeFile(
    out + "/flujo-medidas-revision-ot.json",
    JSON.stringify(
      {
        versionA: versionA.id,
        versionB: versionB.id,
        unchangedPdf: true,
        revision: "REV-B",
        price_change: state.position.measurements.price_change,
        confirmedRelease: released.orders.map((item) => ({ id: item.id, code: item.order_code })),
        pendingGate: "production_measurements_unconfirmed",
        fabrication: { width_mm: order.making.width_mm, height_mm: order.making.height_mm },
      },
      null,
      2,
    ),
  );
  await fs.writeFile(".run/d07-chain-state.json", JSON.stringify({ ...state, versionA, versionB }));
  await page.context().close();
  console.log(
    "PASA autoridad, rectificación después de aprobación, delta, nueva confirmación, PDF inmutable y gate/OT",
  );
}

await fs.mkdir(out, { recursive: true });
try {
  if (process.env.DEKOPEN_D07_MATRIX_ONLY === "1") {
    await verifyMatrix(JSON.parse(await fs.readFile(".run/d07-ui-state.json", "utf8")));
  } else if (process.env.DEKOPEN_D07_CHAIN_ONLY === "1") {
    await verifyChain(JSON.parse(await fs.readFile(".run/d07-ui-state.json", "utf8")));
  } else {
    const prior = JSON.parse(await fs.readFile(".run/d06-editable-state.json", "utf8"));
    const source = await request("estimator", `/positions/${prior.position.id}/`);
    const system = source.design.system_id;
    const ruleCases = JSON.parse(await fs.readFile("engine/tests/golden_mounting.json", "utf8"));
    const names = {
      IN_OPENING: "En vano con holgura",
      SUBFRAME: "Con premarco",
      OVERLAP: "Sobre vano o traslapado",
      RENOVATION: "Renovación sobre marco existente",
    };
    const revisions = {};
    for (const [code, entry] of Object.entries(ruleCases)) {
      const before = await request("owner", `/organization/mounting/${system}/`);
      const current = before.items.find((item) => item.rule.code === code);
      const saved = await request(
        "owner",
        `/organization/mounting/${system}/`,
        {
          rule: { ...entry.rule, name: names[code] },
          expected_revision: current?.revision ?? 0,
          reason: "Ensayo D07 local, reglas sintéticas sin certificación",
        },
        "PUT",
      );
      revisions[code] = saved.items.find((item) => item.rule.code === code).revision;
    }
    const survey = {
      ...ruleCases.IN_OPENING.survey,
      module_id: null,
      rule_revision: revisions.IN_OPENING,
      widths_mm: ["1520"],
      heights_mm: ["1220"],
      origin: "CUSTOMER",
    };
    const design = {
      ...source.design,
      parametric_tree: { ...source.design.parametric_tree, extras: [] },
    };
    const proposal = await request("estimator", "/projects/mounting-preview/", {
      design,
      measurements: [survey],
    });
    expect(proposal.design.nominal_width_mm).toBe("1500");
    expect(proposal.design.nominal_height_mm).toBe("1200");
    const project = await request("estimator", "/projects/", {
      name: "D07 · vano y fabricación DEMO",
      client_name: "Cliente de ensayo",
      client_email: "d07@example.test",
      delivery_address: "Valdivia",
    });
    let position = await request("estimator", `/projects/${project.id}/positions/`, {
      location_tag: "Fachada · DEMO",
      quantity: 1,
      design: proposal.design,
      measurements: [survey],
    });
    expect(position.measurements.state).toBe("CUSTOMER");
    expect(position.measurements.current).toBe(true);
    const page = await pageFor("estimator");
    await page.goto(base + `/projects/${project.id}/positions/${position.id}/edit`);
    const inspector = page.locator(".mounting-inspector");
    await expect(inspector.getByText("Vano y montaje", { exact: true })).toBeVisible();
    await expect(inspector.locator(".mounting-chip")).toContainText("1 520");
    await inspector.getByLabel("Medir en tres puntos").check();
    for (const [name, value] of [
      ["Ancho · Arriba (mm)", "1524"],
      ["Ancho · Centro (mm)", "1520"],
      ["Ancho · Abajo (mm)", "1522"],
      ["Alto · Izquierda (mm)", "1220"],
      ["Alto · Centro (mm)", "1221"],
      ["Alto · Derecha (mm)", "1222"],
    ])
      await inspector.getByLabel(name, { exact: true }).fill(value);
    await inspector.getByLabel("Tipo de muro").selectOption("");
    await inspector.getByRole("button", { name: "Calcular fabricación", exact: true }).click();
    await expect(inspector.getByRole("alert")).toContainText("Elige el tipo de muro");
    await expect(
      inspector.getByRole("button", { name: "Aplicar fabricación", exact: true }),
    ).toHaveCount(0);
    await inspector.getByLabel("Tipo de muro").selectOption("CONCRETE");
    await inspector.getByRole("button", { name: "Calcular fabricación", exact: true }).click();
    await expect(
      inspector.getByRole("button", { name: "Aplicar fabricación", exact: true }),
    ).toBeVisible();
    await expect(inspector).toContainText("dispersión supera la tolerancia");
    await inspector.getByRole("button", { name: "Aplicar fabricación", exact: true }).click();
    await expect(page.locator(".mounting-dimensions")).toBeVisible();
    await inspector.scrollIntoViewIfNeeded();
    await capture(page, "minimo-tres-puntos", ".mounting-inspector");
    await page.getByRole("button", { name: "Deshacer", exact: true }).click();
    await expect(inspector.getByLabel("Medir en tres puntos")).not.toBeChecked();
    await page.getByRole("button", { name: "Rehacer", exact: true }).click();
    await expect(inspector.getByLabel("Medir en tres puntos")).toBeChecked();
    await page.getByRole("button", { name: "Guardar", exact: true }).click();
    await expect(page.getByText("Guardado", { exact: true }).first()).toBeVisible();
    position = await request("estimator", `/positions/${position.id}/`);
    expect(position.measurements.measurements[0].result.width.spread_mm).toBe("4");
    await page.reload();
    await expect(page.locator(".mounting-dimensions")).toBeVisible();
    const advanced = inspector
      .locator("details")
      .filter({ has: page.getByText("Avanzado · escuadra y fijación manual", { exact: true }) });
    await advanced.locator("summary").click();
    await inspector.getByLabel("Fijar fabricación manualmente").check();
    await inspector.getByLabel("Fabricación · ancho (mm)", { exact: true }).fill("1510");
    await inspector.getByLabel("Fabricación · alto (mm)", { exact: true }).fill("1200");
    await inspector
      .getByLabel("Motivo de la fijación")
      .fill("Técnico solicita fijación manual de ensayo");
    await inspector.getByRole("button", { name: "Calcular fabricación", exact: true }).click();
    await expect(inspector).toContainText("fijación manual no es coherente");
    await capture(page, "fijacion-incoherente", ".mounting-inspector");
    await inspector.getByRole("button", { name: "Aplicar fabricación", exact: true }).click();
    await page.getByRole("button", { name: "Guardar", exact: true }).click();
    await expect(page.getByText("Guardado", { exact: true }).first()).toBeVisible();
    position = await request("estimator", `/positions/${position.id}/`);
    expect(position.design.nominal_width_mm).toBe("1510.00");
    const details = page.locator(".position-measurements");
    await details.locator("summary").click();
    await details
      .getByLabel("Responsabilidad de la confirmación")
      .fill("Estimador verificó antecedentes; avisos reconocidos en ensayo DEMO");
    await details.getByLabel("Revisé los avisos de dispersión y fijación").check();
    await details.getByRole("button", { name: "Confirmar medidas para producción" }).click();
    await expect(details).toContainText("Confirmada para producción");
    await capture(page, "confirmacion-explicita", ".measurement-panel");
    position = await request("estimator", `/positions/${position.id}/`);
    expect(position.measurements.state).toBe("CONFIRMED");
    await fs.writeFile(
      ".run/d07-ui-state.json",
      JSON.stringify({ project, position, system, revisions }),
    );
    console.log(
      "PASA D07 mínimo, dispersión, fijación, deshacer/rehacer, guardado/reapertura y confirmación",
    );
  }
} catch (error) {
  if (lastPage && !lastPage.isClosed()) await lastPage.screenshot({ path: out + "/fallo.png" });
  throw error;
} finally {
  const mode =
    process.env.DEKOPEN_D07_MATRIX_ONLY === "1"
      ? "matriz"
      : process.env.DEKOPEN_D07_CHAIN_ONLY === "1"
        ? "cadena"
        : "editor";
  await fs.writeFile(out + `/navegador-${mode}.json`, JSON.stringify(records, null, 2));
  if (factor) {
    const a = sessions.get("owner");
    await fetch(supa + `/auth/v1/factors/${factor.id}`, {
      method: "DELETE",
      headers: { apikey: anon, Authorization: "Bearer " + a.access_token },
    });
  }
  await browser.close();
}

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
  new URL("../../docs/redesign/captures/accesorios-extras/recorrido", import.meta.url),
);
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("D06 verification requires the owned local Supabase stack.");
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
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d06-" + Date.now() }),
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
      ".extra-inspector *, .project-services *, .extra-policy *, .extra-authority-row *, .extra-price-lines *",
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

function service(code, name, basis, cost, selling, extra = {}) {
  return {
    code,
    name,
    scope: "PROJECT",
    kind: "SERVICE",
    basis,
    unit: { AREA: "M2", PERIMETER: "M" }[basis] ?? "EA",
    currency: "CLP",
    cost_rate: cost,
    selling_rate: selling,
    source: "Tarifas sintéticas de ensayo D06; sin certificación",
    synthetic: true,
    ...extra,
  };
}
async function setup() {
  const systems = await request("manager", "/catalogs/systems/");
  const system = systems.items.find((s) => s.code === "DEMO_60" && s.version === 6);
  if (!system) throw new Error("D06 catalog v6 missing");
  const options = await request("estimator", `/projects/design-options/${system.id}/`);
  const glass = options.glass_specs.find(
    (g) => g.article_sku?.endsWith("-GLASS-SAFE") || g.sku?.endsWith("-GLASS-SAFE"),
  );
  if (!glass)
    throw new Error(
      "D06 glass fields " + JSON.stringify(options.glass_specs.map((g) => Object.keys(g))),
    );
  const before = await request("owner", "/organization/extras/");
  const policy = {
    schema_version: 1,
    services: [
      service("INSTALL", "Instalación estándar", "PERIMETER", "1000", "1500", {
        installation: true,
      }),
      service("INSTALL_AREA", "Instalación por superficie", "AREA", "5000", "7500", {
        installation: true,
      }),
      service("INSTALL_POSITION", "Instalación por posición", "PER_POSITION", "20000", "30000", {
        installation: true,
      }),
      service("SEAL", "Sellado y espuma", "PERIMETER", "600", "900"),
      service("REMOVAL", "Retiro de ventana existente", "PER_POSITION", "8000", "12000"),
      service("SCAFFOLD", "Andamio", "FIXED", "40000", "60000"),
      service("FREIGHT_FIXED", "Flete fijo", "FIXED", "10000", "15000"),
      service("FREIGHT", "Flete por zona", "ZONE", "0", "0", {
        zones: {
          "Valdivia urbana": { cost_rate: "15000", selling_rate: "22500" },
          "Valdivia rural": { cost_rate: "25000", selling_rate: "37500" },
        },
      }),
    ],
    position_defaults: [],
    document_prices: "ITEMIZED",
  };
  await fs.writeFile(".run/d06-demo-policy.json", JSON.stringify(policy));
  await request(
    "owner",
    "/organization/extras/",
    {
      policy,
      expected_revision: before.revision,
      reason: "Ensayo integral D06 con tarifas sintéticas",
    },
    "PUT",
  );
  const project = await request("estimator", "/projects/", {
    name: "D06 · fachada con accesorios DEMO",
    client_name: "Cliente de ensayo",
    client_email: "d06@example.test",
    delivery_address: "Valdivia",
  });
  const reference = { id: "vano", type: "BAY", opening_type: "FIXED" };
  const design = {
    system_id: system.id,
    nominal_width_mm: "1500",
    nominal_height_mm: "1400",
    color: "WHITE",
    parametric_tree: {
      ...reference,
      id: "vano",
      opening_type: "FIXED",
      glass_product: glass.product ?? glass.glass_product ?? reference.glass_product,
      glass_article_sku: glass.article_sku ?? glass.sku,
    },
  };
  const position = await request("estimator", `/projects/${project.id}/positions/`, {
    location_tag: "Fachada norte · DEMO",
    quantity: 2,
    design,
  });
  const state = { project, position, system, policy };
  await fs.writeFile(".run/d06-ui-state.json", JSON.stringify(state));
  console.log("PASA D06 · fixture con catálogo v6 y servicios con fuente");
  return state;
}
async function verifyEditor(state) {
  const p = await pageFor("estimator");
  await p.goto(base + `/projects/${state.project.id}/positions/${state.position.id}/edit`, {
    waitUntil: "networkidle",
  });
  const inspector = p.locator(".extra-inspector");
  while (await inspector.getByRole("button", { name: "Quitar", exact: true }).count()) {
    await inspector.getByRole("button", { name: "Quitar", exact: true }).first().click();
    await p.waitForLoadState("networkidle");
  }
  await expect(inspector).toContainText("La posición contiene una ventana");
  const proposal = inspector.locator(".extra-proposal").filter({ hasText: "Vierteaguas" });
  await proposal.getByRole("button", { name: "Descartar", exact: true }).click();
  await expect(inspector).toContainText("Descartado.");
  await p.getByRole("button", { name: "Deshacer", exact: true }).first().click();
  await expect(proposal).toBeVisible();
  await proposal.getByRole("button", { name: "Aceptar", exact: true }).click();
  await expect(inspector.locator(".extra-equation")).toContainText("1,56 m");
  for (const code of ["FRAME_EXTENSION", "SCREEN_FIXED"]) {
    await inspector.getByRole("combobox", { name: "Extra compatible" }).selectOption(code);
    await inspector.getByRole("button", { name: "Agregar", exact: true }).click();
    await p.waitForLoadState("networkidle");
  }
  const extension = inspector.locator(".extra-selected > li").filter({ hasText: "Ensanche" });
  await extension.getByRole("checkbox", { name: "Superior", exact: true }).check();
  await expect(extension.locator(".extra-equation")).toContainText("4,3 m");
  await p.getByRole("button", { name: "Deshacer", exact: true }).first().click();
  await expect(
    extension.getByRole("checkbox", { name: "Superior", exact: true }),
  ).not.toBeChecked();
  await expect(extension.locator(".extra-equation")).toContainText("2,8 m");
  await inspector.scrollIntoViewIfNeeded();
  await capture(p, "inspector-cantidades-sugerencia-aceptada", ".extra-inspector");
  const [saved] = await Promise.all([
    p.waitForResponse(
      (r) => r.url().includes(`/positions/${state.position.id}/`) && r.request().method() === "PUT",
    ),
    p.getByRole("button", { name: "Guardar", exact: true }).click(),
  ]);
  if (!saved.ok())
    throw new Error("D06 save " + saved.status() + " " + JSON.stringify(await saved.json()));
  await p.reload({ waitUntil: "networkidle" });
  await expect(inspector).toContainText("1,56 m");
  state.position = await request("estimator", `/positions/${state.position.id}/`);
  await fs.writeFile(".run/d06-ui-state.json", JSON.stringify(state));
  await capture(p, "inspector-guardado-reabierto", ".extra-inspector");
  await p.context().close();
}
async function verifyServices(state) {
  const p = await pageFor("estimator");
  await p.goto(base + `/projects/${state.project.id}`, { waitUntil: "networkidle" });
  const panel = p.getByRole("region", { name: "Servicios del proyecto" });
  await panel.getByRole("checkbox", { name: "Instalación estándar · DEMO", exact: true }).check();
  await panel.getByRole("checkbox", { name: "Sellado y espuma · DEMO", exact: true }).check();
  await panel.getByRole("checkbox", { name: "Flete por zona · DEMO", exact: true }).check();
  await panel.getByRole("combobox", { name: "Zona", exact: true }).selectOption("Valdivia urbana");
  await panel.getByRole("button", { name: "Guardar servicios", exact: true }).click();
  await expect(panel).toContainText("11,6 m");
  await expect(panel).toContainText("$17.400");
  await panel.getByRole("button", { name: "Deshacer", exact: true }).click();
  await expect(
    panel.getByRole("checkbox", { name: "Instalación estándar · DEMO", exact: true }),
  ).not.toBeChecked();
  await panel.getByRole("button", { name: "Deshacer", exact: true }).click();
  await expect(panel).toContainText("$17.400");
  await panel.scrollIntoViewIfNeeded();
  await capture(p, "servicios-perimetro-flete-deshacer", ".project-services");
  await p.context().close();
}
async function verifyPolicy(state) {
  const p = await pageFor("owner");
  await p.goto(base + "/settings/general", { waitUntil: "networkidle" });
  const panel = p.getByRole("region", { name: "Extras y servicios" });
  await panel
    .getByRole("combobox", { name: "Precios de extras en la cotización", exact: true })
    .selectOption("GROUPED");
  await panel
    .getByRole("textbox", { name: "Motivo del cambio", exact: true })
    .fill("Ensayo D06: propuesta revisada de precios agrupados");
  await panel.getByRole("button", { name: "Revisar cambios de plantilla", exact: true }).click();
  await panel
    .getByRole("button", { name: "Guardar plantilla revisada", exact: true })
    .scrollIntoViewIfNeeded();
  await capture(p, "ajustes-diff-politica", ".extra-policy");
  await panel.getByRole("button", { name: "Guardar plantilla revisada", exact: true }).click();
  await expect(
    panel.getByRole("combobox", { name: "Precios de extras en la cotización", exact: true }),
  ).toHaveValue("GROUPED");
  await panel.getByRole("button", { name: "Deshacer último cambio", exact: true }).click();
  await expect(
    panel.getByRole("combobox", { name: "Precios de extras en la cotización", exact: true }),
  ).toHaveValue("ITEMIZED");
  await capture(p, "ajustes-politica-deshacer", ".extra-policy");
  await p.context().close();
}
async function verifyMore(state) {
  const route = `/projects/${state.project.id}/positions/${state.position.id}/edit`;
  for (const mode of ["loading", "error"]) {
    const p = await pageFor("estimator");
    let release;
    await p.route("**/api/v1/projects/extras-preview/", async (r) => {
      if (mode === "loading") {
        await new Promise((resolve) => {
          release = resolve;
        });
        return r.continue();
      }
      return r.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: { code: "fixture", detail: "La fuente de ensayo no está disponible. Reintenta." },
        }),
      });
    });
    await p.goto(base + route, { waitUntil: "domcontentloaded" });
    const panel = p.locator(".extra-inspector");
    await expect(panel).toContainText(
      mode === "loading" ? "Calculando cantidades y precio" : "no está disponible",
      { timeout: 20000 },
    );
    await panel.scrollIntoViewIfNeeded();
    if (mode === "loading") {
      await p.screenshot({ path: out + "/estado-carga.png" });
      const resumed = p.waitForResponse(
        (r) => r.url().includes("/projects/extras-preview/") && r.ok(),
      );
      release();
      await resumed;
      await p.waitForLoadState("networkidle");
      await p.unroute("**/api/v1/projects/extras-preview/");
    } else {
      await capture(p, "estado-error", ".extra-inspector");
      await p.unroute("**/api/v1/projects/extras-preview/");
      await panel.getByRole("button", { name: "Reintentar", exact: true }).click();
      await expect(panel).toContainText("1,56 m");
      await capture(p, "estado-reintento", ".extra-inspector");
    }
    await p.context().close();
  }
  const manager = await pageFor("manager");
  await manager.goto(base + `/projects/${state.project.id}`, { waitUntil: "networkidle" });
  await expect(manager.locator(".project-services")).toContainText("Tu rol permite consultar");
  await expect(manager.locator(".project-services input[type=checkbox]").first()).toBeDisabled();
  await manager.locator(".project-services").scrollIntoViewIfNeeded();
  await capture(manager, "estado-solo-consulta", ".project-services");
  await manager.context().close();
  const denied = await pageFor("operator");
  await denied.goto(base + route, { waitUntil: "networkidle" });
  await expect(denied.locator("body")).toContainText("Sin acceso");
  await capture(denied, "estado-operario-sin-acceso");
  await denied.context().close();
  const settings = await pageFor("owner");
  await settings.goto(base + "/settings/general", { waitUntil: "networkidle" });
  const policy = settings.getByRole("region", { name: "Extras y servicios" });
  await policy.getByText("Importar desde una fuente · JSON", { exact: true }).click();
  const before = await request("owner", "/organization/extras/");
  const proposed = { ...before.policy, document_prices: "GROUPED" };
  await policy
    .getByRole("textbox", { name: "Contenido de la fuente", exact: true })
    .fill(JSON.stringify(proposed));
  await policy.getByRole("button", { name: "Revisar importación", exact: true }).click();
  await expect(policy).toContainText("Revisión de cambios");
  await policy
    .getByRole("button", { name: "Incorporar propuesta revisada", exact: true })
    .scrollIntoViewIfNeeded();
  await capture(settings, "ajustes-importacion-diff", ".extra-import");
  await policy.getByRole("button", { name: "Descartar propuesta", exact: true }).click();
  await expect(
    policy.getByRole("combobox", { name: "Precios de extras en la cotización", exact: true }),
  ).toHaveValue("ITEMIZED");
  await settings.context().close();
  const catalog = await pageFor("manager");
  await catalog.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
  await catalog.getByRole("button", { name: "Crear serie", exact: true }).click();
  const authority = catalog.getByRole("group", { name: "Accesorios y extras con autoridad" });
  await expect(authority).toContainText("Sin autoridad de extras");
  await authority.scrollIntoViewIfNeeded();
  await capture(
    catalog,
    "catalogo-estado-vacio",
    'fieldset.catalog-group:has(legend:text-is("Accesorios y extras con autoridad"))',
  );
  await authority
    .getByRole("button", { name: "Declarar accesorios desde una fuente", exact: true })
    .click();
  await authority.getByRole("button", { name: "Agregar definición de extra", exact: true }).click();
  await authority.locator(".extra-authority-row > summary").click();
  await expect(authority).toContainText("Extra sin nombre");
  await capture(
    catalog,
    "catalogo-edicion-con-fuente",
    'fieldset.catalog-group:has(legend:text-is("Accesorios y extras con autoridad"))',
  );
  await catalog.context().close();
  console.log("PASA D06 · cinco estados, roles reales y revisión de importación");
}

async function verifyChain(state) {
  const current = await request("estimator", `/projects/${state.project.id}/`);
  let priced;
  const p = await pageFor("estimator");
  if (current.current_pricing_operation_id) {
    const history = await request("estimator", "/pricing/operations/");
    priced = history.find(
      (item) => item.id === current.current_pricing_operation_id && item.state === "APPLIED",
    );
    if (!priced) throw new Error("Applied operation missing");
  } else {
    const prepared = await request("estimator", `/documents/projects/${state.project.id}/inputs/`);
    const positions = prepared.positions.map((pos) => {
      const annotations = new Map();
      for (const row of pos.workshop_suggestions) {
        const key = JSON.stringify([row.bay_id, row.leaf_id]);
        annotations.set(key, {
          ...(annotations.get(key) ?? {}),
          ...Object.fromEntries(Object.entries(row).filter(([, v]) => v != null)),
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
      `/documents/projects/${state.project.id}/inputs/`,
      {
        payment_terms: "Anticipo 50 %, saldo al entregar",
        quotation_valid_until: "2026-11-06",
        positions,
      },
      "PUT",
    );
    await p.goto(base + `/projects/${state.project.id}/pricing`, { waitUntil: "networkidle" });
    await p.locator("input[name=reason]").fill("D06 · revisar accesorios y servicios de fachada");
    await p.locator("input[name=effective_date]").fill("2026-10-06");
    const [response] = await Promise.all([
      p.waitForResponse(
        (r) => r.url().endsWith("/pricing/preview/") && r.request().method() === "POST",
      ),
      p.getByRole("button", { name: "Calcular y revisar", exact: true }).click(),
    ]);
    if (!response.ok())
      throw new Error("Price " + response.status() + " " + JSON.stringify(await response.json()));
    priced = await response.json();
    await expect(p.locator(".extra-price-lines")).toHaveCount(2);
    await expect(p.locator(".operation-decision")).toContainText("Instalación estándar");
    await p.locator(".operation-decision").scrollIntoViewIfNeeded();
    await capture(p, "precio-sublines-servicios", ".extra-price-lines");
    await p.getByRole("button", { name: "Aprobar y aplicar precios", exact: true }).click();
    await expect(p.locator(".operation-decision")).toContainText("Precios aplicados al proyecto.");
  }
  const frozen = await request("estimator", `/documents/projects/${state.project.id}/freeze/`, {
    pricing_operation_id: priced.id,
    confirmed: true,
  });
  if (!frozen.production_allowed || !frozen.documentary_complete)
    throw new Error("Revision not production ready");
  const artifact = await request("estimator", "/documents/artifacts/", {
    document_type: "DOC-01",
    format: "PDF",
    project_version_id: frozen.id,
  });
  const access = await request(
    "estimator",
    `/documents/artifacts/${artifact.id}/access/`,
    {},
    "POST",
  );
  const pdf = await fetch(access.signed_url);
  if (!pdf.ok) throw new Error("PDF download failed");
  await fs.writeFile(out + "/cotizacion-extras.pdf", Buffer.from(await pdf.arrayBuffer()));
  const released = await request(
    "manager",
    `/production/versions/${frozen.id}/release/`,
    {},
    "POST",
  );
  const plans = [];
  for (const order of released.orders) {
    const plan = await request("manager", `/production/orders/${order.id}/optimize/`, {
      color: "WHITE",
      strategy: "fast",
    });
    if (!JSON.stringify(plan).includes("EXTRA-FRAME_EXTENSION"))
      throw new Error("Extension missing from cut plan");
    plans.push({ order: order.order_code, id: order.id, plan });
  }
  await fs.writeFile(
    out + "/flujo-sellado-ot-corte.json",
    JSON.stringify({ priced, frozen, artifact, orders: plans }, null, 2),
  );
  state.sealed = { priced_id: priced.id, version_id: frozen.id };
  await fs.writeFile(".run/d06-ui-state.json", JSON.stringify(state));
  await p.goto(base + `/projects/${state.project.id}`, { waitUntil: "networkidle" });
  await expect(p.locator(".project-services")).toContainText("Servicios de la revisión cerrada");
  await p.locator(".project-services").scrollIntoViewIfNeeded();
  await capture(p, "estado-revision-cerrada", ".project-services");
  await p.context().close();
  console.log("PASA D06 · precio aplicado, PDF sellado, OT y ensanche cortable");
}

async function verifyPrivacy(state) {
  const project = await request("estimator", `/projects/${state.project.id}/`);
  const operationId = project.current_pricing_operation_id;
  if (!operationId) throw new Error("D06 pricing evidence must be applied first");
  for (const role of ["estimator", "owner"]) {
    const operations = (await request(role, "/pricing/operations/")).filter(
      (item) => item.project_id === project.id,
    );
    const index = operations.findIndex((item) => item.id === operationId);
    if (index < 0) throw new Error("D06 operation unavailable for role");
    const authority = operations[index];
    if (role === "estimator") {
      expect(authority.costs_visible).toBe(false);
      expect(authority.total_cost).toBeNull();
      expect(authority.cost_lines).toEqual([]);
      expect(authority.positions_breakdown).toEqual([]);
      expect(authority.authorities).toEqual([]);
      expect(authority.services_cost).toBeUndefined();
      for (const item of authority.services) {
        expect(item.cost_rate).toBeUndefined();
        expect(item.total_cost).toBeUndefined();
      }
    } else {
      expect(authority.costs_visible).toBe(true);
      expect(authority.total_cost).not.toBeNull();
      expect(authority.services[0].cost_rate).toBeDefined();
    }
    for (const size of [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 1024, height: 768 },
    ]) {
      for (const theme of ["light", "dark"]) {
        const p = await pageFor(role, theme, size);
        await p.goto(base + `/projects/${project.id}/pricing`, { waitUntil: "networkidle" });
        await p.getByRole("button", { name: "Recargar", exact: true }).click();
        const review = p.getByRole("button", { name: "Revisar operación", exact: true });
        await expect(review).toHaveCount(operations.length);
        await review.nth(index).click();
        const decision = p.locator(".operation-decision");
        await expect(decision).toContainText("Instalación estándar");
        if (role === "estimator") {
          await expect(decision).toContainText("Los costos de compra son confidenciales");
          await expect(decision.locator("dt").filter({ hasText: "Costo total" })).toHaveCount(0);
          await expect(decision.locator("th").filter({ hasText: "Costo" })).toHaveCount(0);
        } else {
          await expect(decision).toContainText("Costo total");
        }
        await decision.locator(".extra-price-lines").last().scrollIntoViewIfNeeded();
        await capture(p, `privacidad-${role}-${size.width}-${theme}`, ".extra-price-lines");
        await p.context().close();
      }
    }
  }
  console.log("PASA D06 · precios de venta por rol y autoridad de costos conservada");
}
async function verifyCatalogPrivacy(state) {
  const systemId = state.position.design.system_id;
  for (const role of ["estimator", "manager"]) {
    const system = await request(role, `/catalogs/systems/${systemId}/`);
    const workspace = await request(role, `/catalogs/systems/${systemId}/workspace/`);
    const full = role === "manager";
    for (const authority of [system.extra_authority, workspace.system.extra_authority]) {
      expect(JSON.stringify(authority).includes('"cost_rate"')).toBe(full);
      expect(authority.definitions.find((item) => item.code === "SILL").selling_rate).toBeDefined();
    }
    for (const size of [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 1024, height: 768 },
    ]) {
      for (const theme of ["light", "dark"]) {
        const p = await pageFor(role, theme, size);
        await p.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
        await p.locator(".catalog-system").filter({ hasText: system.name }).first().click();
        await p.getByRole("tab", { name: "Ficha de serie", exact: true }).click();
        await p.getByRole("button", { name: `Consultar ${system.name}`, exact: true }).click();
        const authority = p.getByRole("group", { name: "Accesorios y extras con autoridad" });
        const sill = authority
          .locator(".extra-authority-row")
          .filter({ hasText: "Vierteaguas" })
          .first();
        await sill.locator(":scope > summary").click();
        await expect(sill.getByLabel("Tarifa de venta por unidad")).not.toHaveValue("");
        await expect(sill.getByLabel("Costo unitario de suministro completo")).toHaveCount(
          full ? 1 : 0,
        );
        if (!full) await expect(authority).toContainText("Los costos de compra son confidenciales");
        await sill.scrollIntoViewIfNeeded();
        await capture(
          p,
          `catalogo-privacidad-${role}-${size.width}-${theme}`,
          ".extra-authority-row",
        );
        await p.context().close();
      }
    }
  }
  console.log("PASA D06 · catálogo público sin costos y autoridad privada por organización");
}
async function verifyPdfPolicies(state) {
  const original = await request("owner", "/organization/extras/");
  const cases = [];
  try {
    for (const policy of ["ITEMIZED", "GROUPED"]) {
      const latest = await request("owner", "/organization/extras/");
      await request(
        "owner",
        "/organization/extras/",
        {
          policy: { ...original.policy, document_prices: policy },
          expected_revision: latest.revision,
          reason: "D06 · verificar PDF " + policy,
        },
        "PUT",
      );
      const source = await request("estimator", `/projects/${state.project.id}/`);
      const clone = await request("estimator", `/projects/${state.project.id}/clone/`, {
        expected_updated_at: source.updated_at,
      });
      const project = await request("estimator", `/projects/${clone.id}/`);
      const copy = { ...state, project, position: project.positions[0] };
      await verifyChain(copy);
      await fs.copyFile(
        out + "/cotizacion-extras.pdf",
        out + "/cotizacion-extras-" + policy.toLowerCase() + ".pdf",
      );
      cases.push({ policy, project_id: clone.id, ...copy.sealed });
    }
    await fs.writeFile(out + "/politicas-pdf.json", JSON.stringify(cases, null, 2));
  } finally {
    const latest = await request("owner", "/organization/extras/");
    await request(
      "owner",
      "/organization/extras/",
      {
        policy: original.policy,
        expected_revision: latest.revision,
        reason: "D06 · conservar plantilla anterior después del ensayo",
      },
      "PUT",
    );
    await fs.writeFile(".run/d06-ui-state.json", JSON.stringify(state));
  }
  console.log("PASA D06 · PDF por sublíneas y agrupado, ambas revisiones inmutables");
}
async function verifyPublication(state) {
  const p = await pageFor("manager");
  await p.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
  const original = await request(
    "manager",
    `/catalogs/systems/${state.position.design.system_id}/`,
  );
  const schema = await request("manager", "/catalog-imports/schema/");
  const columns = schema.sheets.find((s) => s.name === "Sistemas").columns;
  const code = "REVISION-D06-" + Date.now().toString(36).toUpperCase();
  const sourceName = `extras-${Date.now().toString(36)}.csv`;
  const values = {
    ...original,
    system_code: code,
    name: "Accesorios revisados · DEMO",
    version: 1,
    source: "Ensayo D06 · accesorios sintéticos sin certificación",
    opening_capabilities: [],
    paired_leaf_rule: null,
  };
  const cell = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const row = columns
    .map((c) => {
      const v = c.key.startsWith("sliding.") ? original.sliding?.[c.key.slice(8)] : values[c.key];
      return cell(
        c.kind === "json" && v != null ? JSON.stringify(v) : Array.isArray(v) ? v.join("|") : v,
      );
    })
    .join(";");
  const csv =
    "\ufeffSistemas;DEKOPEN CATÁLOGO V1\n" +
    columns.map((c) => cell(c.label)).join(";") +
    "\n" +
    row +
    "\n";
  await p.getByRole("button", { name: "Importar catálogo", exact: true }).click();
  await p
    .locator("input[type=file]")
    .setInputFiles({ name: sourceName, mimeType: "text/csv", buffer: Buffer.from(csv) });
  const entry = p.locator(".catalog-import-entry").filter({ hasText: sourceName }).first();
  await expect(entry).toContainText("Requiere revisión", { timeout: 60000 });
  await entry.getByRole("button", { name: "Revisar fuente y cambios", exact: true }).click();
  const authority = p.getByRole("group", { name: "Accesorios y extras con autoridad" });
  const sill = authority
    .locator(".extra-authority-row")
    .filter({ has: p.locator("summary", { hasText: "Vierteaguas" }) })
    .first();
  await sill.locator("summary").first().click();
  await sill
    .getByRole("textbox", { name: "Nombre", exact: true })
    .fill("Vierteaguas revisado · DEMO");
  await p.getByRole("button", { name: "Comparar cambios", exact: true }).click();
  const publish = p.getByRole("button", { name: "Publicar catálogo revisado", exact: true });
  await expect(publish).toBeDisabled();
  await p.locator(".catalog-review-diff").scrollIntoViewIfNeeded();
  await capture(p, "catalogo-importacion-diff", ".catalog-import-review");
  await p.locator(".catalog-review-attestation input").check();
  await publish.click();
  await expect(entry).toContainText("Publicado", { timeout: 30000 });
  const catalog = await request("manager", "/catalogs/systems/");
  const published = catalog.items.find((s) => s.code === code);
  expect(published.extra_authority.definitions.find((e) => e.code === "SILL").name).toBe(
    "Vierteaguas revisado · DEMO",
  );
  expect(published.extra_authority.definitions.find((e) => e.code === "SILL").selling_rate).toBe(
    original.extra_authority.definitions.find((e) => e.code === "SILL").selling_rate,
  );
  await entry.getByRole("button", { name: "Deshacer publicación", exact: true }).click();
  await p
    .getByRole("dialog")
    .getByRole("button", { name: "Deshacer publicación", exact: true })
    .click();
  await expect(entry).toContainText("Publicación deshecha", { timeout: 30000 });
  const after = await request("manager", "/catalogs/systems/");
  expect(after.items.find((s) => s.id === published.id)?.is_active).toBe(false);
  expect(after.items.find((s) => s.id === original.id)?.extra_authority).toEqual(
    original.extra_authority,
  );
  await capture(p, "catalogo-publicacion-deshacer", ".catalog-ingest");
  await p.context().close();
  console.log("PASA D06 · importación de extras, edición, diff, publicación y deshacer reales");
}

try {
  await fs.mkdir(out, { recursive: true });
  const state = process.argv.includes("--setup")
    ? await setup()
    : JSON.parse(await fs.readFile(".run/d06-ui-state.json", "utf8"));
  if (process.argv.includes("--inspector")) {
    const editable = JSON.parse(await fs.readFile(".run/d06-editable-state.json", "utf8"));
    const p = await pageFor("estimator");
    await p.goto(base + `/projects/${editable.project.id}/positions/${editable.position.id}/edit`, {
      waitUntil: "networkidle",
    });
    const panel = p.locator(".extra-inspector");
    await expect(panel).toContainText("1,56 m");
    await panel.locator(".extra-equation").first().scrollIntoViewIfNeeded();
    await capture(p, "inspector-cantidad-visible", ".extra-inspector");
    await fs.writeFile(
      ".run/d06-inspector-layout.json",
      JSON.stringify(
        await panel.evaluate((e) => {
          const rows = [];
          while (e) {
            const r = e.getBoundingClientRect();
            const s = getComputedStyle(e);
            rows.push({
              cls: e.className,
              top: r.top,
              height: r.height,
              scrollTop: e.scrollTop,
              scrollHeight: e.scrollHeight,
              overflowY: s.overflowY,
            });
            e = e.parentElement;
          }
          return rows;
        }),
        null,
        2,
      ),
    );
    await p.context().close();
  } else if (process.argv.includes("--audit")) {
    const p = await pageFor("estimator", "light", { width: 390, height: 844 });
    await p.goto(
      base + `/projects/${state.project.id}${process.argv.includes("--pricing") ? "/pricing" : ""}`,
      { waitUntil: "networkidle" },
    );
    const spills = await p.evaluate(() =>
      [...document.querySelectorAll("body *")]
        .filter(
          (e) =>
            e.getBoundingClientRect().right > document.documentElement.clientWidth + 1 &&
            getComputedStyle(e).display !== "none",
        )
        .map((e) => ({
          tag: e.tagName,
          cls: e.className,
          text: e.textContent?.trim().slice(0, 100),
          right: e.getBoundingClientRect().right,
          width: e.getBoundingClientRect().width,
        }))
        .slice(0, 25),
    );
    await fs.writeFile(".run/d06-overflow.json", JSON.stringify(spills, null, 2));
    await p.context().close();
  } else if (process.argv.includes("--editable")) {
    const source = await request("estimator", `/projects/${state.project.id}/`);
    const copy = await request("estimator", `/projects/${state.project.id}/clone/`, {
      expected_updated_at: source.updated_at,
    });
    const project = await request("estimator", `/projects/${copy.id}/`);
    await fs.writeFile(
      ".run/d06-editable-state.json",
      JSON.stringify({ ...state, project, position: project.positions[0] }),
    );
    console.log("PASA D06 · borrador propio para matriz final del editor");
  } else if (process.argv.includes("--catalog-privacy")) {
    await verifyCatalogPrivacy(state);
  } else if (process.argv.includes("--privacy")) {
    await verifyPrivacy(state);
  } else if (process.argv.includes("--pdf-policies")) {
    await verifyPdfPolicies(state);
  } else if (process.argv.includes("--publication")) {
    await verifyPublication(state);
  } else if (process.argv.includes("--chain")) {
    await verifyChain(state);
  } else if (process.argv.includes("--more")) {
    await verifyMore(JSON.parse(await fs.readFile(".run/d06-editable-state.json", "utf8")));
  } else if (!process.argv.includes("--setup")) {
    if (!process.argv.includes("--policy-only")) {
      await verifyEditor(state);
      await verifyServices(state);
    }
    await verifyPolicy(state);
  }
} catch (error) {
  if (lastPage && !lastPage.isClosed()) await lastPage.screenshot({ path: out + "/fallo.png" });
  throw error;
} finally {
  const mode =
    process.argv.find((argument) => argument.startsWith("--"))?.slice(2) ?? "editor-servicios";
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

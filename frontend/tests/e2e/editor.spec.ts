import { expect, test, type Page } from "@playwright/test";
import { environment } from "./support/environment";
import * as OTPAuth from "otpauth";

const supabase = environment("SUPABASE_URL")!;
const service = environment("SUPABASE_SERVICE_ROLE_KEY")!;
const backend = environment("DJANGO_URL") ?? "http://127.0.0.1:8000";
let userId: string, organizationId: string, projectId: string, systemId: string;
let ownerId: string;
let session: { user: { id: string }; access_token: string };
test.use({ viewport: { width: 1440, height: 900 } });

test.beforeAll(async () => {
  test.setTimeout(120_000);
  if (!supabase || !service || !["127.0.0.1", "localhost"].includes(new URL(supabase).hostname)) {
    throw new Error("Editor E2E requires isolated local Supabase");
  }
  const admin = {
    apikey: service,
    Authorization: `Bearer ${service}`,
    "Content-Type": "application/json",
  };
  const email = `editor-${crypto.randomUUID()}@example.invalid`,
    password = "Editor-E2E-local-2026!";
  const user = await fetch(`${supabase}/auth/v1/admin/users`, {
    method: "POST",
    headers: admin,
    body: JSON.stringify({ email, password, email_confirm: true }),
  });
  expect(user.ok).toBeTruthy();
  userId = (await user.json()).id;
  organizationId = crypto.randomUUID();
  for (const [table, row] of [
    [
      "tenancy_organizations",
      { id: organizationId, name: "Editor E2E · DEMO", tax_id: `E2E-${organizationId}` },
    ],
    [
      "tenancy_memberships",
      { user_id: userId, org_id: organizationId, role: "ESTIMATOR", is_active: true },
    ],
  ] as const) {
    const result = await fetch(`${supabase}/rest/v1/${table}`, {
      method: "POST",
      headers: admin,
      body: JSON.stringify(row),
    });
    expect(result.ok).toBeTruthy();
  }
  const login = await fetch(`${supabase}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: admin,
    body: JSON.stringify({ email, password }),
  });
  expect(login.ok).toBeTruthy();
  session = await login.json();
  const headers = {
    Authorization: `Bearer ${session.access_token}`,
    "X-Organization-ID": organizationId,
    "Content-Type": "application/json",
  };
  const systems = await fetch(`${backend}/api/v1/engine/systems/`, { headers });
  expect(systems.ok).toBeTruthy();
  const available = (await systems.json()).systems.filter(
    (item: { code: string; quote_ready: boolean }) => item.code === "DEMO_60" && item.quote_ready,
  );
  expect(available).toHaveLength(1);
  systemId = available[0].id;
  // Commercial writes go through an OWNER with actual MFA and audit reasons.
  const ownerEmail = `editor-owner-${crypto.randomUUID()}@example.invalid`;
  const owner = await fetch(`${supabase}/auth/v1/admin/users`, {
    method: "POST",
    headers: admin,
    body: JSON.stringify({ email: ownerEmail, password, email_confirm: true }),
  });
  expect(owner.ok).toBeTruthy();
  ownerId = (await owner.json()).id;
  const membership = await fetch(`${supabase}/rest/v1/tenancy_memberships`, {
    method: "POST",
    headers: admin,
    body: JSON.stringify({
      user_id: ownerId,
      org_id: organizationId,
      role: "OWNER",
      is_active: true,
    }),
  });
  expect(membership.ok).toBeTruthy();
  const ownerLogin = await fetch(`${supabase}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: admin,
    body: JSON.stringify({ email: ownerEmail, password }),
  });
  expect(ownerLogin.ok).toBeTruthy();
  const ownerSession = await ownerLogin.json();
  const ownerAuth = { ...admin, Authorization: `Bearer ${ownerSession.access_token}` };
  const enrollment = await fetch(`${supabase}/auth/v1/factors`, {
    method: "POST",
    headers: ownerAuth,
    body: JSON.stringify({ factor_type: "totp", friendly_name: "Editor fixture" }),
  });
  expect(enrollment.ok).toBeTruthy();
  const factor = await enrollment.json();
  const challengeResponse = await fetch(`${supabase}/auth/v1/factors/${factor.id}/challenge`, {
    method: "POST",
    headers: ownerAuth,
    body: "{}",
  });
  expect(challengeResponse.ok).toBeTruthy();
  const challenge = await challengeResponse.json();
  const verification = await fetch(`${supabase}/auth/v1/factors/${factor.id}/verify`, {
    method: "POST",
    headers: ownerAuth,
    body: JSON.stringify({
      challenge_id: challenge.id,
      code: new OTPAuth.TOTP({
        secret: OTPAuth.Secret.fromBase32(factor.totp.secret),
        algorithm: "SHA1",
        digits: 6,
        period: 30,
      }).generate(),
    }),
  });
  expect(verification.ok).toBeTruthy();
  const verified = await verification.json();
  const pricingHeaders = { ...headers, Authorization: `Bearer ${verified.access_token}` };
  async function commercial(path: string, values: unknown) {
    const response = await fetch(`${backend}/api/v1/pricing/admin/${path}/`, {
      method: "POST",
      headers: pricingHeaders,
      body: JSON.stringify({
        values,
        reason: "Editor E2E · autoridad sintética DEMO del catálogo",
      }),
    });
    const body = await response.json();
    expect(
      response.ok,
      `Commercial fixture ${path}: ${body?.error?.code ?? response.status}`,
    ).toBeTruthy();
    return body;
  }
  // Explicit synthetic commercial authority, isolated to this test tenant.
  // The catalog seeds provide the amounts; the test does not guess prices.
  const list = await commercial("cost-lists", {
    supplier_name: "Editor E2E · DEMO",
    currency: "CLP",
    valid_from: "2026-01-01",
  });
  const listId = list.items[0].id;
  const catalogRates = await fetch(
    `${supabase}/rest/v1/catalog_demo_prices?system_id=eq.${systemId}&select=sku,unit,unit_cost::text`,
    { headers: admin },
  );
  expect(catalogRates.ok).toBeTruthy();
  const rates = (await catalogRates.json()) as { sku: string; unit: string; unit_cost: string }[];
  expect(rates.length).toBeGreaterThan(0);
  // scripts/dev_fixture.py declares the same 100 CLP synthetic reinforcement
  // cost. It is fixture input, never a manufacturing or supplier authority.
  const steelResponse = await fetch(
    `${supabase}/rest/v1/reinforcement_articles?system_id=eq.${systemId}&select=commercial_sku,purchase_unit`,
    { headers: admin },
  );
  expect(steelResponse.ok).toBeTruthy();
  for (const steel of await steelResponse.json()) {
    if (!rates.some((rate) => rate.sku === steel.commercial_sku))
      rates.push({ sku: steel.commercial_sku, unit: steel.purchase_unit, unit_cost: "100" });
  }
  for (const rate of rates)
    await commercial("cost-items", { ...rate, cost_list_id: listId, item_type: "DEMO" });
  await commercial("rules", {
    pricing_mode: "COST_PLUS_MARGIN",
    default_margin_pct: "0.35",
    tax_rate_pct: "0.19",
    waste_factor_pct: "0.08",
    labor_rate_per_m2: "15000",
    installation_rate_per_m2: "12000",
  });
  const project = await fetch(`${backend}/api/v1/projects/`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "Casa Taller · Editor E2E DEMO",
      client_name: "Familia E2E · DEMO",
    }),
  });
  expect(project.ok).toBeTruthy();
  projectId = (await project.json()).id;
});

test.beforeEach(async ({ page }) => {
  await page.addInitScript(
    ({ session, organizationId }) => {
      localStorage.setItem("sb-127-auth-token", JSON.stringify(session));
      localStorage.setItem(`dekopen.active_org.${session.user.id}`, organizationId);
      localStorage.setItem("dekopen.theme", "light");
    },
    { session, organizationId },
  );
});

test.afterAll(async () => {
  const headers = { apikey: service, Authorization: `Bearer ${service}` };
  if (organizationId) {
    const removed = await fetch(
      `${supabase}/rest/v1/tenancy_organizations?id=eq.${organizationId}`,
      { method: "DELETE", headers },
    );
    expect(removed.status).toBe(204);
  }
  if (userId)
    await fetch(`${supabase}/auth/v1/admin/users/${userId}`, { method: "DELETE", headers });
  if (ownerId)
    await fetch(`${supabase}/auth/v1/admin/users/${ownerId}`, { method: "DELETE", headers });
});

async function open(page: Page) {
  await page.goto(`/projects/${projectId}/positions/new?system=${systemId}`);
  await page.locator(".starter-card").first().waitFor();
}

test("P06 bow is created in seven interactions, survives exact reload and synchronizes both drawings", async ({
  page,
}) => {
  await open(page);
  const started = Date.now();
  let interactions = 0;
  await page.locator(".starter-card").filter({ hasText: "Bow 3 módulos" }).click();
  interactions++;
  for (const ordinal of [1, 2, 3]) {
    if (ordinal !== 1) {
      await page.getByRole("button", { name: `Módulo ${ordinal} en planta`, exact: true }).click();
      interactions++;
    }
    const simulation = waitForDesignSimulation(page);
    await page
      .getByRole("combobox", { name: "Vidrio", exact: true })
      .selectOption({ label: "4-16-4 Float Incoloro · DEMO" });
    interactions++;
    await simulation;
    await expect(page.getByRole("combobox", { name: "Vidrio", exact: true })).toHaveValue(/.+/);
  }
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled({
    timeout: 20000,
  });
  const created = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url().endsWith(`/projects/${projectId}/positions/`),
  );
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  interactions++;
  const response = await created;
  expect(response.status()).toBe(201);
  const payload = response.request().postDataJSON(),
    position = await response.json();
  expect(interactions).toBeLessThanOrEqual(10);
  expect(Date.now() - started).toBeLessThan(60000);
  expect(position.design.parametric_tree).toEqual(payload.design.parametric_tree);
  const product = position.design.parametric_tree;
  expect(
    product.assembly.modules.map((item: { width_mm: string }) => Number(item.width_mm)),
  ).toEqual([600, 1200, 600]);
  expect(
    product.assembly.couplings.map((item: { angle_deg: string }) => Number(item.angle_deg)),
  ).toEqual([22.5, 22.5]);
  const evaluation = page.waitForResponse(
    (candidate) =>
      candidate.url().endsWith("/engine/assembly/calculate/") &&
      candidate.request().postDataJSON().product.assembly.modules[0].id ===
        product.assembly.modules[0].id,
  );
  await page.goto(`/projects/${projectId}/positions/${position.id}/edit`);
  expect((await evaluation).request().postDataJSON().product).toEqual(product);
  await page.getByRole("button", { name: "Módulo 2 en planta", exact: true }).click();
  await expect(page.locator(".front-module.is-selected")).toHaveCount(1);
  expect(await page.locator(".front-module.is-selected").getAttribute("aria-label")).toContain(
    product.assembly.modules[1].id,
  );
  await page.locator(".front-module").first().click();
  await expect(
    page.getByRole("button", { name: "Módulo 1 en planta", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  const separator = page.getByRole("separator", { name: "Altura de planta" });
  await separator.press("ArrowUp");
  await expect(separator).toHaveAttribute("aria-valuenow", "276");
  await page.getByRole("combobox", { name: "Elevación del conjunto" }).selectOption("projected");
  await expect(page.locator(".front-module").first()).toHaveAttribute("transform", /scale/);
  await page.getByRole("combobox", { name: "Elevación del conjunto" }).selectOption("developed");
  await page.getByRole("button", { name: "Ángulo de unión 1", exact: true }).press("Enter");
  const angle = page.getByRole("textbox", { name: "Ángulo de unión 1", exact: true });
  await angle.fill("89");
  await angle.press("Enter");
  await expect(page.getByRole("alert").filter({ hasText: "No se aplicó el cambio" })).toBeVisible({
    timeout: 20000,
  });
  await page.getByRole("button", { name: "Revisar unión", exact: true }).first().click();
  await expect(page.getByRole("combobox", { name: "Acoplador", exact: true })).toBeFocused();
});

test("P06 module drag previews engine geometry and sale, snaps at 30 degrees and undoes", async ({
  page,
}) => {
  await open(page);
  await page.locator(".starter-card").filter({ hasText: "Bow 3 módulos" }).click();
  for (const ordinal of [1, 2, 3]) {
    await page.getByRole("button", { name: `Módulo ${ordinal} en planta`, exact: true }).click();
    const simulation = waitForDesignSimulation(page, "set_glass");
    await page
      .getByRole("combobox", { name: "Vidrio", exact: true })
      .selectOption({ label: "4-16-4 Float Incoloro · DEMO" });
    await simulation;
  }
  const price = page.getByRole("button", { name: "Precio neto indicativo", exact: true });
  await expect(price).toContainText("$", { timeout: 20000 });
  const coordinates = await page
    .getByRole("button", { name: "Módulo 2 en planta", exact: true })
    .evaluate((element) => {
      const module = element as SVGPolygonElement;
      const joint = module
        .closest(".bow-plan-content")!
        .querySelector(".plan-coupling") as SVGPolygonElement;
      const points = Array.from(module.points);
      const center = new DOMPoint(
        points.reduce((x, p) => x + p.x / points.length, 0),
        points.reduce((y, p) => y + p.y / points.length, 0),
      );
      const pivot = joint.points[0]!,
        delta = (-7.5 * Math.PI) / 180;
      const x = center.x - pivot.x,
        y = center.y - pivot.y;
      const next = new DOMPoint(
        pivot.x + x * Math.cos(delta) - y * Math.sin(delta),
        pivot.y + x * Math.sin(delta) + y * Math.cos(delta),
      );
      const matrix = module.getScreenCTM()!;
      const from = center.matrixTransform(matrix),
        to = next.matrixTransform(matrix);
      return { from: { x: from.x, y: from.y }, to: { x: to.x, y: to.y } };
    });
  const preview = page.waitForResponse(
    (response) =>
      response.url().endsWith("/engine/assembly/calculate/") &&
      Number(response.request().postDataJSON().product.assembly.couplings[0].angle_deg) === 30,
  );
  const sale = page.waitForResponse(
    (response) =>
      response.url().endsWith("/operations/simulate/") &&
      response.request().postDataJSON().ops.length === 0 &&
      Number(response.request().postDataJSON().product.assembly.couplings[0].angle_deg) === 30,
  );
  await page.mouse.move(coordinates.from.x, coordinates.from.y);
  await page.mouse.down();
  await page.mouse.move(coordinates.to.x, coordinates.to.y);
  expect((await preview).status()).toBe(200);
  expect((await sale).status()).toBe(200);
  await expect(page.getByText("Vista previa de ángulo", { exact: true })).toBeVisible();
  await expect(page.locator(".assembly-plan-preview-price .editor-price")).toContainText("$", {
    timeout: 20000,
  });
  const commit = waitForDesignSimulation(page, "set_coupling_angle");
  await page.mouse.up();
  await commit;
  await expect(page.getByRole("button", { name: "Ángulo de unión 1", exact: true })).toHaveText(
    "30°",
  );
  await page.keyboard.press("Control+z");
  await expect(page.getByRole("button", { name: "Ángulo de unión 1", exact: true })).toHaveText(
    "22,5°",
  );
});

// Editing waits for the real engine transaction before checking the UI. Its
// catalog/pricing work can outlast the default five-second locator assertion.
async function waitForDesignSimulation(page: Page, operation?: string): Promise<void> {
  const response = await page.waitForResponse((candidate) => {
    if (
      !candidate.url().endsWith("/api/v1/projects/operations/simulate/") ||
      candidate.request().method() !== "POST"
    )
      return false;
    const data = candidate.request().postDataJSON() as { ops: { op: string }[] };
    return operation ? data.ops.some((op) => op.op === operation) : data.ops.length > 0;
  });
  expect(response.status()).toBe(200);
  const simulation = await response.json();
  expect(simulation.valid).toBe(true);
}

async function waitForIndicativePrice(
  page: Page,
  quantity: number,
  width: string,
  height: string,
  glassSku?: string,
): Promise<void> {
  const response = await page.waitForResponse((candidate) => {
    if (
      !candidate.url().endsWith("/api/v1/projects/operations/simulate/") ||
      candidate.request().method() !== "POST"
    )
      return false;
    const data = candidate.request().postDataJSON() as {
      ops: unknown[];
      quantity: number;
      product: { assembly: { modules: { width_mm: string; height_mm: string; tree: unknown }[] } };
    };
    const [module] = data.product.assembly.modules;
    return (
      data.ops.length === 0 &&
      data.quantity === quantity &&
      module !== undefined &&
      module.width_mm === width &&
      module.height_mm === height &&
      (!glassSku || JSON.stringify(module.tree).includes(glassSku))
    );
  });
  expect(response.status()).toBe(200);
  expect((await response.json()).valid).toBe(true);
}

test("two tilt-turn leaves 1500×1200 and 4-16-4 take at most six design interactions", async ({
  page,
}) => {
  await open(page);
  let interactions = 0;
  await page.getByRole("button", { name: /Dos hojas.*Oscilobatiente doble/ }).click();
  interactions++;
  const glass = page.getByRole("combobox", { name: "Vidrio", exact: true });
  await expect(glass.locator("option").filter({ hasText: /4-16-4/ })).toHaveCount(1);
  const options = await glass.locator("option").evaluateAll((nodes) =>
    nodes.map((node) => ({
      value: (node as HTMLOptionElement).value,
      text: node.textContent ?? "",
    })),
  );
  const thermopane = options.find((option) => option.text.includes("4-16-4"));
  expect(thermopane).toBeDefined();
  const glassSimulation = waitForDesignSimulation(page, "set_glass");
  await glass.selectOption(thermopane!.value);
  await glassSimulation;
  interactions++;
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  for (const [label, value] of [
    ["Ancho total", "1500"],
    ["Alto", "1200"],
  ]) {
    await page.locator(`.canvas-sheet [role="button"][aria-label="${label}"]`).first().click();
    interactions++;
    const field = page.locator(`foreignObject input[aria-label="${label}"]`);
    await field.fill(value!);
    const simulation = waitForDesignSimulation(
      page,
      label === "Alto" ? "set_height" : "set_total_width",
    );
    const finalPrice =
      label === "Alto" ? waitForIndicativePrice(page, 1, "1500.00", "1200.00") : null;
    await field.press("Enter");
    await simulation;
    if (finalPrice) await finalPrice;
    interactions++;
    await expect(page.locator(".viewport-status")).toContainText(
      label === "Alto" ? "1\u2009200" : "1\u2009500",
    );
    await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  }
  expect(interactions).toBeLessThanOrEqual(6);
  await expect(page.locator(".canvas-sheet [aria-label^='Paño']")).toHaveCount(2);
  await expect(
    page.getByRole("button", { name: "Precio neto indicativo", exact: true }),
  ).toContainText("$");
  await page.getByRole("button", { name: "Precio neto indicativo", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Fuente del precio indicativo", exact: true }),
  ).toContainText("Motor comercial");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  await page.getByLabel("Ubicación del vano", { exact: true }).fill("Dormitorio DEMO");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page).toHaveURL(/\/positions\/[^/]+\/edit$/);
  await page.reload();
  await expect(page.getByLabel("Ubicación del vano", { exact: true })).toHaveValue(
    "Dormitorio DEMO",
  );
  await expect(page.locator(".viewport-status")).toHaveText("1\u2009500 × 1\u2009200 mm");
  await expect(page.locator(".canvas-sheet [aria-label^='Paño']")).toHaveCount(2);
});

test("the sheet fits desktop, all tools are named, and a 10000px pan keeps it reachable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page);
  await page.getByRole("button", { name: "Cerrar Biblioteca de tipologías" }).click();
  const canvas = page.locator(".canvas-viewport");
  const box = (await canvas.boundingBox())!;
  expect(box.width).toBeGreaterThanOrEqual(1440 * 0.6);
  expect(box.height).toBeGreaterThanOrEqual(900 * 0.75);
  for (const button of await page.locator(".assembly-tools button").all()) {
    expect(await button.getAttribute("aria-label")).toBeTruthy();
    expect(await button.getAttribute("title")).toBeTruthy();
  }
  for (const width of [1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  const start = (await canvas.boundingBox())!;
  await page.mouse.move(start.x + 200, start.y + 200);
  await page.mouse.down({ button: "middle" });
  await page.mouse.move(start.x + 10200, start.y + 10200, { steps: 2 });
  await page.mouse.up({ button: "middle" });
  // Assert visibility BEFORE the explicit recovery control: a fit-only check
  // would hide an unbounded pan regression.
  await expect
    .poll(async () => {
      const drawing = (await page.locator(".canvas-sheet .front-module").boundingBox())!;
      const viewport = (await canvas.boundingBox())!;
      return (
        Math.min(drawing.x + drawing.width, viewport.x + viewport.width) -
        Math.max(drawing.x, viewport.x)
      );
    })
    .toBeGreaterThan(20);
  const panned = (await page.locator(".canvas-sheet .front-module").boundingBox())!;
  expect(
    Math.min(panned.y + panned.height, start.y + start.height) - Math.max(panned.y, start.y),
  ).toBeGreaterThan(20);
  await page.getByRole("button", { name: /Centrar.*Ajustar a la vista/ }).click();
  const drawing = await page.locator(".canvas-sheet .front-module").boundingBox();
  const viewport = (await canvas.boundingBox())!;
  expect(drawing!.x).toBeGreaterThanOrEqual(viewport.x);
  expect(drawing!.y).toBeGreaterThanOrEqual(viewport.y);
  expect(drawing!.x + drawing!.width).toBeLessThanOrEqual(viewport.x + viewport.width);
});

async function twoLeaves(page: Page) {
  await open(page);
  await page.getByRole("button", { name: /Dos hojas.*Oscilobatiente doble/ }).click();
  const glass = page.getByRole("combobox", { name: "Vidrio", exact: true });
  const option = glass.locator("option").filter({ hasText: /4-16-4/ });
  await expect(option).toHaveCount(1);
  const sku = (await option.getAttribute("value"))!;
  const simulation = waitForDesignSimulation(page, "set_glass");
  const price = waitForIndicativePrice(page, 1, "1400.00", "1400.00", sku);
  await glass.selectOption({ label: "4-16-4 Float Incoloro · DEMO" });
  await simulation;
  await price;
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
}

async function propose(page: Page) {
  await page.keyboard.press("Control+k");
  await page
    .locator('[role="dialog"] [role="combobox"]')
    .fill("partir en tres, centro fijo, laterales abatibles hacia el centro");
  await page.getByRole("option", { name: /partir en tres/i }).click();
}

test("price pending and transport failure hide the previous amount and retry the real engine", async ({
  page,
}) => {
  await twoLeaves(page);
  const chip = page.getByRole("button", { name: "Precio neto indicativo", exact: true });
  await expect(chip).toContainText("$");
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let intercept!: () => void;
  const intercepted = new Promise<void>((resolve) => {
    intercept = resolve;
  });
  const route = "**/api/v1/projects/operations/simulate/";
  await page.route(route, async (request) => {
    const data = request.request().postDataJSON() as { ops: unknown[]; quantity: number };
    if (data.ops.length || data.quantity !== 2) return request.continue();
    const response = await request.fetch();
    intercept();
    await held;
    await request.fulfill({ response });
  });
  await page.getByLabel("Cantidad", { exact: true }).fill("2");
  await intercepted;
  await expect(chip).toContainText("Calculando precio");
  await expect(chip).not.toContainText("$");
  release();
  await expect(chip).toContainText("$");
  await page.unroute(route);
  await page.route(route, async (request) => {
    const data = request.request().postDataJSON() as { ops: unknown[] };
    if (data.ops.length) return request.continue();
    await request.abort("failed");
  });
  await page.getByLabel("Cantidad", { exact: true }).fill("3");
  await expect(chip).toContainText("Sin dato");
  await expect(chip).not.toContainText("$");
  await chip.click();
  await expect(
    page.getByRole("region", { name: "Fuente del precio indicativo", exact: true }),
  ).toContainText("No se pudo consultar el precio");
  await page.unroute(route);
  const retriedPrice = waitForIndicativePrice(page, 3, "1400.00", "1400.00");
  await page.getByRole("button", { name: "Reintentar precio", exact: true }).click();
  await retriedPrice;
  await expect(chip).toContainText("$");
});

test("a simulated proposal applies and undoes, and quantity changes discard a late response", async ({
  page,
}) => {
  await twoLeaves(page);
  await page.getByLabel("Ancho", { exact: true }).fill("2000");
  const widthSimulation = waitForDesignSimulation(page, "set_module_width");
  await page.getByLabel("Ancho", { exact: true }).press("Enter");
  await widthSimulation;
  await expect(page.locator(".viewport-status")).toHaveText("2\u2009000 × 1\u2009400 mm");
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  await page.getByLabel("Ancho", { exact: true }).blur();
  const proposalSimulation = waitForDesignSimulation(page);
  await propose(page);
  await proposalSimulation;
  await expect(page.getByRole("button", { name: "Aplicar propuesta", exact: true })).toBeEnabled();
  await expect(page.locator(".command-ghost")).toHaveCount(1);
  await expect(page.locator(".editor-proposal-price")).toContainText("Δ neto de línea");
  await page.getByRole("button", { name: "Aplicar propuesta", exact: true }).click();
  await expect(page.locator(".canvas-sheet [aria-label^='Paño']")).toHaveCount(3);
  await page.getByRole("button", { name: "Deshacer", exact: true }).click();
  await expect(page.locator(".canvas-sheet [aria-label^='Paño']")).toHaveCount(2);

  let release!: () => void;
  const hold = new Promise<void>((resolve) => {
    release = resolve;
  });
  let intercept!: () => void;
  const intercepted = new Promise<void>((resolve) => {
    intercept = resolve;
  });
  let returned!: () => void;
  const completed = new Promise<void>((resolve) => {
    returned = resolve;
  });
  await page.route("**/api/v1/projects/operations/simulate/", async (route) => {
    if (!(route.request().postDataJSON() as { ops: unknown[] }).ops.length) return route.continue();
    const response = await route.fetch();
    intercept();
    await hold;
    await route.fulfill({ response });
    returned();
  });
  await propose(page);
  await intercepted;
  await page.getByLabel("Cantidad", { exact: true }).fill("2");
  release();
  await completed;
  await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
  await expect(page.locator(".command-ghost")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Aplicar propuesta", exact: true })).toHaveCount(0);
  await expect(page.locator(".canvas-sheet [aria-label^='Paño']")).toHaveCount(2);
});

test("every editor link opens the unsaved guard and only one footer panel remains open", async ({
  page,
}) => {
  await twoLeaves(page);
  const path = new URL(page.url()).pathname;
  const guarded = async (action: () => Promise<unknown>) => {
    await action();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("sin guardar");
    await dialog.getByRole("button", { name: "Cancelar", exact: true }).click();
    expect(new URL(page.url()).pathname).toBe(path);
  };
  await guarded(() => page.getByRole("link", { name: "Volver al proyecto", exact: true }).click());
  await page.getByRole("button", { name: "Posiciones del proyecto", exact: true }).click();
  await guarded(() =>
    page
      .locator(".editor-bottom-panel")
      .getByRole("link", { name: "Nuevo vano", exact: true })
      .click(),
  );
  await page.getByRole("button", { name: "Precio neto indicativo", exact: true }).click();
  await guarded(() =>
    page.getByRole("link", { name: "Revisar reglas de precio", exact: true }).click(),
  );
  await page.getByRole("button", { name: "Posiciones del proyecto", exact: true }).click();
  await page.getByRole("button", { name: "Despiece y materiales", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Posiciones del proyecto", exact: true }),
  ).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".editor-bottom-panel")).toHaveCount(1);
  await expect(page.locator(".editor-bottom-panel table")).not.toHaveCount(0);
});

test("tablet opening choices stay compatible and mobile blocks editing and save shortcuts", async ({
  page,
}) => {
  await twoLeaves(page);
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.getByRole("button", { name: "Inspector", exact: true }).click();
  await page.locator(".editor-opening-trigger").click();
  const choices = page.getByRole("group", { name: "Aperturas del sistema" });
  await expect(choices).toBeVisible();
  expect((await choices.innerText()).toLowerCase()).not.toContain("corredera");
  for (const name of await choices.getByRole("button").allTextContents())
    expect(name.trim().length).toBeGreaterThan(4);
  await expect(page.locator(".assembly-side")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByText("Vista de lectura · edición disponible desde 1024 px.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Ubicación del vano", { exact: true })).toBeDisabled();
  await expect(page.getByLabel("Cantidad", { exact: true })).toBeDisabled();
  let writes = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && /\/positions\//.test(request.url())) writes++;
  });
  await page.keyboard.press("Control+s");
  await page.keyboard.press("Delete");
  expect(writes).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await expect(page.locator(".canvas-sheet .front-module")).toBeVisible();
});

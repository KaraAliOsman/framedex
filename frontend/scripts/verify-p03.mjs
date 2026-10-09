/** Real P03 acceptance. Requires an explicitly selected local DEMO fixture.
 * Sessions and MFA secrets stay in memory; reports never contain capabilities.
 * --matrix records five roles plus the two new indexes in both themes.
 * DEKOPEN_P03_DECISION_PROJECT enables consequential price-decision exercise.
 */
import { chromium, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import * as OTPAuth from "otpauth";
import fs from "node:fs/promises";
import { collectPresentationFindings } from "./ux-capture/collect.ts";
import { detectTextFindings } from "./ux-capture/detectors.ts";

const base = "http://127.0.0.1:5173",
  apiBase = "http://127.0.0.1:8000/api/v1";
const supa = process.env.SUPABASE_URL,
  anon = process.env.SUPABASE_ANON_KEY;
const org = process.env.DEKOPEN_FIXTURE_ORG_ID;
if (!org || !supa || !anon || new URL(supa).port !== "25331")
  throw new Error("Select the owned local framedex-cola DEMO fixture explicitly.");
const out = process.env.DEKOPEN_P03_OUTPUT ?? "docs/redesign/captures/shell-hoy/recorrido";
const sessions = new Map(),
  factors = [],
  records = [];
const browser = await chromium.launch();
let lastPage;
async function auth(role) {
  if (sessions.has(role)) return sessions.get(role);
  const headers = { apikey: anon, "Content-Type": "application/json" };
  const response = await fetch(supa + "/auth/v1/token?grant_type=password", {
    method: "POST",
    headers,
    body: JSON.stringify({
      email: `demo-${role}@fixture.dekopen.local`,
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!response.ok) throw new Error("Fixture login: " + response.status);
  let session = await response.json();
  if (role === "owner") {
    headers.Authorization = `Bearer ${session.access_token}`;
    const enrolled = await fetch(supa + "/auth/v1/factors", {
      method: "POST",
      headers,
      body: JSON.stringify({ factor_type: "totp", friendly_name: "p03-" + Date.now() }),
    });
    if (!enrolled.ok) throw new Error("Fixture MFA enrollment: " + enrolled.status);
    const factor = await enrolled.json();
    factors.push({ factor, session });
    const challenged = await fetch(`${supa}/auth/v1/factors/${factor.id}/challenge`, {
      method: "POST",
      headers,
      body: "{}",
    });
    if (!challenged.ok) throw new Error("Fixture MFA challenge: " + challenged.status);
    const challenge = await challenged.json();
    const code = new OTPAuth.TOTP({
      secret: OTPAuth.Secret.fromBase32(factor.totp.secret),
      algorithm: "SHA1",
      digits: 6,
      period: 30,
    }).generate();
    const verified = await fetch(`${supa}/auth/v1/factors/${factor.id}/verify`, {
      method: "POST",
      headers,
      body: JSON.stringify({ challenge_id: challenge.id, code }),
    });
    if (!verified.ok) throw new Error("Fixture MFA verification: " + verified.status);
    session = { ...session, ...(await verified.json()) };
    factors.at(-1).session = session;
  }
  sessions.set(role, session);
  return session;
}
async function api(path, role = "estimator", body, method = body ? "POST" : "GET") {
  const session = await auth(role);
  const response = await fetch(apiBase + path, {
    method,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "X-Organization-ID": org,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error("Fixture domain request: " + response.status);
  return response.json();
}
async function pageFor(role = "estimator", width = 1440, theme = "light") {
  const session = await auth(role);
  const context = await browser.newContext({
    viewport: {
      width,
      height: width === 390 ? 844 : width === 1024 ? 768 : width === 1280 ? 800 : 900,
    },
    storageState: {
      cookies: [],
      origins: [
        {
          origin: base,
          localStorage: [
            { name: "sb-127-auth-token", value: JSON.stringify(session) },
            { name: `dekopen.active_org.${session.user.id}`, value: org },
            { name: "dekopen.theme", value: theme },
          ],
        },
      ],
    },
  });
  lastPage = await context.newPage();
  return lastPage;
}
async function capture(page, name, scope = ".today-page", simulation = null) {
  await page.evaluate(() => document.fonts.ready);
  const selectors = `${scope},${scope} *,.app-topbar,.app-topbar *,.app-rail,.app-rail *`;
  const findings = [
    ...detectTextFindings(await page.locator(scope).innerText()),
    ...(await collectPresentationFindings(page, false, selectors)),
  ];
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  const axe = await new AxeBuilder({ page })
    .include(scope)
    .include(".app-topbar")
    .include(".app-rail")
    .analyze();
  const serious = axe.violations
    .filter((v) => ["serious", "critical"].includes(v.impact))
    .map((v) => ({ id: v.id, targets: v.nodes.map((n) => n.target) }));
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  records.push({ name, simulation, findings, overflow, serious });
  expect(findings).toEqual([]);
  expect(overflow).toBe(false);
  expect(serious).toEqual([]);
}
async function visit(page, path) {
  await page.goto(base + path);
  await page.waitForLoadState("networkidle");
}
async function search(page, text, group) {
  const result = (await api("/search/?q=" + encodeURIComponent(text))).results.find(
    (r) => r.group === group && r.title.includes(text),
  );
  expect(result).toBeTruthy();
  await page.keyboard.press("Control+k");
  await page.locator(".command-palette input").fill(text);
  const option = page
    .getByRole("option")
    .filter({ has: page.getByText(result.title, { exact: true }) })
    .first();
  await expect(option).toBeVisible();
  await option.click();
  await page.waitForLoadState("networkidle");
  expect(new URL(page.url()).pathname + new URL(page.url()).search).toBe(result.path);
  if (group === "orders")
    await expect(
      page
        .locator(text.startsWith("OT-") ? ".production-detail" : ".purchasing-order")
        .filter({ hasText: text })
        .first(),
    ).toBeVisible();
  if (text.startsWith("RT-"))
    await expect(page.locator(".inventory-remnants tr[aria-current=true]")).toContainText(text);
  records.push({ name: "buscar-" + text, result: "PASA", group });
}
try {
  await fs.mkdir(out, { recursive: true });
  const me = await api("/auth/me/");
  expect(me.active_organization.name).toContain("P03 DEMO");
  if (process.argv.includes("--matrix")) {
    for (const role of ["owner", "estimator", "manager", "operator", "installer"])
      for (const width of [1440, 1280, 1024, 390])
        for (const theme of ["light", "dark"]) {
          const page = await pageFor(role, width, theme);
          await visit(page, "/dashboard");
          await expect(page.getByRole("heading", { name: "Hoy", exact: true })).toBeVisible();
          expect((await api("/analytics/today/", role)).actions.length).toBeGreaterThan(0);
          await capture(page, `${role}-${width}-${theme}`);
          await page.context().close();
        }
    for (const path of ["/inventory", "/quotes"])
      for (const width of [1440, 1280, 1024, 390])
        for (const theme of ["light", "dark"]) {
          const page = await pageFor("estimator", width, theme);
          await visit(page, path);
          await capture(
            page,
            `${path.slice(1)}-${width}-${theme}`,
            path === "/inventory" ? ".inventory-page" : ".quotations-page",
          );
          await page.context().close();
        }
  } else {
    const page = await pageFor();
    await visit(page, "/dashboard");
    expect((await api("/analytics/today/")).actions.some((a) => a.kind === "quote_viewed")).toBe(
      true,
    );
    for (const [text, group] of [
      ["P-000012", "projects"],
      ["OC-000003", "orders"],
      ["RT-000045", "inventory"],
      ["OT-P-000005-REV-A-03", "orders"],
      ["Cliente Prat · P03 DEMO", "clients"],
    ])
      await search(page, text, group);
    await search(page, "P-000005", "quotes");
    await visit(page, "/dashboard");
    const before = (await api("/analytics/today/")).actions
      .filter((a) => a.kind === "price_decision")
      .map((a) => a.operation_id);
    const writes = [];
    page.on("request", (r) => {
      if (r.method() !== "GET") writes.push(new URL(r.url()).pathname);
    });
    await page.getByRole("button", { name: "Atención pendiente", exact: true }).click();
    await expect(page.locator(".attention-menu")).toBeVisible();
    await page.keyboard.press("Escape");
    expect(
      (await api("/analytics/today/")).actions
        .filter((a) => a.kind === "price_decision")
        .map((a) => a.operation_id),
    ).toEqual(before);
    expect(writes).toEqual([]);
    const trigger = page.getByRole("button", { name: "Ayuda de atajos", exact: true });
    await trigger.focus();
    await page.keyboard.press("?");
    await expect(page.getByRole("dialog", { name: "Atajos de teclado" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(trigger).toBeFocused();
    await page.getByRole("button", { name: "Buscar o ejecutar un comando" }).click();
    await expect(page.locator(".command-palette input")).toBeFocused();
    await page.keyboard.press("Tab");
    expect(
      await page
        .locator(".command-palette")
        .evaluate((node) => node.contains(document.activeElement)),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: "Buscar o ejecutar un comando" })).toBeFocused();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole("button", { name: "Menú de navegación" }).click();
    await expect(page.locator(".app-shell")).toHaveClass(/rail-open/);
    await expect(page.locator(".app-rail a").first()).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    expect(
      await page.locator(".app-rail").evaluate((node) => node.contains(document.activeElement)),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await expect(page.locator(".app-shell")).not.toHaveClass(/rail-open/);
    await expect(page.getByRole("button", { name: "Menú de navegación" })).toBeFocused();
    await capture(page, "atajos-campana-390");
    for (const width of [390, 480, 760, 1023, 1024, 1280, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      ).toBe(true);
    }
    const other = me.memberships.find((member) => member.organization_id !== org);
    expect(other).toBeTruthy();
    let releaseSearch;
    const delayed = new Promise((resolve) => {
      releaseSearch = resolve;
    });
    let searchArrived;
    const arrived = new Promise((resolve) => {
      searchArrived = resolve;
    });
    await page.route("**/api/v1/search/?*", async (route) => {
      const response = await route.fetch();
      searchArrived();
      await delayed;
      await route.fulfill({ response }).catch(() => {});
    });
    await page.keyboard.press("Control+k");
    await page.locator(".command-palette input").fill("Cliente Prat");
    await arrived;
    await page.keyboard.press("Escape");
    await page.locator(".org-switcher__current").click();
    await page
      .locator(".org-switcher .shell-menu button")
      .filter({ hasText: other.organization_name })
      .click();
    await expect(page.locator(".org-switcher__current")).toContainText(other.organization_name);
    releaseSearch();
    await page.keyboard.press("Control+k");
    await expect(page.locator(".command-palette input")).toHaveValue("");
    await expect(page.getByRole("option").filter({ hasText: "Cliente Prat" })).toHaveCount(0);
    await page.keyboard.press("Escape");
    await page.unroute("**/api/v1/search/?*");
    await page.locator(".org-switcher__current").click();
    await page
      .locator(".org-switcher .shell-menu button")
      .filter({ hasText: me.active_organization.name })
      .click();
    await expect(page.locator(".org-switcher__current")).toContainText(me.active_organization.name);
    records.push({ name: "cambio-organizacion-busqueda-tardia", result: "PASA" });
    const payload = await api("/analytics/today/");
    for (const state of ["vacio", "error", "carga"]) {
      await page.route("**/api/v1/analytics/today/", (route) =>
        state === "error"
          ? route.fulfill({
              status: 500,
              contentType: "application/json",
              body: JSON.stringify({ error: { code: "fixture_failure" } }),
            })
          : state === "carga"
            ? new Promise(() => {})
            : route.fulfill({ json: { ...payload, actions: [], pipeline: [] } }),
      );
      await page.goto(base + "/dashboard");
      await expect(
        page.getByText(
          state === "vacio"
            ? "Todo al día"
            : state === "error"
              ? "No se pudo consultar tu trabajo"
              : "Consultando los compromisos de hoy",
          { exact: true },
        ),
      ).toBeVisible({ timeout: 20000 });
      await capture(
        page,
        "estado-" + state,
        ".today-page",
        "HTTP controlled to exercise UI state; domain not mutated",
      );
      await page.unroute("**/api/v1/analytics/today/");
    }
    await page.context().close();
    const floor = await pageFor("operator");
    await visit(floor, "/");
    expect(new URL(floor.url()).pathname).toBe("/production");
    await visit(floor, "/quotes");
    await expect(floor.getByText(/El dueño y el estimador consultan cotizaciones/)).toBeVisible();
    await capture(floor, "estado-sin-permiso", ".ui-empty--denied");
    await floor.context().close();
    const project = process.env.DEKOPEN_P03_DECISION_PROJECT;
    if (project) {
      for (const reject of [true, false]) {
        const draft = await api(`/projects/${project}/`);
        expect(draft.status).toBe("DRAFT");
        if (draft.current_pricing_operation_id)
          await api(`/projects/${project}/reset-pricing/`, "estimator", {
            expected_operation_id: draft.current_pricing_operation_id,
            confirmed: true,
            reason: "P03 · repetir decisión sobre borrador DEMO sin emisión",
          });
        const today = (await api("/analytics/today/")).today;
        const op = await api("/pricing/preview/", "estimator", {
          project_id: project,
          pricing_mode: "COST_PLUS_MARGIN",
          context_code: "DEFAULT",
          currency: "CLP",
          effective_date: today,
          discount_pct: "0",
          target_margin: "0.20",
          segment: "RETAIL",
          reason: "P03 · propuesta DEMO para decisión explícita",
        });
        expect(op.state).toBe("PENDING");
        const owner = await pageFor("owner");
        await visit(owner, "/dashboard");
        const row = owner
          .locator(".today-action")
          .filter({ hasText: op.project_code })
          .filter({ hasText: "Decide el acuerdo" });
        await row.getByRole("button", { name: "Revisar y decidir" }).first().click();
        const decision = owner.locator(".today-decision");
        await expect(decision.getByRole("button", { name: "Aprobar y aplicar" })).toBeDisabled();
        await decision
          .getByLabel("Motivo de la decisión")
          .fill("P03 · decisión revisada en Hoy DEMO");
        await decision.getByLabel("Confirmo las condiciones").check();
        await decision
          .getByRole("button", { name: reject ? "Rechazar" : "Aprobar y aplicar", exact: true })
          .click();
        await expect(decision.getByRole("status")).toContainText(
          reject ? "Solicitud rechazada" : "Precio aprobado y aplicado",
        );
        expect((await api(`/pricing/operations/${op.id}/`, "owner")).state).toBe(
          reject ? "REJECTED" : "APPLIED",
        );
        await capture(owner, reject ? "rechazo-en-hoy" : "aprobacion-en-hoy");
        await owner.context().close();
        const estimator = await pageFor();
        await visit(estimator, "/dashboard");
        await estimator
          .locator(".today-action")
          .filter({ hasText: op.project_code })
          .filter({ hasText: reject ? "Precio rechazado" : "Precio aprobado" })
          .getByRole("button", { name: "Leer decisión" })
          .first()
          .click();
        await estimator.getByRole("button", { name: "Marcar decisión como leída" }).click();
        await expect(estimator.getByRole("status")).toContainText("Decisión marcada como leída");
        expect((await api("/analytics/today/")).actions.some((a) => a.operation_id === op.id)).toBe(
          false,
        );
        await capture(estimator, reject ? "lectura-rechazo" : "lectura-aprobacion");
        await estimator.context().close();
      }
    }
  }
  console.log(`PASA: ${records.length} recorridos/capturas P03; sin hallazgos ni axe serious.`);
} catch (error) {
  if (lastPage && !lastPage.isClosed())
    await lastPage.screenshot({ path: out + "/fallo.png", fullPage: true });
  throw error;
} finally {
  await fs.writeFile(out + "/informe.json", JSON.stringify(records, null, 2));
  await browser.close();
  for (const { factor, session } of factors)
    await fetch(`${supa}/auth/v1/factors/${factor.id}`, {
      method: "DELETE",
      headers: { apikey: anon, Authorization: `Bearer ${session.access_token}` },
    });
}

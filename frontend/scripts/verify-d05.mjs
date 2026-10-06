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
  new URL("../../docs/redesign/captures/colores-acabados/recorrido", import.meta.url),
);
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("D05 verification requires the owned local Supabase stack.");
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
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d05-" + Date.now() }),
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
    ? await page.locator(scope).innerText()
    : name.startsWith("catalogo-")
      ? await page.locator(".finish-authority").innerText()
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
      ".finish-selector *, .finish-authority *, .assembly-view-choices *, .portal-position__faces *",
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

async function verifyStatesAndPublication() {
  const state = JSON.parse(await fs.readFile(".run/d05-ui-state.json", "utf8"));
  const route = `/projects/${state.project.id}/positions/${state.position.id}/edit`;
  for (const mode of ["loading", "error", "permission", "blocked"]) {
    const p = await pageFor("estimator");
    let release;
    if (mode === "blocked") {
      await p.route("**/api/v1/projects/design-options/**", async (r) => {
        const response = await r.fetch();
        const data = await response.json();
        data.finish_authority.combinations = data.finish_authority.combinations.filter(
          (c) => c.code !== "WHITE_WALNUT",
        );
        await r.fulfill({ response, json: data });
      });
    } else {
      await p.route("**/api/v1/projects/finish-preview/", async (r) => {
        if (mode === "loading") {
          await new Promise((resolve) => {
            release = resolve;
          });
          return r.continue();
        }
        return r.fulfill({
          status: mode === "permission" ? 403 : 503,
          contentType: "application/json",
          body: JSON.stringify({ error: { code: "fixture", detail: "Fallo de ensayo" } }),
        });
      });
    }
    await p.goto(base + route, { waitUntil: "domcontentloaded" });
    const selector = p.locator(".finish-selector");
    if (mode !== "loading")
      await expect(selector).toContainText(
        mode === "error"
          ? "Sin dato: no se pudo"
          : mode === "permission"
            ? "Tu rol no permite"
            : "Bloqueado",
      );
    if (mode === "loading") {
      await selector.scrollIntoViewIfNeeded();
      await expect(selector.locator(".ui-dim-loader")).toBeVisible();
      await p.screenshot({ path: out + "/estado-carga.png" });
      release();
      await expect(selector.locator(".ui-dim-loader")).toHaveCount(0);
    } else await capture(p, "estado-" + mode);
    if (mode === "error") {
      await p.unroute("**/api/v1/projects/finish-preview/");
      await selector.getByRole("button", { name: "Reintentar precio", exact: true }).click();
      await expect(selector.locator("[role=alert]")).toHaveCount(0);
      await expect(selector.locator(".finish-price")).toContainText("$");
      await capture(p, "estado-reintento");
    }
    await p.context().close();
  }
  const denied = await pageFor("operator");
  await denied.goto(base + route, { waitUntil: "networkidle" });
  await expect(denied.locator("body")).toContainText("Sin acceso");
  await capture(denied, "rol-operario-sin-acceso");
  await denied.context().close();
  const p = await pageFor("manager");
  await p.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
  await p.getByRole("button", { name: "Crear serie", exact: true }).click();
  const chart = p.locator(".finish-authority");
  await expect(chart).toContainText("Sin carta por caras");
  await chart.scrollIntoViewIfNeeded();
  await capture(p, "carta-vacia", ".finish-authority");
  await p.getByRole("button", { name: "Cancelar", exact: true }).click();
  const original = await request(
    "manager",
    `/catalogs/systems/${state.position.design.system_id}/`,
  );
  const schema = await request("manager", "/catalog-imports/schema/");
  const columns = schema.sheets.find((s) => s.name === "Sistemas").columns;
  const code = "REVISION-D05-" + Date.now().toString(36);
  const sourceName = `carta-caras-${Date.now().toString(36)}.csv`;
  const values = {
    ...original,
    system_code: code,
    name: "Carta de ensayo por caras · DEMO",
    version: 1,
    source: "Ensayo de publicación D05 · datos sintéticos sin certificación",
    opening_capabilities: [],
    paired_leaf_rule: null,
  };
  const csvCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const row = columns
    .map((c) => {
      const value = c.key.startsWith("sliding.")
        ? original.sliding?.[c.key.slice(8)]
        : values[c.key];
      return csvCell(
        c.kind === "json" && value != null
          ? JSON.stringify(value)
          : Array.isArray(value)
            ? value.join("|")
            : value,
      );
    })
    .join(";");
  const csv =
    "\ufeffSistemas;DEKOPEN CATÁLOGO V1\n" +
    columns.map((c) => csvCell(c.label)).join(";") +
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
  await expect(p.locator(".finish-authority")).toContainText("Nogal");
  const walnut = p
    .locator(".finish-authority details")
    .filter({ has: p.locator("summary", { hasText: /Nogal\s*·\s*Foliado/ }) })
    .first();
  await walnut.locator("summary").first().click();
  await walnut
    .getByRole("textbox", { name: "Nombre comercial", exact: true })
    .fill("Nogal revisado · DEMO");
  await p.getByRole("button", { name: "Comparar cambios", exact: true }).click();
  const publish = p.getByRole("button", { name: "Publicar catálogo revisado", exact: true });
  await expect(publish).toBeDisabled();
  await p.locator(".catalog-review-diff").scrollIntoViewIfNeeded();
  await capture(p, "carta-diff-publicacion", ".catalog-import-review");
  await p.locator(".catalog-review-attestation input").check();
  await publish.click();
  await expect(entry).toContainText("Publicado", { timeout: 30000 });
  const systems = await request("manager", "/catalogs/systems/");
  const published = systems.items.find((s) => s.code === code);
  expect(published.finish_authority.colors.find((c) => c.code === "WALNUT").name).toBe(
    "Nogal revisado · DEMO",
  );
  await entry.getByRole("button", { name: "Deshacer publicación", exact: true }).click();
  await p
    .getByRole("dialog")
    .getByRole("button", { name: "Deshacer publicación", exact: true })
    .click();
  await expect(entry).toContainText("Publicación deshecha", { timeout: 30000 });
  const after = await request("manager", "/catalogs/systems/");
  expect(after.items.find((s) => s.id === published.id)?.is_active).toBe(false);
  await capture(p, "carta-publicacion-deshacer", ".catalog-ingest");
  await p.context().close();
  console.log(
    "PASA D05 · cinco estados, reintento, permiso real, carta editable, diff, publicación y deshacer",
  );
}

try {
  await fs.mkdir(out, { recursive: true });
  if (process.argv.includes("--states-only")) {
    await verifyStatesAndPublication();
  } else {
    const evidence = JSON.parse(
      await fs.readFile(
        "docs/redesign/captures/colores-acabados/recorrido/flujo-7-acabados.json",
        "utf8",
      ),
    );
    const project = await request("estimator", "/projects/", {
      name: "D05 · elección de acabados DEMO",
      client_name: "Cliente de ensayo",
    });
    const source = await request("estimator", `/positions/${evidence.positions[1].position_id}/`);
    const position = await request("estimator", `/projects/${project.id}/positions/`, {
      location_tag: "Dormitorio · DEMO",
      quantity: 1,
      design: source.design,
    });
    const route = `/projects/${project.id}/positions/${position.id}/edit`;
    const p = await pageFor("estimator");
    await p.goto(base + route, { waitUntil: "networkidle" });
    await expect(p.locator(".finish-selector")).toContainText("Refuerzo obligatorio");
    await expect(p.locator(".finish-selector")).toContainText("Plazo adicional: 5 días");
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toHaveValue(
      "WALNUT",
    );
    await capture(p, "selector-bicolor-interior");
    await p.getByRole("button", { name: "Vista exterior", exact: true }).click();
    await expect(p.locator('.assembly-canvas [data-testid="product-front"]')).toHaveClass(
      /is-exterior/,
    );
    await capture(p, "selector-bicolor-exterior");
    await p.getByRole("button", { name: "Vista interior", exact: true }).click();
    await p
      .getByRole("combobox", { name: "Color exterior", exact: true })
      .selectOption("ANTHRACITE");
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toHaveValue(
      "ANTHRACITE",
    );
    await p.getByRole("button", { name: "Deshacer", exact: true }).first().click();
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toHaveValue(
      "WALNUT",
    );
    await p.getByRole("checkbox", { name: "Igual en ambas caras", exact: true }).check();
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toBeDisabled();
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toHaveValue(
      "WHITE",
    );
    await p.getByRole("checkbox", { name: "Igual en ambas caras", exact: true }).uncheck();
    await p.getByRole("combobox", { name: "Color exterior", exact: true }).selectOption("WALNUT");
    await p.waitForLoadState("networkidle");
    await expect(p.getByRole("button", { name: "Guardar", exact: true })).toBeEnabled();
    console.log(
      "D05 guardar: estado",
      await p.locator(".projects-header [role=status]").innerText(),
    );
    const [saved] = await Promise.all([
      p.waitForResponse(
        (r) => r.url().includes(`/positions/${position.id}/`) && r.request().method() === "PUT",
      ),
      p.getByRole("button", { name: "Guardar", exact: true }).click(),
    ]);
    expect(saved.ok()).toBe(true);
    await p.reload({ waitUntil: "networkidle" });
    await expect(p.getByRole("combobox", { name: "Color exterior", exact: true })).toHaveValue(
      "WALNUT",
    );
    const reopened = await request("estimator", `/positions/${position.id}/`);
    expect(reopened.design.color).toBe("WHITE_WALNUT");
    expect(reopened.bom.finish.exterior.code).toBe("WALNUT");
    await p.locator(".model3d-toggle").click();
    await expect(p.locator(".model3d-inset canvas")).toBeVisible();
    await p.waitForTimeout(1500);
    await capture(p, "bicolor-3d");
    await p.context().close();
    for (const theme of ["light", "dark"])
      for (const size of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
      ]) {
        const page = await pageFor("estimator", theme, size);
        await page.goto(base + route, { waitUntil: "networkidle" });
        await expect(page.locator(".finish-selector")).toContainText("aproximado");
        await capture(page, `editor-${size.width}-${theme}`);
        await page.context().close();
      }
    for (const theme of ["light", "dark"])
      for (const size of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
      ]) {
        const page = await pageFor("manager", theme, size);
        await page.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
        const system = await request("manager", `/catalogs/systems/${source.design.system_id}/`);
        await page.locator(".catalog-system").filter({ hasText: system.name }).click();
        await page.getByRole("button", { name: "Consultar sistema", exact: true }).click();
        await expect(page.locator(".finish-authority")).toBeVisible();
        await page.locator(".finish-authority").scrollIntoViewIfNeeded();
        await capture(page, `catalogo-${size.width}-${theme}`);
        await page.context().close();
      }
    const portalFixture = JSON.parse(await fs.readFile(out + "/portal-fixture.json", "utf8"));
    const link = await request(
      "estimator",
      `/projects/${portalFixture.project_id}/quote-link/`,
      {},
    );
    const publicResponse = await fetch(api + `/portal/quotes/${link.token}/`);
    if (!publicResponse.ok) throw new Error("No se pudo consultar la cotización pública.");
    const publicQuote = await publicResponse.json();
    expect(publicQuote.positions).toHaveLength(7);
    for (const position of publicQuote.positions) {
      expect(position.resolved_finish?.profile_skus).toEqual({});
      expect(position.resolved_finish?.interior.name).toBeTruthy();
      expect(position.resolved_finish?.exterior.name).toBeTruthy();
    }
    for (const theme of ["light", "dark"])
      for (const size of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
        { width: 390, height: 844 },
      ]) {
        const page = await pageFor("estimator", theme, size);
        await page.goto(base + `/cotizacion/${link.token}`, { waitUntil: "networkidle" });
        await expect(page.locator("body")).toContainText("Nogal exterior / Blanco interior");
        await capture(page, `portal-${size.width}-${theme}`);
        const bicolor = page.locator(".portal-position").nth(1);
        const img = bicolor.locator("img.position-thumb");
        await bicolor.scrollIntoViewIfNeeded();
        await expect(img).toBeVisible();
        const insideImage = await img.getAttribute("src");
        await bicolor.getByRole("button", { name: "Vista exterior", exact: true }).click();
        await expect(img).not.toHaveAttribute("src", insideImage, { timeout: 30000 });
        await capture(page, `portal-exterior-${size.width}-${theme}`);
        await page.context().close();
      }
    await fs.writeFile(".run/d05-ui-state.json", JSON.stringify({ project, position }));
    console.log("PASA D05 · guardar/reabrir, undo, caras, 3D, catálogo y portal en matriz");
  }
} catch (e) {
  if (lastPage && !lastPage.isClosed()) await lastPage.screenshot({ path: out + "/fallo.png" });
  throw e;
} finally {
  await fs.writeFile(
    out +
      (process.argv.includes("--states-only") ? "/estados-publicacion.json" : "/navegador.json"),
    JSON.stringify(records, null, 2),
  );
  if (factor) {
    const a = sessions.get("owner");
    await fetch(supa + `/auth/v1/factors/${factor.id}`, {
      method: "DELETE",
      headers: { apikey: anon, Authorization: "Bearer " + a.access_token },
    });
  }
  await browser.close();
}

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
  new URL("../../docs/redesign/captures/vidrios-compuestos/recorrido", import.meta.url),
);
const browser = await chromium.launch({ headless: true });
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
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d02-" + Date.now() }),
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
async function capture(page, name) {
  await page.waitForLoadState("networkidle");
  const file = name + ".png";
  await page.screenshot({ path: out + "/" + file });
  const text = await page.locator("body").innerText();
  records.push({
    name,
    screenshot: file,
    width: await page.evaluate(() => innerWidth),
    overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    errors: page.errors,
    findings: detectTextFindings(text),
    presentation: await collectPresentationFindings(
      page,
      name.startsWith("pedido-"),
      ".glass-selector *, .glass-composer *, .glass-rules *, .glass-order *, .glass-batch *",
    ),
  });
  const record = records.at(-1);
  if (record.overflow || page.errors.length || record.findings.length || record.presentation.length)
    throw new Error(name + " browser error, overflow or presentation finding");
  console.log("PASA", name);
}
async function advanced(page) {
  const summary = page.locator(".glass-selector > details > summary");
  if ((await summary.locator("..").getAttribute("open")) === null) await summary.click();
  await page.getByText("Corte del vidrio a escala", { exact: true }).first().waitFor();
}
try {
  await fs.mkdir(out, { recursive: true });
  const systems = await request("estimator", "/catalogs/systems/");
  const system = systems.items.find((s) => s.code === "DEMO_60" && s.version === 2);
  const project = await request("estimator", "/projects/", {
    name: "D02 · selección, reglas y deshacer DEMO",
    client_name: "Cliente de prueba",
  });
  const settings = await pageFor("manager");
  await settings.goto(base + "/settings/general", { waitUntil: "networkidle" });
  const rules = settings.locator(".glass-rules");
  await rules.getByRole("button", { name: "Revisar ejemplos DEMO" }).click();
  await rules.getByRole("button", { name: "Revisar cambios de reglas" }).click();
  await expect(rules.getByRole("button", { name: "Aplicar reglas" })).toBeEnabled();
  await rules.getByRole("button", { name: "Aplicar reglas" }).click();
  await rules.getByText("Reglas guardadas con historial de revisión.").waitFor();
  await capture(settings, "reglas-aplicadas");
  await settings.context().close();

  const page = await pageFor("estimator");
  await page.goto(base + `/projects/${project.id}/positions/new`, { waitUntil: "networkidle" });
  await page.getByLabel("Serie de perfiles", { exact: true }).selectOption(system.id);
  const low = page.getByRole("button", { name: /DEMO · Termopanel Low-E/ });
  await low.click();
  await advanced(page);
  await page.getByLabel("Altura sobre el piso · mm", { exact: true }).fill("900");
  await page.getByLabel("Paño lateral de una puerta", { exact: true }).check();
  await page.locator(".glass-bay-notice").waitFor();
  await capture(page, "aviso-en-bahia");
  await page.locator(".glass-bay-notice").click();
  await expect(low).toHaveAttribute("aria-pressed", "false");
  const alternativeSku = await page
    .locator('.glass-product[aria-pressed="true"]')
    .getAttribute("data-glass-sku");
  const safe = page.locator(`[data-glass-sku="${alternativeSku}"]`);
  await expect(safe).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".glass-bay-notice")).toHaveCount(0);
  await page.keyboard.press("Control+z");
  await expect(low).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Control+y");
  await expect(safe).toHaveAttribute("aria-pressed", "true");
  const saved = page.waitForResponse(
    (r) => r.url().includes("/positions/") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  const response = await saved;
  if (!response.ok())
    throw new Error("Save " + response.status() + " " + JSON.stringify(await response.json()));
  await page.waitForURL(/\/positions\/[^/]+\/edit$/);
  const detail = await request("estimator", `/projects/${project.id}/`);
  const position = detail.positions[0];
  if (!position) throw new Error("Saved position missing");
  await page.reload({ waitUntil: "networkidle" });
  await expect(safe).toHaveAttribute("aria-pressed", "true");
  await capture(page, "guardado-y-reabierto");
  await page.context().close();

  const owner = await pageFor("owner");
  await owner.goto(base + `/projects/${project.id}/positions/${position.id}/edit`, {
    waitUntil: "networkidle",
  });
  await advanced(owner);
  await owner.getByRole("button", { name: "Componer y publicar variante", exact: true }).click();
  const dialog = owner.getByRole("dialog");
  const sku = "D02-UI-" + Date.now();
  const variantName = "DEMO · Vidrio revisado " + sku.slice(-6);
  await dialog.getByLabel("Nombre comercial", { exact: true }).fill(variantName);
  await dialog.getByLabel("Código del nuevo producto", { exact: true }).fill(sku);
  await dialog.getByLabel("Código de compra", { exact: true }).fill(sku + "-BUY");
  await dialog.getByLabel("Proveedor", { exact: true }).fill("Vidriero sintético D02");
  await dialog.getByRole("button", { name: "Revisar publicación", exact: true }).click();
  await capture(owner, "diff-antes-de-publicar");
  await dialog.getByRole("button", { name: "Publicar y asignar vidrio", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  const variant = owner.locator(`[data-glass-sku="${sku}"]`);
  await expect(variant).toHaveAttribute("aria-pressed", "true");
  await owner.keyboard.press("Control+z");
  await expect(variant).toHaveAttribute("aria-pressed", "false");
  await owner.keyboard.press("Control+y");
  await expect(variant).toHaveAttribute("aria-pressed", "true");
  const persisted = owner.waitForResponse(
    (r) => r.url().includes("/positions/") && r.request().method() === "PUT",
  );
  await owner.getByRole("button", { name: "Guardar", exact: true }).click();
  const saveResponse = await persisted;
  if (!saveResponse.ok())
    throw new Error(
      "Variant save " + saveResponse.status() + " " + JSON.stringify(await saveResponse.json()),
    );
  await owner.reload({ waitUntil: "networkidle" });
  await expect(variant).toHaveAttribute("aria-pressed", "true");
  await owner.context().close();

  const sizes = [
    { width: 1440, height: 900 },
    { width: 1280, height: 800 },
    { width: 1024, height: 768 },
  ];
  for (const theme of ["light", "dark"])
    for (const size of sizes) {
      const p = await pageFor("estimator", theme, size);
      const tag = theme + "-" + size.width;
      await p.goto(base + `/projects/${project.id}/positions/${position.id}/edit`, {
        waitUntil: "networkidle",
      });
      await p.locator('.glass-product[aria-pressed="true"]').waitFor();
      await p.locator(".glass-selector").scrollIntoViewIfNeeded();
      await capture(p, "selector-basico-" + tag);
      await advanced(p);
      await p.locator(".glass-section").scrollIntoViewIfNeeded();
      await capture(p, "selector-avanzado-" + tag);
      await p.getByRole("button", { name: "Componer y publicar variante", exact: true }).click();
      await p.getByRole("dialog").waitFor();
      await capture(p, "compositor-sin-permiso-" + tag);
      await p.context().close();
      const s = await pageFor("manager", theme, size);
      await s.goto(base + "/settings/general", { waitUntil: "networkidle" });
      await s.locator(".glass-rules").scrollIntoViewIfNeeded();
      await capture(s, "reglas-" + tag);
      await s.context().close();
    }
  const evidence = JSON.parse(await fs.readFile(out + "/flujo-12-posiciones.json", "utf8"));
  for (const theme of ["light", "dark"])
    for (const size of [...sizes, { width: 390, height: 844 }]) {
      const p = await pageFor("manager", theme, size);
      await p.goto(base + "/production?order=" + evidence.orders[0], { waitUntil: "networkidle" });
      const panel = p.locator(".glass-order").last();
      await panel.getByRole("button", { name: "Revisar pedido" }).click();
      await panel.locator(".glass-order-rows").waitFor();
      await panel.scrollIntoViewIfNeeded();
      await capture(p, "pedido-" + theme + "-" + size.width);
      if (theme === "light" && size.width === 1440)
        for (const label of ["Descargar PDF y etiquetas", "Descargar CSV"]) {
          const pending = p.waitForEvent("download");
          await panel.getByRole("button", { name: label }).click();
          const download = await pending;
          await download.saveAs(out + "/ui-" + download.suggestedFilename());
        }
      await p.context().close();
    }
  await fs.writeFile(
    out + "/qa-report.json",
    JSON.stringify(
      {
        result: "PASA",
        project_id: project.id,
        position_id: position.id,
        variant_sku: sku,
        records,
      },
      null,
      2,
    ),
  );
} catch (error) {
  if (lastPage && !lastPage.isClosed()) {
    await lastPage.screenshot({ path: out + "/verification-failure.png" });
    console.log(
      JSON.stringify({
        path: new URL(lastPage.url()).pathname,
        text: (await lastPage.locator("body").innerText()).slice(0, 2000),
        errors: lastPage.errors,
      }),
    );
  }
  throw error;
} finally {
  await browser.close();
  if (factor) {
    const a = sessions.get("owner");
    const r = await fetch(supa + `/auth/v1/factors/${factor.id}`, {
      method: "DELETE",
      headers: { apikey: anon, Authorization: "Bearer " + a.access_token },
    });
    if (!r.ok) throw new Error("MFA cleanup " + r.status);
  }
}

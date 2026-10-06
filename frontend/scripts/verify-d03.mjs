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
  new URL("../../docs/redesign/captures/aperturas-tipologias/recorrido", import.meta.url),
);
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("D03 verification requires the owned local Supabase stack.");
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
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d03-" + Date.now() }),
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
      ".opening-palette *, .opening-availability *, .catalog-editor *",
    ),
  });
  const record = records.at(-1);
  if (record.overflow || page.errors.length || record.findings.length || record.presentation.length)
    throw new Error(name + " " + JSON.stringify(record));
  console.log("PASA", name);
}

try {
  await fs.mkdir(out, { recursive: true });
  const evidence = JSON.parse(
    await fs.readFile(
      "docs/redesign/captures/aperturas-tipologias/recorrido/flujo-21-aperturas.json",
      "utf8",
    ),
  );
  const project = await request("estimator", "/projects/", {
    name: "D03 · verificación de aperturas DEMO",
    client_name: "Cliente de prueba",
  });
  const positions = [];
  for (const item of evidence.positions) {
    const original = await request("estimator", `/positions/${item.position_id}/`);
    if (!original.design)
      throw new Error("Run verify_opening_flow.py against this local stack first.");
    const saved = await request("estimator", `/projects/${project.id}/positions/`, {
      location_tag: original.location_tag,
      quantity: 1,
      design: original.design,
    });
    positions.push({ ...item, id: saved.id });
  }
  await fs.mkdir(".run", { recursive: true });
  await fs.writeFile(".run/d03-ui-state.json", JSON.stringify({ project, positions }));
  const page = await pageFor("estimator");
  await page.goto(base + `/projects/${project.id}/positions/${positions[0].id}/edit`, {
    waitUntil: "networkidle",
  });
  await page.locator(".opening-palette").waitFor();
  const original = page.getByRole("button", {
    name: "Abatible hacia adentro — bisagras a la izquierda",
    exact: true,
  });
  await expect(original).toHaveAttribute("aria-pressed", "true");
  const tilt = page.getByRole("button", { name: "Solo abatimiento (banderola)", exact: true });
  await tilt.hover();
  await expect(page.locator(".opening-preview-label")).toContainText("Vista previa ·", {
    timeout: 20000,
  });
  await expect(page.locator('.assembly-canvas [data-motion="TILT"]')).toHaveCount(1);
  await expect(original).toHaveAttribute("aria-pressed", "true");
  await capture(page, "preview-banderola-sin-aplicar");
  await page.mouse.move(400, 200);
  await expect(page.locator(".opening-preview-label")).toHaveCount(0);
  await tilt.focus();
  await expect(page.locator(".opening-preview-label")).toContainText("Vista previa ·", {
    timeout: 20000,
  });
  await expect(original).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Enter");
  await expect(tilt).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Deshacer", exact: true }).click();
  await expect(original).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Rehacer", exact: true }).click();
  await expect(tilt).toHaveAttribute("aria-pressed", "true");
  const saved = page.waitForResponse(
    (r) => r.url().includes(`/positions/${positions[0].id}/`) && r.request().method() === "PUT",
  );
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  const save = await saved;
  if (!save.ok())
    throw new Error("Save " + save.status() + " " + JSON.stringify(await save.json()));
  await page.reload({ waitUntil: "networkidle" });
  await expect(tilt).toHaveAttribute("aria-pressed", "true");
  await capture(page, "guardado-reapertura-banderola");
  await original.click();
  const reset = page.waitForResponse(
    (r) => r.url().includes(`/positions/${positions[0].id}/`) && r.request().method() === "PUT",
  );
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  if (!(await reset).ok()) throw new Error("Restore failed");
  for (const item of positions) {
    await page.goto(base + `/projects/${project.id}/positions/${item.id}/edit`, {
      waitUntil: "networkidle",
    });
    await page.getByRole("button", { name: "Técnica", exact: true }).click();
    await expect(page.locator(".assembly-view-label")).toHaveText("Vista interior");
    const expected = (item.bom.opening_leaves ?? []).filter(
      (l) => l.opening.movement !== "FIXED" || l.opening.fixed_in_sash,
    );
    await expect(page.locator(".assembly-canvas [data-physical-leaf]")).toHaveCount(
      expected.length,
    );
    for (const leaf of expected) {
      const graphic = page
        .locator(".assembly-canvas [data-physical-leaf]")
        .filter({
          has: page.locator(
            `[data-hinge="${leaf.opening.hinge_side}"][data-leaf-role="${leaf.opening.leaf_role}"]`,
          ),
        })
        .first();
      await expect(graphic).toBeVisible();
      if (leaf.handle)
        await expect(graphic.locator("[data-engine-handle]")).toHaveAttribute(
          "data-handle-side",
          leaf.handle.side,
        );
    }
    await capture(page, "tipologia-" + item.name.toLowerCase());
  }
  await page.context().close();
  for (const theme of ["light", "dark"])
    for (const size of [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 1024, height: 768 },
    ]) {
      const p = await pageFor("estimator", theme, size);
      const item = positions.find((p) => p.name === "FRENCH-RIGHT");
      await p.goto(base + `/projects/${project.id}/positions/${item.id}/edit`, {
        waitUntil: "networkidle",
      });
      await p.locator(".opening-palette").waitFor();
      await capture(p, `editor-${size.width}-${theme}`);
      await p.getByRole("button", { name: "Técnica", exact: true }).click();
      await expect(p.locator('.assembly-canvas [data-leaf-role="PASSIVE"]')).toHaveCount(1);
      await expect(p.locator(".assembly-canvas [data-engine-handle]")).toHaveCount(1);
      await capture(p, `tecnica-${size.width}-${theme}`);
      await p.context().close();
    }
  console.log(
    "PASA preview mouse/keyboard, apply/undo/redo/save/reopen, 21 physical renders and viewport/theme matrix",
  );
  const ai = await pageFor("estimator");
  const target = positions.find((p) => p.name === "TURN-LEFT-OUTWARD");
  await ai.goto(base + `/projects/${project.id}/positions/${target.id}/edit`, {
    waitUntil: "networkidle",
  });
  const panel = ai.locator(".assistant-panel");
  if ((await panel.getAttribute("open")) === null) await panel.locator("summary").click();
  await panel
    .locator("textarea")
    .fill(
      "En el módulo 1 cambia la apertura a abatible hacia afuera con bisagras a la derecha. Conserva las medidas, el vidrio y el acabado.",
    );
  const proposed = ai.waitForResponse(
    (r) => r.url().includes("/design-assist/") && r.request().method() === "POST",
    { timeout: 150000 },
  );
  await panel.getByRole("button", { name: "Generar", exact: true }).click();
  const response = await proposed;
  const proposal = await response.json();
  if (
    !response.ok() ||
    !proposal.ops?.some(
      (o) =>
        o.op === "set_opening" &&
        o.opening?.direction === "OUTWARD" &&
        o.opening?.hinge_side === "RIGHT",
    )
  )
    throw new Error("MiMo proposal " + JSON.stringify(proposal));
  await fs.writeFile(out + "/ia-mimo-propuesta.json", JSON.stringify(proposal, null, 2));
  await capture(ai, "ia-mimo-propuesta-antes-de-aplicar");
  await panel.getByRole("button", { name: /Aplicar/ }).click();
  const right = ai.getByRole("button", {
    name: "Abatible hacia afuera — bisagras a la derecha",
    exact: true,
  });
  await expect(right).toHaveAttribute("aria-pressed", "true");
  await ai.getByRole("button", { name: "Deshacer", exact: true }).click();
  await expect(
    ai.getByRole("button", {
      name: "Abatible hacia afuera — bisagras a la izquierda",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await capture(ai, "ia-mimo-aplicar-deshacer");
  await ai.context().close();
} catch (e) {
  if (lastPage) await lastPage.screenshot({ path: out + "/fallo.png" });
  throw e;
} finally {
  await fs.writeFile(out + "/navegador.json", JSON.stringify(records, null, 2));
  if (factor) {
    const a = sessions.get("owner");
    await fetch(supa + `/auth/v1/factors/${factor.id}`, {
      method: "DELETE",
      headers: { apikey: anon, Authorization: "Bearer " + a.access_token },
    });
  }
  await browser.close();
}

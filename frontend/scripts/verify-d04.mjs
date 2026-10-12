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
  new URL("../../docs/redesign/captures/herrajes-clases/recorrido", import.meta.url),
);
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("D04 verification requires the owned local Supabase stack.");
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
      body: JSON.stringify({ factor_type: "totp", friendly_name: "d04-" + Date.now() }),
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
      ".hardware-panel *, .production-hardware *, .catalog-editor *",
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

async function edit(page, project, position) {
  await page.goto(base + `/projects/${project.id}/positions/${position.id}/edit`, {
    waitUntil: "networkidle",
  });
  await selectBay(page);
  await expect(page.locator(".hardware-panel")).toBeVisible();
  await expect(page.locator(".hardware-panel")).not.toContainText("Resolviendo clase", {
    timeout: 30000,
  });
}

async function selectBay(page) {
  await expect(page.locator(".assembly-canvas")).toBeVisible();
  const toggle = page.getByRole("button", { name: "Árbol del conjunto", exact: true });
  const tree = page.getByRole("navigation", { name: "Árbol del conjunto" });
  if ((await toggle.getAttribute("aria-pressed")) === "false") await toggle.click();
  await expect(tree).toBeVisible();
  await page
    .getByRole("navigation", { name: "Árbol del conjunto" })
    .getByRole("button", { name: /· Paño 1 · Módulo 1/ })
    .first()
    .click();
}

async function resize(page, label, value) {
  await page
    .getByRole("navigation", { name: "Árbol del conjunto" })
    .getByRole("button", { name: /^Módulo 1 \d/ })
    .click();
  const input = page.getByRole("textbox", { name: label + " mm", exact: true });
  await input.fill(value);
  await input.press("Enter");
  await selectBay(page);
}

async function save(page, position) {
  const response = page.waitForResponse(
    (r) => r.url().includes(`/positions/${position.id}/`) && r.request().method() === "PUT",
  );
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  const result = await response;
  if (!result.ok())
    throw new Error("Save failed " + result.status() + " " + JSON.stringify(await result.json()));
}

async function verifyCatalog(evidence) {
  const original = await request("manager", `/positions/${evidence.positions[0].position_id}/`);
  const systems = await request("manager", "/catalogs/systems/");
  const system = systems.items.find((item) => item.id === original.design.system_id);
  if (!system) throw new Error("Hardware authority series is missing");
  for (const theme of ["light", "dark"])
    for (const size of [
      { width: 1440, height: 900 },
      { width: 1280, height: 800 },
      { width: 1024, height: 768 },
    ]) {
      const p = await pageFor("manager", theme, size);
      await p.goto(base + "/catalogs/systems", { waitUntil: "networkidle" });
      await p.locator(".catalog-system").filter({ hasText: system.name }).click();
      await p.getByRole("tab", { name: "Kits de herraje", exact: true }).click();
      await p
        .getByRole("button", { name: /^Consultar .*Estándar/ })
        .first()
        .click();
      const authority = p.getByRole("group", { name: "Familia y reglas de clase" });
      await expect(authority).toContainText("DEMO, sin certificación");
      await expect(authority).toContainText("Fuente:");
      await expect(authority).toContainText("Cremona");
      await authority.scrollIntoViewIfNeeded();
      await capture(p, `catalogo-${size.width}-${theme}`);
      await p.context().close();
    }
}

try {
  await fs.mkdir(out, { recursive: true });
  const evidence = JSON.parse(
    await fs.readFile(
      "docs/redesign/captures/herrajes-clases/recorrido/flujo-12-posiciones.json",
      "utf8",
    ),
  );
  if (process.argv.includes("--catalog-only")) {
    await verifyCatalog(evidence);
  } else {
    if (process.argv.includes("--downstream-only")) {
      records.push(
        ...JSON.parse(await fs.readFile(out + "/navegador.json", "utf8")).filter(
          (record) => !record.name.startsWith("pedido-") && !record.name.startsWith("portal-"),
        ),
      );
    } else {
      const project = await request("estimator", "/projects/", {
        name: "D04 · revisión de clases DEMO",
        client_name: "Cliente de ensayo",
      });
      const positions = [];
      for (const item of evidence.positions.slice(0, 4)) {
        const original = await request("estimator", `/positions/${item.position_id}/`);
        const position = await request("estimator", `/projects/${project.id}/positions/`, {
          location_tag: item.name + " · DEMO",
          quantity: 1,
          design: original.design,
        });
        positions.push({ ...position, name: item.name });
      }
      const basePosition = await request("estimator", `/positions/${positions[0].id}/`);
      const paired = structuredClone(basePosition.design);
      paired.nominal_width_mm = "1600";
      paired.parametric_tree.opening.leaf_role = "ACTIVE";
      paired.parametric_tree.opening.movement = "TURN";
      paired.parametric_tree.hinged_layout = {
        leaves: [
          { slot: "LEFT", opening: { ...paired.parametric_tree.opening, leaf_role: "ACTIVE" } },
          {
            slot: "RIGHT",
            opening: {
              ...paired.parametric_tree.opening,
              hinge_side: "RIGHT",
              leaf_role: "PASSIVE",
            },
          },
        ],
      };
      positions.push(
        await request("estimator", `/projects/${project.id}/positions/`, {
          location_tag: "Pareja activa y pasiva · DEMO",
          quantity: 1,
          design: paired,
        }),
      );
      await fs.writeFile(
        ".run/d04-ui-state.json",
        JSON.stringify({ project, positions: positions.map((p) => ({ id: p.id, name: p.name })) }),
      );
      const page = await pageFor("estimator");
      await edit(page, project, positions[0]);
      const panel = page.locator(".hardware-panel");
      await expect(panel).toContainText("Estándar · DEMO");
      await panel.getByLabel("Modelo de manilla", { exact: true }).selectOption("KEY");
      await expect(panel.getByLabel("Modelo de manilla", { exact: true })).toHaveValue("KEY");
      await panel.getByLabel("Color de manilla", { exact: true }).selectOption("BLACK");
      await panel.getByText("Opciones vendibles", { exact: true }).click();
      await panel.getByLabel("Microventilación · DEMO", { exact: true }).check();
      await page.keyboard.press("F6");
      await expect(panel.locator(".hardware-advanced")).toHaveAttribute("open", "");
      await expect(panel).toContainText("Peso con herraje");
      await expect(panel).toContainText("Fuente: Herrajes sintéticos");
      await capture(page, "inspector-f6-manilla-opciones");
      await save(page, positions[0]);
      await page.reload({ waitUntil: "networkidle" });
      await selectBay(page);
      await expect(panel.getByLabel("Modelo de manilla", { exact: true })).toHaveValue("KEY");
      await expect(panel.getByLabel("Color de manilla", { exact: true })).toHaveValue("BLACK");
      await panel.getByText("Opciones vendibles", { exact: true }).click();
      await expect(panel.getByLabel("Microventilación · DEMO", { exact: true })).toBeChecked();
      await capture(page, "guardado-reapertura-opciones");
      await page.keyboard.press("F6");
      await panel
        .getByLabel("Clase de herraje", { exact: true })
        .selectOption({ label: "Pesada · DEMO" });
      await expect(panel.getByRole("region", { name: "Cambio de clase propuesto" })).toContainText(
        "Estándar · DEMO → Pesada · DEMO",
      );
      await capture(page, "diff-clase-con-delta");
      await panel.getByRole("button", { name: "Aplicar clase", exact: true }).click();
      await expect(panel.locator(".hardware-class strong")).toHaveText("Pesada · DEMO");
      await page.getByRole("button", { name: "Deshacer", exact: true }).click();
      await expect(panel.locator(".hardware-class strong")).toHaveText("Estándar · DEMO");
      await capture(page, "clase-aplicar-deshacer");
      const height = panel.getByLabel("Altura de manilla desde la base (mm)", { exact: true });
      await height.fill("5");
      await height.press("Enter");
      await expect(panel).toContainText("Bloqueada");
      await expect(panel).toContainText("Manilla a 5 mm");
      await expect(page.getByRole("button", { name: "Guardar", exact: true })).toBeDisabled();
      await capture(page, "altura-fuera-de-rango");
      await page.getByRole("button", { name: "Deshacer", exact: true }).click();
      await expect(panel).toContainText("Compatible · resuelta por el motor");
      await page.context().close();

      // An explicitly incompatible class must show the motor's proposed repair.
      const large = structuredClone(basePosition.design);
      large.nominal_width_mm = "1500";
      large.nominal_height_mm = "2300";
      const options = await request("estimator", `/projects/design-options/${large.system_id}/`);
      const standard = options.hardware_kits.find(
        (k) => k.opening_type === "TILT_TURN" && k.class_authority?.priority === 0,
      );
      large.parametric_tree.hardware_set_sku = standard.sku;
      const bad = await pageFor("estimator");
      await edit(bad, project, positions[1]);
      // The UI changes dimensions before saving; preview alone must remain editable.
      await bad.keyboard.press("F6");
      const bp = bad.locator(".hardware-panel");
      await bp.getByLabel("Clase de herraje", { exact: true }).selectOption(standard.sku);
      await bp.getByRole("button", { name: "Aplicar clase", exact: true }).click();
      await resize(bad, "Ancho", "1400");
      await resize(bad, "Alto", "2300");
      await expect(bp.getByRole("button", { name: /Revisar Pesada/ })).toBeVisible();
      {
        await bp.getByRole("button", { name: /Revisar Pesada/ }).click();
        await expect(bp.getByRole("region", { name: "Cambio de clase propuesto" })).toContainText(
          "Δ",
        );
        await capture(bad, "restriccion-siguiente-clase");
        await bp.getByRole("button", { name: "Aplicar clase", exact: true }).click();
        await expect(bp.locator(".hardware-class strong")).toHaveText("Pesada · DEMO");
        await bad.getByRole("button", { name: "Deshacer", exact: true }).click();
      }
      await resize(bad, "Ancho", "1800");
      const division = bp.getByRole("button", { name: "Revisar división compatible", exact: true });
      await expect(division).toBeVisible();
      await division.click();
      await expect(bp).toContainText("Δ herrajes:");
      await capture(bad, "division-diff-motor");
      await bp.getByRole("button", { name: "Aplicar división", exact: true }).click();
      await expect(bad.locator(".assembly-view-label")).toHaveText("Vista interior");
      await bad.getByRole("button", { name: "Deshacer", exact: true }).click();
      await capture(bad, "division-aplicar-deshacer");
      await bad.context().close();

      for (const theme of ["light", "dark"])
        for (const size of [
          { width: 1440, height: 900 },
          { width: 1280, height: 800 },
          { width: 1024, height: 768 },
        ]) {
          const p = await pageFor("estimator", theme, size);
          await edit(p, project, positions[0]);
          await capture(p, `editor-${size.width}-${theme}`);
          await p.keyboard.press("F6");
          await capture(p, `avanzado-${size.width}-${theme}`);
          await edit(p, project, positions[4]);
          await expect(p.locator(".hardware-panel .hardware-leaf")).toHaveCount(2);
          await expect(
            p.locator(".hardware-panel .hardware-leaf").nth(1).getByLabel("Modelo de manilla"),
          ).toHaveCount(0);
          await capture(p, `pareja-${size.width}-${theme}`);
          await p.context().close();
        }
      for (const mode of ["empty", "error", "permission", "loading"]) {
        const p = await pageFor("estimator");
        await p.route("**/api/v1/projects/hardware-preview/", async (route) => {
          if (mode === "loading") await new Promise((resolve) => setTimeout(resolve, 2500));
          if (mode === "loading") return route.continue();
          if (mode === "empty")
            return route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({
                leaves: [],
                division: null,
                is_demo: true,
                pricing_basis: "Catálogo sintético",
              }),
            });
          return route.fulfill({
            status: mode === "permission" ? 403 : 503,
            contentType: "application/json",
            body: JSON.stringify({ error: { code: "fixture", detail: "Fallo de ensayo" } }),
          });
        });
        await p.goto(base + `/projects/${project.id}/positions/${positions[0].id}/edit`, {
          waitUntil: "networkidle",
        });
        await selectBay(p);
        const hp = p.locator(".hardware-panel");
        await expect(hp).toContainText(
          mode === "loading"
            ? "Resolviendo clase"
            : mode === "empty"
              ? "no tiene hojas móviles"
              : mode === "permission"
                ? "Tu rol no permite"
                : "Sin dato: no se pudo",
        );
        if (mode === "loading") {
          await hp.scrollIntoViewIfNeeded();
          await expect(hp.locator(".ui-dim-loader")).toBeVisible();
          await p.screenshot({ path: out + "/estado-carga.png" });
        } else await capture(p, "estado-" + mode);
        if (mode === "error") {
          await p.unroute("**/api/v1/projects/hardware-preview/");
          await hp.getByRole("button", { name: "Volver a resolver", exact: true }).click();
          await expect(hp).toContainText("Compatible · resuelta por el motor");
        }
        await p.context().close();
      }
    }
    for (const theme of ["light", "dark"])
      for (const size of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
        { width: 390, height: 844 },
      ]) {
        const p = await pageFor("manager", theme, size);
        await p.goto(base + `/production?order=${evidence.orders[0]}`, {
          waitUntil: "networkidle",
        });
        const picking = p.getByRole("region", { name: "Picking de herrajes" });
        await expect(picking).toContainText("Cremona");
        await picking.getByText("Picking consolidado de la revisión", { exact: true }).click();
        await expect(picking.locator(".production-hardware-rows")).toHaveCount(2, {
          timeout: 30000,
        });
        await picking
          .getByRole("heading", { name: "Picking de herrajes" })
          .scrollIntoViewIfNeeded();
        await capture(p, `pedido-${size.width}-${theme}`);
        await p.context().close();
      }
    for (const role of ["operator", "installer"]) {
      const p = await pageFor(role);
      await p.goto(base + `/production?order=${evidence.orders[0]}`, { waitUntil: "networkidle" });
      await expect(p.getByRole("region", { name: "Picking de herrajes" })).toContainText("Cremona");
      await capture(p, "pedido-rol-" + role);
      await p.context().close();
    }
    const portalFixture = JSON.parse(await fs.readFile(out + "/portal-fixture.json", "utf8"));
    const link = await request(
      "estimator",
      `/projects/${portalFixture.project_id}/quote-link/`,
      {},
    );
    // The public token remains confined to memory and never enters evidence.
    for (const theme of ["light", "dark"])
      for (const size of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
        { width: 390, height: 844 },
      ]) {
        const p = await pageFor("estimator", theme, size);
        await p.goto(base + link.path, { waitUntil: "networkidle" });
        await expect(p.locator("body")).toContainText("Manilla");
        await expect(p.locator("body")).not.toContainText("Cremona");
        await capture(p, `portal-${size.width}-${theme}`);
        await p.context().close();
      }
    console.log(
      "PASA D04 · F6, opciones, guardado, diff, undo, división, estados, roles y matriz.",
    );
  }
} catch (e) {
  if (lastPage && !lastPage.isClosed()) await lastPage.screenshot({ path: out + "/fallo.png" });
  throw e;
} finally {
  await fs.writeFile(
    out + (process.argv.includes("--catalog-only") ? "/catalogo.json" : "/navegador.json"),
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

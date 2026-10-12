import { chromium, expect } from "@playwright/test";
import fs from "node:fs/promises";

const base = "http://127.0.0.1:5173",
  api = "http://127.0.0.1:8000/api/v1";
const supa = process.env.SUPABASE_URL,
  anon = process.env.SUPABASE_ANON_KEY;
const org = "548b9ce5-746b-5a4a-9127-733c4dcd0582";
const out = "docs/redesign/captures/aperturas-tipologias/recorrido";
if (!["127.0.0.1", "localhost"].includes(new URL(supa).hostname))
  throw new Error("This verification requires the owned local fixture.");
const sessions = new Map(),
  records = [];
async function auth(role) {
  if (sessions.has(role)) return sessions.get(role);
  const response = await fetch(supa + "/auth/v1/token?grant_type=password", {
    method: "POST",
    headers: { apikey: anon, "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `demo-${role}@fixture.dekopen.local`,
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!response.ok) throw new Error("Fixture login " + response.status);
  const session = await response.json();
  sessions.set(role, session);
  return session;
}
async function request(role, path, body, { method, etag, status = 200 } = {}) {
  const session = await auth(role);
  const response = await fetch(api + path, {
    method: method ?? (body ? "POST" : "GET"),
    headers: {
      Authorization: "Bearer " + session.access_token,
      "X-Organization-ID": org,
      "Content-Type": "application/json",
      ...(etag ? { "If-Match": '"' + etag + '"' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const result = await response.json();
  if (response.status !== status) throw new Error(path + " unexpected status " + response.status);
  return result;
}

let originalRules,
  rulesChanged = false;
const browser = await chromium.launch({ headless: true });
try {
  const state = JSON.parse(await fs.readFile(".run/d03-ui-state.json", "utf8"));
  const source = state.positions.find((item) => item.name === "DOOR-LEFT-OUTWARD");
  const original = await request("estimator", `/positions/${source.id}/`);
  const options = await request(
    "estimator",
    `/projects/design-options/${original.design.system_id}/`,
  );
  const glass = options.glass_specs.find((item) => item.sku.endsWith("-GLASS-LOWE"));
  const design = structuredClone(original.design);
  function infill(node) {
    if (node.version === "product-v2") {
      node.assembly.modules.forEach((module) => infill(module.tree));
    } else if (node.type === "BAY") {
      node.glass_article_sku = glass.sku;
      node.glass_product = glass.product;
      node.glass_spec = glass.spec;
      node.glass_thickness_mm = glass.total_thickness_mm;
    } else (node.children ?? []).forEach(infill);
  }
  infill(design.parametric_tree);
  const project = await request(
    "estimator",
    "/projects/",
    {
      name: "D03 · seguridad de puerta DEMO",
      client_name: "Cliente de prueba",
    },
    { status: 201 },
  );
  const payload = { location_tag: "Puerta de ensayo DEMO", quantity: 1, design };
  const position = await request("estimator", `/projects/${project.id}/positions/`, payload, {
    status: 201,
  });
  originalRules = await request("manager", "/catalogs/glass/rules/");
  const rule = { ...originalRules.examples.find((item) => item.zone === "DOOR"), mandatory: true };
  await request(
    "manager",
    "/catalogs/glass/rules/",
    { items: [rule] },
    {
      method: "PUT",
      etag: originalRules.revision,
    },
  );
  rulesChanged = true;
  const session = await auth("estimator");
  for (const size of [
    { width: 1440, height: 900 },
    { width: 1280, height: 800 },
    { width: 1024, height: 768 },
  ]) {
    for (const theme of ["light", "dark"]) {
      const context = await browser.newContext({
        viewport: size,
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
      const page = await context.newPage(),
        errors = [],
        previews = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("response", async (response) => {
        if (!response.url().endsWith("/catalogs/glass/preview/") || response.status() !== 200)
          return;
        const input = response.request().postDataJSON();
        if (input.technical_sku !== glass.sku || !input.width_mm) return;
        const report = await response.json();
        previews.push({
          opening_use: input.opening_use,
          opening_type: input.opening_type,
          width_mm: input.width_mm,
          height_mm: input.height_mm,
          findings: report.findings,
        });
      });
      await page.goto(base + `/projects/${project.id}/positions/${position.id}/edit`, {
        waitUntil: "networkidle",
      });
      await expect(page.locator(`.glass-product[data-glass-sku="${glass.sku}"]`)).toBeDisabled();
      await expect(page.locator('.glass-findings li[data-blocking="true"]').first()).toBeVisible();
      await expect
        .poll(() =>
          previews.some(
            (preview) =>
              preview.opening_use === "DOOR" &&
              preview.findings.some((finding) => finding.code === rule.code && finding.blocking),
          ),
        )
        .toBe(true);
      await page
        .locator('.glass-findings li[data-blocking="true"]')
        .first()
        .evaluate((element) => element.scrollIntoView({ block: "center", inline: "nearest" }));
      const name = `seguridad-puerta-${size.width}-${theme}`;
      await page.screenshot({ path: `${out}/${name}.png` });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (errors.length || overflow) throw new Error("Browser safety regression " + name);
      records.push({ name, errors, overflow, previews });
      await context.close();
    }
  }
  const save = await request("estimator", `/projects/${project.id}/positions/`, payload, {
    status: 422,
  });
  expect(save.error.code).toBe("glass_rule_required");
  const price = await request(
    "estimator",
    "/pricing/preview/",
    {
      project_id: project.id,
      pricing_mode: "COST_PLUS_MARGIN",
      context_code: "DEFAULT",
      currency: "CLP",
      effective_date: "2026-10-06",
      discount_pct: "0",
      target_margin: "0.35",
      segment: "RETAIL",
      confirmed: false,
      reason: "Regresión sintética D03 de seguridad de puerta",
    },
    { status: 422 },
  );
  expect(price.error.code).toBe("glass_rule_required");
  await fs.writeFile(
    `${out}/seguridad-puerta.json`,
    JSON.stringify(
      { records, saving: save.error.code, repricing: price.error.code, rule_source: rule.source },
      null,
      2,
    ),
  );
  console.log("PASA: six browser captures, authoritative preview, save and repricing safety.");
} finally {
  if (rulesChanged) {
    const current = await request("manager", "/catalogs/glass/rules/");
    await request(
      "manager",
      "/catalogs/glass/rules/",
      { items: originalRules.items },
      {
        method: "PUT",
        etag: current.revision,
      },
    );
    console.log("Owned fixture rules restored.");
  }
  await browser.close();
}

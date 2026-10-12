/** P12 acceptance against the explicitly selected owned local DEMO stack.
 * Authentication remains in memory; evidence contains no credentials. */
import { chromium, expect } from "@playwright/test";
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
const before = process.argv.includes("--before");
const out =
  process.env.DEKOPEN_P12_OUTPUT ??
  `docs/redesign/captures/produccion-estaciones/${before ? "antes" : "despues"}`;
const records = [],
  sessions = new Map();
const browser = await chromium.launch();
async function auth(role) {
  if (sessions.has(role)) return sessions.get(role);
  const response = await fetch(`${supa}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: anon, "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `demo-${role}@fixture.dekopen.local`,
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!response.ok) throw new Error(`Fixture login: ${response.status}`);
  const session = await response.json();
  sessions.set(role, session);
  return session;
}
async function api(path, role = "manager", body, method = body ? "POST" : "GET") {
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
  if (!response.ok) throw new Error(`Fixture domain request ${path}: ${response.status}`);
  return response.json();
}
async function pageFor(role, width, theme) {
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
  return context.newPage();
}
async function capture(page, name, workshop = false) {
  await page.evaluate(() => document.fonts.ready);
  const scope = ".production-page";
  const findings = [
    ...detectTextFindings(await page.locator(scope).innerText()),
    ...(await collectPresentationFindings(page, workshop, `${scope},${scope} *`)),
  ];
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  records.push({ name, findings, overflow });
  if (!before) {
    expect(findings).toEqual([]);
    expect(overflow).toBe(false);
  }
}
try {
  await fs.mkdir(out, { recursive: true });
  const orders = (await api("/production/orders/")).orders;
  const fixture = JSON.parse(await fs.readFile(".run/p12-fixture.json", "utf8"));
  const selected = orders.find((o) => o.id === fixture.orderId);
  if (!selected) throw new Error("The selected DEMO fixture needs a real work order.");
  expect(
    orders.filter((o) => o.project_version_id === fixture.versionId && !o.payload?.remake_of),
  ).toHaveLength(100);
  for (const role of ["manager", "operator"]) {
    for (const width of role === "operator" ? [1440, 1280, 1024, 390] : [1440, 1280, 1024]) {
      for (const theme of ["light", "dark"]) {
        const page = await pageFor(role, width, theme);
        await page.goto(base + "/production");
        await page.waitForLoadState("networkidle");
        await capture(page, `${role}-tablero-${width}-${theme}`, role === "operator");
        const start = performance.now();
        await page.goto(`${base}/production?order=${selected.id}`);
        await page.waitForFunction(
          (selector) => {
            const element = document.querySelector(selector);
            return element instanceof HTMLElement && element.offsetWidth > 0;
          },
          role === "operator" ? ".production-station-task" : "[role=tablist]",
          { polling: "raf" },
        );
        const interactiveMs = Math.round(performance.now() - start);
        records.push({ name: `${role}-interactividad-${width}-${theme}`, interactiveMs });
        if (!before) expect(interactiveMs).toBeLessThan(2000);
        await page.waitForLoadState("networkidle");
        await capture(page, `${role}-detalle-${width}-${theme}`, role === "operator");
        if (role === "manager") {
          const tabsTop = await page
            .getByRole("tablist")
            .evaluate((el) => el.getBoundingClientRect().top + scrollY);
          if (!before) expect(tabsTop).toBeLessThan(2 * page.viewportSize().height);
          records.push({ name: `pestanas-${width}-${theme}`, tabsTop });
          for (const tab of [
            "Piezas",
            "Corte",
            "Mecanizado",
            "Vidrios",
            "Herrajes",
            "Calidad",
            "Embalaje",
            "Trazabilidad",
          ]) {
            await page.getByRole("tab", { name: tab, exact: true }).click();
            await page.waitForLoadState("networkidle");
            await capture(page, `manager-${tab.toLowerCase()}-${width}-${theme}`);
          }
        }
        if (role === "operator") {
          const text = await page.locator(".production-page").innerText();
          expect(text).not.toMatch(/Cliente DEMO|margen|\$|Dirección privada/);
        }
        await page.context().close();
      }
    }
  }
} finally {
  await fs.writeFile(`${out}/informe.json`, JSON.stringify(records, null, 2));
  await browser.close();
}
console.log(`P12: ${records.length} captures recorded.`);

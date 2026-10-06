import { chromium, type Browser, type BrowserContext, type Page } from "@playwright/test";
import { spawn, type ChildProcess } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import * as OTPAuth from "otpauth";

import { detectTextFindings, summarizeFindings } from "./detectors.ts";
import { collectPresentationFindings } from "./collect.ts";
import {
  FIXTURE_USERS,
  THEMES,
  VIEWPORTS,
  routesForFixture,
  type FixtureRefs,
  type RouteDefinition,
  type UxRole,
} from "./routes.ts";

type Args = {
  out: string;
  routes?: string;
  roles?: UxRole[];
};

type AuthSession = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  expires_at?: number;
  token_type: string;
  user: { id: string };
};

type CaptureRecord = {
  routeId: string;
  path: string;
  reachedPath: string;
  role: string;
  theme: string;
  viewport: string;
  screenshot: string;
  overflowX: boolean;
  consoleErrors: string[];
  httpErrors: { url: string; status: number }[];
  findings: { kind: string; match?: string; sample?: string }[];
};

const baseUrl = process.env.UX_CAPTURE_BASE_URL ?? "http://127.0.0.1:5173";
const supabaseUrl =
  process.env.SUPABASE_URL ?? process.env.VITE_SUPABASE_URL ?? "http://127.0.0.1:25321";
const anonKey = process.env.SUPABASE_ANON_KEY ?? process.env.VITE_SUPABASE_ANON_KEY ?? "";
const djangoUrl = process.env.DJANGO_URL ?? "http://127.0.0.1:8000";
const organizationId = process.env.DEKOPEN_FIXTURE_ORG_ID ?? "548b9ce5-746b-5a4a-9127-733c4dcd0582";
const sessions = new Map<UxRole, AuthSession>();
const coverage = new Map<
  string,
  { text: string; ranges: { start: number; end: number }[]; usedSelectors?: string[] }
>();
let ownedFactor: { id: string; session: AuthSession } | undefined;

function parseArgs(argv: string[]): Args {
  const args: Args = { out: "docs/redesign/captures/ux-run" };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--out") args.out = argv[++index] ?? args.out;
    else if (item === "--routes") args.routes = argv[++index];
    else if (item === "--roles") {
      args.roles = (argv[++index] ?? "")
        .split(",")
        .map((role) => role.trim())
        .filter((role): role is UxRole => role in FIXTURE_USERS);
    }
  }
  return args;
}

async function waitForHttp(url: string, timeoutMs = 30_000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.status < 500) return true;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }
  return false;
}

async function ensureVite(): Promise<ChildProcess | null> {
  if (await waitForHttp(baseUrl, 2_000)) return null;
  const npmCli = path.join(
    path.dirname(process.execPath),
    "node_modules",
    "npm",
    "bin",
    "npm-cli.js",
  );
  const child = spawn(process.execPath, [npmCli, "run", "dev", "--", "--host", "127.0.0.1"], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      VITE_SUPABASE_URL: supabaseUrl,
      VITE_SUPABASE_ANON_KEY: anonKey,
    },
    stdio: "ignore",
  });
  if (!(await waitForHttp(baseUrl, 45_000))) {
    child.kill();
    throw new Error(`Vite did not become ready at ${baseUrl}`);
  }
  return child;
}

async function signIn(role: UxRole): Promise<AuthSession> {
  const cached = sessions.get(role);
  if (cached) return cached;
  const user = FIXTURE_USERS[role];
  const response = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: anonKey, "Content-Type": "application/json" },
    body: JSON.stringify({ email: user.email, password: user.password }),
  });
  if (!response.ok) {
    throw new Error(`Could not sign in ${role}: HTTP ${response.status} ${await response.text()}`);
  }
  let session = (await response.json()) as AuthSession;
  if (role === "OWNER") {
    // Exercise the real mandatory MFA boundary; never bypass it in the UI.
    const headers = {
      apikey: anonKey,
      Authorization: `Bearer ${session.access_token}`,
      "Content-Type": "application/json",
    };
    const enroll = await fetch(`${supabaseUrl}/auth/v1/factors`, {
      method: "POST",
      headers,
      body: JSON.stringify({ factor_type: "totp", friendly_name: `ux-${Date.now()}` }),
    });
    if (!enroll.ok) throw new Error(`OWNER MFA enrollment -> ${enroll.status}`);
    const factor = (await enroll.json()) as { id: string; totp: { secret: string } };
    const challenge = await fetch(`${supabaseUrl}/auth/v1/factors/${factor.id}/challenge`, {
      method: "POST",
      headers,
      body: "{}",
    });
    if (!challenge.ok) throw new Error(`OWNER MFA challenge -> ${challenge.status}`);
    const { id: challengeId } = (await challenge.json()) as { id: string };
    const code = new OTPAuth.TOTP({
      secret: OTPAuth.Secret.fromBase32(factor.totp.secret),
      algorithm: "SHA1",
      digits: 6,
      period: 30,
    }).generate();
    const verified = await fetch(`${supabaseUrl}/auth/v1/factors/${factor.id}/verify`, {
      method: "POST",
      headers,
      body: JSON.stringify({ challenge_id: challengeId, code }),
    });
    if (!verified.ok) throw new Error(`OWNER MFA verification -> ${verified.status}`);
    session = { ...session, ...((await verified.json()) as AuthSession) };
    ownedFactor = { id: factor.id, session };
  }
  sessions.set(role, session);
  return session;
}

async function authenticatedFetch<T>(session: AuthSession, apiPath: string): Promise<T> {
  const response = await fetch(`${djangoUrl}/api/v1${apiPath}`, {
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "X-Organization-ID": organizationId,
    },
  });
  if (!response.ok) throw new Error(`GET ${apiPath} -> ${response.status}`);
  return (await response.json()) as T;
}

async function discoverFixture(session: AuthSession): Promise<FixtureRefs> {
  const projects = await authenticatedFetch<{ items: { id: string; name: string }[] }>(
    session,
    "/projects/",
  );
  const project =
    projects.items.find((item) => /casa|vivienda|fixture/i.test(item.name)) ?? projects.items[0];
  if (!project) throw new Error("Fixture has no project; run scripts/dev_fixture.py first");
  const detail = await authenticatedFetch<{
    positions?: { id: string }[];
    items?: { id: string }[];
  }>(session, `/projects/${project.id}/`);
  const positionId = detail.positions?.[0]?.id ?? detail.items?.[0]?.id ?? "missing-position";
  let clientId = process.env.DEKOPEN_UX_CLIENT_ID ?? "missing-client";
  try {
    const clients = await authenticatedFetch<{ items: { id: string }[] }>(session, "/clients/");
    clientId = clients.items[0]?.id ?? clientId;
  } catch {
    // Clients are still covered by /clients when detail discovery is unavailable.
  }
  return {
    projectId: process.env.DEKOPEN_UX_PROJECT_ID ?? project.id,
    positionId: process.env.DEKOPEN_UX_POSITION_ID ?? positionId,
    clientId,
    quoteTokens: {
      vigente: process.env.DEKOPEN_UX_QUOTE_VIGENTE ?? "fixture-vigente",
      aprobada: process.env.DEKOPEN_UX_QUOTE_APROBADA ?? "fixture-aprobada",
      revocada: process.env.DEKOPEN_UX_QUOTE_REVOCADA ?? "fixture-revocada",
      expirada: process.env.DEKOPEN_UX_QUOTE_EXPIRADA ?? "fixture-expirada",
      reemplazada: process.env.DEKOPEN_UX_QUOTE_REEMPLAZADA ?? "fixture-reemplazada",
    },
  };
}

function globMatches(value: string, glob?: string): boolean {
  if (!glob) return true;
  const pattern = new RegExp(
    `^${glob
      .split("*")
      .map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join(".*")}$`,
  );
  return pattern.test(value);
}

async function prepareContext(
  browser: Browser,
  role: UxRole,
  theme: string,
  viewport: { width: number; height: number },
  publicRoute: boolean,
): Promise<BrowserContext> {
  const session = publicRoute ? null : await signIn(role);
  const storageKey = `sb-${new URL(supabaseUrl).hostname.split(".")[0]}-auth-token`;
  const context = await browser.newContext({
    baseURL: baseUrl,
    viewport,
    storageState: session
      ? {
          cookies: [],
          origins: [
            {
              origin: new URL(baseUrl).origin,
              localStorage: [
                { name: storageKey, value: JSON.stringify(session) },
                { name: `dekopen.active_org.${session.user.id}`, value: organizationId },
              ],
            },
          ],
        }
      : undefined,
  });
  await context.addInitScript(
    ({ selectedTheme }) => {
      window.localStorage.setItem("dekopen.theme", selectedTheme);
    },
    { selectedTheme: theme },
  );
  return context;
}

async function captureRoute(
  context: BrowserContext,
  route: RouteDefinition,
  role: UxRole,
  theme: string,
  viewportId: string,
  outDir: string,
): Promise<CaptureRecord> {
  const page = await context.newPage();
  await page.coverage.startCSSCoverage({ resetOnNavigation: false });
  const consoleErrors: string[] = [];
  const httpErrors: { url: string; status: number }[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      httpErrors.push({ url: response.url(), status: response.status() });
    }
  });
  await page.goto(route.path, { waitUntil: "networkidle", timeout: 45_000 });
  await page.waitForTimeout(350);
  const text = await page
    .locator("body")
    .innerText({ timeout: 5_000 })
    .catch(() => "");
  const overflowX = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  const findings = [
    ...detectTextFindings(text),
    ...(await collectPresentationFindings(
      page,
      route.workshop || role === "OPERATOR" || role === "INSTALLER",
    )),
  ];
  const screenshot = `${route.id}__${role}__${theme}__${viewportId}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: true });
  for (const sheet of await page.coverage.stopCSSCoverage()) {
    const key = sheet.url.split("?")[0] || `inline-${sheet.text.length}`;
    const previous = coverage.get(key);
    coverage.set(key, { text: sheet.text, ranges: [...(previous?.ranges ?? []), ...sheet.ranges] });
  }
  // Vite injects anonymous <style> sheets that Chromium's URL-only coverage
  // omits. Record matching CSSOM selectors too; removal also needs a source
  // reachability check because this run cannot exercise every transient state.
  const injected = await page.evaluate(() =>
    Array.from(document.styleSheets).flatMap((sheet) => {
      const owner = sheet.ownerNode;
      if (!(owner instanceof HTMLStyleElement)) return [];
      const usedSelectors: string[] = [];
      function visit(rules: CSSRuleList): void {
        for (const rule of Array.from(rules)) {
          if (rule instanceof CSSMediaRule && !matchMedia(rule.conditionText).matches) continue;
          if (rule instanceof CSSStyleRule) {
            try {
              if (document.querySelector(rule.selectorText)) usedSelectors.push(rule.selectorText);
            } catch {
              /* Browser-only pseudo-elements are retained by source evidence. */
            }
          } else if ("cssRules" in rule) visit((rule as CSSGroupingRule).cssRules);
        }
      }
      visit(sheet.cssRules);
      return [
        {
          url: owner.dataset.viteDevId ?? `inline-${owner.textContent?.length}`,
          text: owner.textContent ?? "",
          usedSelectors,
        },
      ];
    }),
  );
  for (const sheet of injected) {
    const previous = coverage.get(sheet.url);
    coverage.set(sheet.url, {
      text: sheet.text,
      ranges: previous?.ranges ?? [],
      usedSelectors: Array.from(
        new Set([...(previous?.usedSelectors ?? []), ...sheet.usedSelectors]),
      ),
    });
  }
  const reachedPath = new URL(page.url()).pathname;
  await page.close();
  return {
    routeId: route.id,
    path: route.path,
    reachedPath,
    role,
    theme,
    viewport: viewportId,
    screenshot,
    overflowX,
    consoleErrors,
    httpErrors,
    findings,
  };
}

function htmlReport(records: readonly CaptureRecord[]): string {
  const items = records
    .map(
      (record) => `<article>
<h2>${record.routeId} · ${record.role} · ${record.theme} · ${record.viewport}</h2>
<img src="./${record.screenshot}" loading="lazy" width="240">
<p>${record.path}</p>
<p>Hallazgos: ${record.findings.length} · HTTP >=400: ${record.httpErrors.length} · consola: ${record.consoleErrors.length} · overflow: ${record.overflowX}</p>
</article>`,
    )
    .join("\n");
  return `<!doctype html><meta charset="utf-8"><title>DEKOPEN ux:capture</title><style>body{font-family:system-ui;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}article{border:1px solid #ccc;padding:12px}img{max-width:100%;border:1px solid #ddd}</style><main>${items}</main>`;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const outDir = path.resolve(args.out);
  await mkdir(outDir, { recursive: true });
  const vite = await ensureVite();
  const browser = await chromium.launch({ headless: true });
  const estimator = await signIn("ESTIMATOR");
  const refs = await discoverFixture(estimator);
  const selectedRoles = new Set(args.roles ?? Object.keys(FIXTURE_USERS));
  const routes = routesForFixture(refs).filter(
    (route) => globMatches(route.id, args.routes) || globMatches(route.path, args.routes),
  );
  const records: CaptureRecord[] = [];
  try {
    for (const route of routes) {
      const roles = route.public ? [route.roles[0] ?? "ESTIMATOR"] : route.roles;
      for (const role of roles.filter((item) => selectedRoles.has(item))) {
        if (!route.public) await signIn(role);
        for (const theme of THEMES) {
          await Promise.all(
            VIEWPORTS.map(async (viewport) => {
              const context = await prepareContext(
                browser,
                role,
                theme,
                viewport,
                Boolean(route.public),
              );
              records.push(await captureRoute(context, route, role, theme, viewport.id, outDir));
              console.log(`${records.length}: ${route.id} ${role} ${theme} ${viewport.id}`);
              await context.close();
            }),
          );
          await writeFile(
            path.join(outDir, "records.partial.json"),
            JSON.stringify(records, null, 2),
          );
        }
      }
    }
  } finally {
    await browser.close();
    if (vite) vite.kill();
    if (ownedFactor) {
      const removed = await fetch(`${supabaseUrl}/auth/v1/factors/${ownedFactor.id}`, {
        method: "DELETE",
        headers: { apikey: anonKey, Authorization: `Bearer ${ownedFactor.session.access_token}` },
      });
      if (!removed.ok) throw new Error(`Fixture MFA teardown -> ${removed.status}`);
    }
  }
  const report = {
    generatedAt: new Date().toISOString(),
    baseUrl,
    records,
    topFindings: summarizeFindings(records).slice(0, 30),
  };
  await writeFile(path.join(outDir, "report.json"), JSON.stringify(report, null, 2));
  await writeFile(path.join(outDir, "index.html"), htmlReport(records));
  await writeFile(path.join(outDir, "coverage.json"), JSON.stringify(Object.fromEntries(coverage)));
}

await main();

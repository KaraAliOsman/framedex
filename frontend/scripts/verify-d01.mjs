import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import * as OTPAuth from "otpauth";
const base = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000/api/v1";
const org = "548b9ce5-746b-5a4a-9127-733c4dcd0582";
const sb = process.env.SUPABASE_URL;
const key = process.env.SUPABASE_ANON_KEY;
const response = await fetch(`${sb}/auth/v1/token?grant_type=password`, {
  method: "POST",
  headers: { apikey: key, "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "demo-owner@fixture.dekopen.local",
    password: "Demo-Fixture-2026!",
  }),
});
if (!response.ok) throw new Error("Fixture login failed");
let session = await response.json();
const mfaHeaders = {
  apikey: key,
  Authorization: `Bearer ${session.access_token}`,
  "Content-Type": "application/json",
};
const enrolled = await fetch(`${sb}/auth/v1/factors`, {
  method: "POST",
  headers: mfaHeaders,
  body: JSON.stringify({ factor_type: "totp", friendly_name: `D01-${Date.now()}` }),
});
if (!enrolled.ok) throw new Error(`MFA enrollment ${enrolled.status}`);
const factor = await enrolled.json();
const challenged = await fetch(`${sb}/auth/v1/factors/${factor.id}/challenge`, {
  method: "POST",
  headers: mfaHeaders,
  body: "{}",
});
const challenge = await challenged.json();
const code = new OTPAuth.TOTP({
  secret: OTPAuth.Secret.fromBase32(factor.totp.secret),
  algorithm: "SHA1",
  digits: 6,
  period: 30,
}).generate();
const verified = await fetch(`${sb}/auth/v1/factors/${factor.id}/verify`, {
  method: "POST",
  headers: mfaHeaders,
  body: JSON.stringify({ challenge_id: challenge.id, code }),
});
if (!verified.ok) throw new Error(`MFA verification ${verified.status}`);
session = { ...session, ...(await verified.json()) };
const out = path.resolve("docs/redesign/captures/sistemas-catalogo/flujos");
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  storageState: {
    cookies: [],
    origins: [
      {
        origin: base,
        localStorage: [
          {
            name: `sb-${new URL(sb).hostname.split(".")[0]}-auth-token`,
            value: JSON.stringify(session),
          },
          { name: `dekopen.active_org.${session.user.id}`, value: org },
        ],
      },
    ],
  },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
try {
  let releaseLoading;
  await page.route("**/api/v1/catalog-imports/", async (route) => {
    await new Promise((resolve) => {
      releaseLoading = resolve;
    });
    await route.fulfill({ status: 200, contentType: "application/json", body: '{"imports":[]}' });
  });
  await page.goto(base + "/catalogs/systems");
  await expect(page.getByRole("button", { name: "Importar catálogo", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Importar catálogo", exact: true }).click();
  await expect(page.getByText("Cargando importaciones…", { exact: true })).toBeVisible();
  releaseLoading();
  await expect(page.getByText(/Tu catálogo todavía no tiene importaciones/)).toBeVisible();
  await page.screenshot({ path: path.join(out, "06-vacio.png"), fullPage: false });
  await page.unroute("**/api/v1/catalog-imports/");
  await page.route("**/api/v1/catalog-imports/", async (route) => {
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: '{"error":{"detail":"No se pudo leer la fuente."}}',
    });
  });
  await page.getByRole("button", { name: "Cerrar importador", exact: true }).click();
  await page.getByRole("button", { name: "Importar catálogo", exact: true }).click();
  await expect(page.getByText("No se pudo leer la fuente.", { exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(out, "07-error.png"), fullPage: false });
  await page.unroute("**/api/v1/catalog-imports/");
  await page.getByRole("button", { name: "Cerrar importador", exact: true }).click();
  await page.getByRole("button", { name: "Importar catálogo", exact: true }).click();
  const row = page
    .locator(".catalog-import-entry")
    .filter({ hasText: "ficha-sintetica-d01.pdf" })
    .filter({ hasText: "Requiere revisión" })
    .first();
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Revisar fuente y cambios" }).click();
  await expect(page.getByText("Fuente del proveedor", { exact: true })).toBeVisible();
  await page.locator(".catalog-import-review").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(out, "01-ia-fuente.png"), fullPage: true });
  await page.getByRole("button", { name: "Comparar cambios", exact: true }).click();
  await expect(
    page.getByText(
      "Corrige los campos indicados o excluye sus filas. La publicación está bloqueada.",
      { exact: true },
    ),
  ).toBeVisible();
  await page.locator(".catalog-review-diff").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(out, "02-ia-errores-diff.png"), fullPage: true });
  if (await page.getByRole("button", { name: "Publicar catálogo revisado" }).count())
    throw new Error("Invalid source allowed publication");
  await page.getByRole("button", { name: "Cerrar revisión", exact: true }).click();
  for (const [theme, width, height] of [
    ["light", 1440, 900],
    ["dark", 1440, 900],
    ["light", 1280, 800],
    ["dark", 1280, 800],
    ["light", 1024, 768],
    ["dark", 1024, 768],
  ]) {
    await page.setViewportSize({ width, height });
    await page.evaluate((theme) => {
      localStorage.setItem("dekopen.theme", theme);
      document.documentElement.dataset.theme = theme;
    }, theme);
    await row.getByRole("button", { name: "Revisar fuente y cambios" }).click();
    await page.locator(".catalog-import-review").scrollIntoViewIfNeeded();
    await expect(page.getByText("Fuente del proveedor", { exact: true })).toBeVisible();
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1))
      throw new Error(`Overflow ${width} ${theme}`);
    await page.screenshot({
      path: path.join(out, `revision-${width}-${theme}.png`),
      fullPage: true,
    });
    await page.getByRole("button", { name: "Cerrar revisión", exact: true }).click();
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.evaluate(() => {
    document.documentElement.dataset.theme = "light";
    localStorage.setItem("dekopen.theme", "light");
  });
  const previousManual = page
    .locator(".catalog-import-entry")
    .filter({ hasText: "catalogo-nine-sheets.xlsx" })
    .filter({ hasText: "Publicado" });
  if (await previousManual.count()) {
    await previousManual
      .first()
      .getByRole("button", { name: "Deshacer publicación", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Deshacer publicación", exact: true })
      .click();
    await expect(previousManual).toHaveCount(0, { timeout: 30000 });
  }
  const python = existsSync(".venv/Scripts/python.exe")
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
  const fixture = path.resolve(".run/d01-browser-fixture.xlsx");
  const prepared = spawnSync(
    python,
    [
      "scripts/catalog_interchange_fixture.py",
      "--output",
      fixture,
      "--system-code",
      `REVISION-D01-${Date.now().toString(36)}`,
    ],
    { encoding: "utf8" },
  );
  if (prepared.status !== 0) throw new Error("Could not prepare the exact interchange fixture");
  await page.locator("input[type=file]").setInputFiles({
    name: "catalogo-nine-sheets.xlsx",
    mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    buffer: await readFile(fixture),
  });
  const manual = page
    .locator(".catalog-import-entry")
    .filter({ hasText: "catalogo-nine-sheets.xlsx" })
    .first();
  await expect(manual).toContainText("Requiere revisión", { timeout: 60000 });
  await manual.getByRole("button", { name: "Revisar fuente y cambios" }).click();
  await page.getByRole("button", { name: "Comparar cambios", exact: true }).click();
  const publish = page.getByRole("button", { name: "Publicar catálogo revisado", exact: true });
  await expect(publish).toBeDisabled();
  await page.locator(".catalog-review-attestation input").check();
  await expect(publish).toBeEnabled();
  const attestation = page.locator(".catalog-review-attestation");
  const attestationBox = await attestation.boundingBox();
  const attestationText = await attestation.locator("span").boundingBox();
  if (
    !attestationBox ||
    !attestationText ||
    attestationText.x + attestationText.width > attestationBox.x + attestationBox.width + 1
  )
    throw new Error("Publication review text is clipped");
  await page.locator(".catalog-review-diff").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(out, "05-manual-diff.png"), fullPage: false });
  await publish.click();
  await expect(manual).toContainText("Publicado", { timeout: 30000 });
  await manual.getByRole("button", { name: "Ver fuente", exact: true }).click();
  await page
    .locator(".catalog-sheet-tabs button")
    .filter({ hasText: /^Vidrios/ })
    .click();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar esta hoja CSV", exact: true }).click();
  await (await download).saveAs(path.join(out, "vidrios-exportados.csv"));
  await page.getByRole("button", { name: "Cerrar revisión", exact: true }).click();
  await manual.getByRole("button", { name: "Deshacer publicación", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Deshacer publicación", exact: true })
    .click();
  await expect(manual).toContainText("Publicación deshecha", { timeout: 30000 });
  await page.getByRole("button", { name: "Cerrar importador", exact: true }).click();
  await page
    .locator(".catalog-system")
    .filter({ hasText: "PVC practicable 60 mm · DEMO" })
    .filter({ hasNotText: "autoridad guardada" })
    .click();
  await page.screenshot({ path: path.join(out, "03-catalogo-demo.png"), fullPage: true });
  await page.goto(base + "/pricing/cost-lists");
  await page.locator(".pricing-demo-costs summary").click();
  await expect(page.locator(".pricing-demo-rows")).toBeVisible();
  await page.screenshot({ path: path.join(out, "04-precios-demo.png"), fullPage: true });
  const estimatorLogin = await fetch(`${sb}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: key, "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "demo-estimator@fixture.dekopen.local",
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!estimatorLogin.ok) throw new Error("Read-only fixture login failed");
  const estimatorSession = await estimatorLogin.json();
  const readOnly = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await readOnly.addInitScript(
    ({ session, sb, org }) => {
      localStorage.setItem(
        `sb-${new URL(sb).hostname.split(".")[0]}-auth-token`,
        JSON.stringify(session),
      );
      localStorage.setItem(`dekopen.active_org.${session.user.id}`, org);
    },
    { session: estimatorSession, sb, org },
  );
  const reader = await readOnly.newPage();
  await reader.goto(base + "/catalogs/systems");
  await reader.getByRole("button", { name: "Importar catálogo", exact: true }).click();
  await expect(reader.getByText(/Puedes consultar las importaciones/)).toBeVisible();
  await expect(reader.locator("input[type=file]")).toHaveCount(0);
  await expect(
    reader.getByRole("button", { name: "Publicar catálogo revisado", exact: true }),
  ).toHaveCount(0);
  await reader.screenshot({ path: path.join(out, "08-sin-permiso-publicar.png"), fullPage: false });
  await readOnly.close();
  await writeFile(
    path.join(out, "resultado.json"),
    JSON.stringify(
      {
        realAIReview: true,
        emptyAndLoadingStates: true,
        simulatedReadFailure: true,
        readOnlyRoleCannotUploadOrPublish: true,
        publicationBlockedByErrors: true,
        manualNineSheets: true,
        publicationRequiresReview: true,
        exportCSV: true,
        undo: true,
        viewports: 6,
        consoleErrors: errors,
      },
      null,
      2,
    ),
  );
  if (errors.length) throw new Error(errors.join("; "));
  console.log(
    "D01 real AI review, diff errors, six viewport/theme pairs and DEMO catalog/prices PASS",
  );
} finally {
  await browser.close();
  const deleted = await fetch(`${sb}/auth/v1/factors/${factor.id}`, {
    method: "DELETE",
    headers: { apikey: key, Authorization: `Bearer ${session.access_token}` },
  });
  if (!deleted.ok) throw new Error(`MFA cleanup ${deleted.status}`);
}

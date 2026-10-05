import { chromium, expect as baseExpect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { FIXTURE_USERS } from "./ux-capture/routes.ts";

const expect = baseExpect.configure({ timeout: 15_000 });
const baseURL = process.env.UX_CAPTURE_BASE_URL ?? "http://127.0.0.1:5173";
const authURL = process.env.SUPABASE_URL ?? "http://127.0.0.1:25321";
const apiURL = process.env.DJANGO_URL ?? "http://127.0.0.1:8000";
const key = process.env.SUPABASE_ANON_KEY ?? process.env.VITE_SUPABASE_ANON_KEY ?? "";
const org = "548b9ce5-746b-5a4a-9127-733c4dcd0582";
const out = path.resolve("docs/redesign/captures/sistema-diseno/validacion");
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const results: unknown[] = [];
try {
  for (const surface of ["catalogo", "cobranza"]) {
    const role = surface === "catalogo" ? "WORKSHOP_MANAGER" : "ESTIMATOR";
    const login = await fetch(`${authURL}/auth/v1/token?grant_type=password`, {
      method: "POST",
      headers: { apikey: key, "Content-Type": "application/json" },
      body: JSON.stringify(FIXTURE_USERS[role]),
    });
    if (!login.ok) throw new Error(`Fixture ${role}: HTTP ${login.status}`);
    const session = await login.json();
    let target = "/catalogs/systems";
    if (surface === "cobranza") {
      const projects = await fetch(`${apiURL}/api/v1/projects/`, {
        headers: { Authorization: `Bearer ${session.access_token}`, "X-Organization-ID": org },
      });
      if (!projects.ok) throw new Error(`Fixture projects: HTTP ${projects.status}`);
      const data = await projects.json();
      const project = data.items.find((row: { name: string }) =>
        row.name.includes("Vivienda demo"),
      );
      if (!project) throw new Error("Missing synthetic housing fixture");
      target = `/projects/${project.id}`;
    }
    for (const theme of ["light", "dark"]) {
      const context = await browser.newContext({
        baseURL,
        viewport: { width: 1440, height: 900 },
        reducedMotion: "reduce",
        storageState: {
          cookies: [],
          origins: [
            {
              origin: baseURL,
              localStorage: [
                {
                  name: `sb-${new URL(authURL).hostname.split(".")[0]}-auth-token`,
                  value: JSON.stringify(session),
                },
                { name: `dekopen.active_org.${session.user.id}`, value: org },
                { name: "dekopen.theme", value: theme },
              ],
            },
          ],
        },
      });
      const page = await context.newPage();
      const writes: string[] = [];
      page.on("request", (request) => {
        if (
          request.url().startsWith(`${apiURL}/api/v1/`) &&
          ["POST", "PUT", "PATCH", "DELETE"].includes(request.method())
        )
          writes.push(new URL(request.url()).pathname);
      });
      await page.goto(target);
      if (surface === "catalogo") {
        await page.getByRole("button", { name: "Crear serie", exact: true }).click();
        await page
          .locator(".catalog-editor")
          .getByRole("button", { name: "Guardar", exact: true })
          .click();
        await expect(page.locator(".catalog-editor [aria-invalid=true]").first()).toBeFocused();
      } else {
        await page
          .locator("summary")
          .filter({ hasText: /^Cobranza$/ })
          .click();
        await page.getByRole("button", { name: "Registrar pago", exact: true }).click();
        await page.getByRole("button", { name: "Guardar pago", exact: true }).click();
        await expect(page.locator("input[name=amount]")).toBeFocused();
        await page.locator("input[name=amount]").fill("12,5");
        await page.getByRole("button", { name: "Guardar pago", exact: true }).click();
        await expect(
          page.getByRole("alert").filter({ hasText: "hasta 0 decimales" }),
        ).toBeVisible();
      }
      const errors = page.getByRole("alert").filter({ hasText: "Revisa los campos indicados" });
      if (surface === "cobranza")
        await expect(
          page.locator("input[name=amount]").locator("..").locator("[data-validation-error]"),
        ).toBeInViewport();
      await expect(errors).toBeVisible();
      expect(
        await page
          .locator("form")
          .evaluateAll((forms) => forms.every((form) => (form as HTMLFormElement).noValidate)),
      ).toBe(true);
      expect(writes).toEqual([]);
      await page.screenshot({
        path: path.join(out, `${surface}-${theme}-1440.png`),
        fullPage: true,
      });
      results.push({
        surface,
        theme,
        nativeValidation: false,
        firstErrorFocused: true,
        writes: 0,
        result: "PASA",
      });
      await context.close();
      console.log(`Validación ${surface} ${theme}: PASA`);
    }
  }
} finally {
  await browser.close();
}
await writeFile(path.join(out, "results.json"), JSON.stringify(results, null, 2));

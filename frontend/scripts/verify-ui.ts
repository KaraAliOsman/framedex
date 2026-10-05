import { chromium, expect as baseExpect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
const expect = baseExpect.configure({ timeout: 15_000 });

const baseURL = process.env.UX_CAPTURE_BASE_URL ?? "http://127.0.0.1:5173";
const authURL = process.env.SUPABASE_URL ?? "http://127.0.0.1:25321";
const key = process.env.SUPABASE_ANON_KEY ?? process.env.VITE_SUPABASE_ANON_KEY ?? "";
const login = await fetch(`${authURL}/auth/v1/token?grant_type=password`, {
  method: "POST",
  headers: { apikey: key, "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "demo-estimator@fixture.dekopen.local",
    password: "Demo-Fixture-2026!",
  }),
});
if (!login.ok) throw new Error(`Fixture login failed (${login.status})`);
const session = await login.json();
const out = path.resolve("docs/redesign/captures/sistema-diseno/manual");
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
const records: unknown[] = [];
try {
  for (const theme of ["light", "dark"])
    for (const density of ["office", "workshop", "document"]) {
      for (const viewport of [
        { width: 1440, height: 900 },
        { width: 1280, height: 800 },
        { width: 1024, height: 768 },
        ...(density === "workshop" || density === "document" ? [{ width: 390, height: 844 }] : []),
      ]) {
        const context = await browser.newContext({
          baseURL,
          viewport,
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
                  {
                    name: `dekopen.active_org.${session.user.id}`,
                    value: "548b9ce5-746b-5a4a-9127-733c4dcd0582",
                  },
                  { name: "dekopen.theme", value: theme },
                ],
              },
            ],
          },
        });
        const page = await context.newPage();
        const errors: string[] = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.goto("/dev/ui");
        await expect(page.getByRole("heading", { name: "Manual de componentes" })).toBeVisible();
        await page
          .getByRole("radio", {
            name: { office: "Oficina", workshop: "Taller", document: "Documento" }[density]!,
            exact: true,
          })
          .click();
        await expect(page.getByLabel("Obra de referencia").locator("option")).not.toHaveCount(0);
        await page.evaluate(() => document.fonts.ready);
        const dimensions = page.locator(".ui-manual__sheet > div > .ui-value");
        await expect(dimensions).toHaveText(/\d.*×.*mm/);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth + 1,
        );
        expect(overflow, `${theme}/${density}/${viewport.width}: horizontal overflow`).toBe(false);
        const axe = await new AxeBuilder({ page }).analyze();
        const violations = axe.violations.filter(
          (issue) => issue.impact === "serious" || issue.impact === "critical",
        );
        await writeFile(
          path.join(out, `${theme}-${density}-${viewport.width}-axe.json`),
          JSON.stringify(violations, null, 2),
        );
        expect(violations, `axe ${theme}/${density}/${viewport.width}`).toEqual([]);
        await page.screenshot({
          path: path.join(out, `${theme}-${density}-${viewport.width}.png`),
          fullPage: true,
        });
        // Errors come from the Spanish form edge, never browser-native bubbles.
        await page.getByRole("button", { name: "Comprobar formato" }).click();
        await expect(
          page.getByRole("alert").filter({ hasText: "Revisa los campos indicados" }),
        ).toBeVisible();
        await expect(page.getByLabel("Nombre de muestra")).toBeFocused();
        const errorAxe = await new AxeBuilder({ page }).analyze();
        expect(
          errorAxe.violations.filter(
            (issue) => issue.impact === "serious" || issue.impact === "critical",
          ),
        ).toEqual([]);
        await page.getByLabel("Nombre de muestra").fill("Muestra del taller");
        await page.locator('input[name="dimension"]').fill("1249,5");
        await page.getByLabel("Monto en pesos").fill("2.400");
        await page.getByRole("button", { name: "Comprobar formato" }).click();
        await expect(page.getByRole("status").filter({ hasText: "Formato válido" })).toBeVisible();
        await page.getByRole("button", { name: "Abrir diálogo", exact: true }).click();
        await expect(page.getByRole("dialog")).toBeVisible();
        const modalAxe = await new AxeBuilder({ page }).analyze();
        expect(
          modalAxe.violations.filter(
            (issue) => issue.impact === "serious" || issue.impact === "critical",
          ),
        ).toEqual([]);
        await page.keyboard.press("Escape");
        await expect(
          page.getByRole("button", { name: "Abrir diálogo", exact: true }),
        ).toBeFocused();
        await page.keyboard.press("Control+k");
        await page.getByRole("combobox", { name: "Buscar comando" }).fill("Abrir ficha");
        await page.getByRole("combobox", { name: "Buscar comando" }).press("Enter");
        await expect(page.getByRole("dialog", { name: "Ficha de la obra" })).toBeVisible();
        await page.keyboard.press("Escape");
        await page.getByRole("tab", { name: "Bien / Mal" }).click();
        await expect(page.getByRole("heading", { name: "Todo compite" })).toBeVisible();
        await page.screenshot({
          path: path.join(out, `${theme}-${density}-${viewport.width}-bien-mal.png`),
          fullPage: true,
        });
        expect(errors).toEqual([]);
        records.push({
          theme,
          density,
          viewport,
          axe: "PASA",
          overflow,
          flow: "formulario español → diálogo → teclado → comando → ficha → Bien / Mal",
        });
        console.log(`Manual ${theme} ${density} ${viewport.width}: PASA`);
        await context.close();
      }
    }
} finally {
  await browser.close();
}
await writeFile(path.join(out, "results.json"), JSON.stringify(records, null, 2));

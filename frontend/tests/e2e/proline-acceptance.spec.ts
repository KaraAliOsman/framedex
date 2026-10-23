import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type TestInfo } from "@playwright/test";
import * as OTPAuth from "otpauth";

import { environment } from "./support/environment";
import { requireMailpitHealthy, waitForMagicLink } from "./support/mailpit";

/* P10 · Proline acceptance (F1). A workshop that does not exist yet signs up,
 * creates itself, chooses PRO6004 from the reference library and walks the
 * first use. The workshop's technical data and prices are synthetic and say
 * so; the library contributes identity only. Each step is timed. */

function local(name: string): string {
  const value = environment(name);
  if (!value) throw new Error(`${name} is required for the acceptance E2E`);
  const url = new URL(value);
  if (!["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))
    throw new Error("The acceptance runs only against the isolated local stack");
  return url.origin;
}

async function capture(page: Page, info: TestInfo, name: string): Promise<void> {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  expect(
    (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
      .violations,
  ).toEqual([]);
  const path = info.outputPath(`${name}-${page.viewportSize()!.width}.png`);
  await page.screenshot({ path, animations: "disabled" });
  await info.attach(name, { path, contentType: "image/png" });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Aceptación Proline ${viewport.width}`, () => {
    test.use({ viewport });
    test("a new workshop goes from sign-up to its first sent quote with PRO6004", async ({
      page,
    }, info) => {
      test.setTimeout(420_000);
      const supabaseUrl = local("SUPABASE_URL");
      const mailpit = local("MAILPIT_URL");
      await requireMailpitHealthy(mailpit);
      const email = `proline-${crypto.randomUUID()}@example.com`;
      const timings: { step: string; ms: number }[] = [];
      let mark = Date.now();
      const lap = (step: string): void => {
        const now = Date.now();
        timings.push({ step, ms: now - mark });
        mark = now;
      };

      // 1 · Sign-up: a magic link that creates the account.
      await page.goto("/login");
      await page.getByRole("link", { name: "Crea tu taller", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "Crea tu taller en DEKOPEN", exact: true }),
      ).toBeVisible();
      await capture(page, info, "f1-registro");
      await page.getByLabel("Correo", { exact: true }).fill(email);
      await page.getByRole("button", { name: "Enviar enlace de acceso", exact: true }).click();
      await expect(page.getByRole("status")).toContainText("Revisa tu correo para continuar");
      const message = await waitForMagicLink({ baseUrl: mailpit, supabaseUrl, recipient: email });
      await page.goto(message.link);
      lap("registro");

      // 2 · The workshop names itself (Chile, CLP, IVA 19 %).
      const workshop = page.getByTestId("create-workshop");
      await expect(workshop.getByText("19 %", { exact: true })).toBeVisible();
      await capture(page, info, "f1-taller");
      await workshop.getByLabel("Nombre del taller", { exact: true }).fill("Ventanas del Sur · ensayo");
      await workshop.getByRole("button", { name: "Crear mi taller", exact: true }).click();

      // 3 · The owner's second factor.
      await page.getByRole("button", { name: "Configurar autenticador", exact: true }).click();
      const secret = (await page.getByTestId("totp-secret").textContent())?.trim() ?? "";
      const totp = new OTPAuth.TOTP({
        algorithm: "SHA1",
        digits: 6,
        period: 30,
        secret: OTPAuth.Secret.fromBase32(secret),
      });
      await page.getByLabel("Código de seis dígitos").fill(totp.generate());
      await page.getByRole("button", { name: "Verificar", exact: true }).click();
      await expect(page.getByTestId("app-shell")).toBeVisible();
      lap("taller-y-segundo-factor");

      // 4 · Hoy points a workshop without series to its first use.
      await expect(page.getByRole("heading", { name: "Prepara tu taller", exact: true })).toBeVisible();
      await capture(page, info, "f1-hoy");
      await page.getByRole("link", { name: "Empezar", exact: true }).click();

      // 5 · Company: legal identity, commercial terms and documents.
      await expect(page.getByRole("heading", { name: "Prepara tu empresa", exact: true })).toBeVisible();
      await page.getByLabel("RUT legal", { exact: true }).fill("76.123.456-0");
      await page.getByRole("button", { name: "Guardar empresa", exact: true }).click();
      await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
      await capture(page, info, "f1-empresa");
      await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
      await page.getByRole("button", { name: "Guardar condiciones", exact: true }).click();
      await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
      await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
      await page.getByRole("button", { name: "Guardar documentos", exact: true }).click();
      await page.getByRole("dialog").getByRole("button", { name: "Confirmar", exact: true }).click();
      await page.getByRole("button", { name: "Crear primer proyecto", exact: true }).click();
      lap("empresa");

      // 6 · First use: PRO6004 from the reference library.
      const library = page.getByRole("region", { name: "Tu serie del fabricante", exact: true });
      await expect(library).toBeVisible();
      await capture(page, info, "f1-biblioteca");
      await library.getByRole("link", { name: /PRO6004/ }).click();
      const create = page.getByRole("dialog", { name: "Desde una plantilla", exact: true });
      await expect(create.getByLabel("Fabricante", { exact: true })).toHaveValue("Proline");
      await expect(create.getByLabel("Código", { exact: true })).toHaveValue("PRO6004");
      await capture(page, info, "f1-serie");
      await create.getByRole("button", { name: "Crear serie", exact: true }).click();
      const wizard = page.getByRole("dialog", { name: "Preparar mi serie", exact: true });
      await expect(
        wizard.getByRole("button", { name: "Paso 1: Serie", exact: true }),
      ).toHaveAttribute("aria-current", "step");
      lap("serie");

      console.info(JSON.stringify({ surface: "proline-acceptance", viewport, timings }));
      await info.attach("tiempos", {
        body: JSON.stringify(timings, null, 2),
        contentType: "application/json",
      });
    });
  });
}

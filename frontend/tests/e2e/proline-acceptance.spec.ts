import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type TestInfo } from "@playwright/test";
import { fileURLToPath } from "node:url";
import * as OTPAuth from "otpauth";

import { environment, santiagoToday } from "./support/environment";
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

/** Synthetic workshop files: `scripts/catalog_interchange_fixture.py --system-code
 * PRO6004 --openings --rename …` (see the fixture README) and a price sheet. */
function fixture(name: string): string {
  return fileURLToPath(new URL(`./fixtures/${name}`, import.meta.url));
}

/** The quote link as the client receives it: the sandbox mail to their address. */
async function quoteLinkFor(mailpit: string, recipient: string): Promise<string> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    const listing = (await (await fetch(`${mailpit}/api/v1/messages`)).json()) as {
      messages: { ID: string; To: { Address: string }[] }[];
    };
    const message = listing.messages.find((item) =>
      item.To.some((to) => to.Address.toLowerCase() === recipient),
    );
    if (message) {
      const body = (await (await fetch(`${mailpit}/api/v1/message/${message.ID}`)).json()) as {
        HTML?: string;
        Text?: string;
      };
      const content = `${body.HTML ?? ""}
${body.Text ?? ""}`.replaceAll("&amp;", "&");
      const link = (content.match(/https?:\/\/[^\s"'<>]+/g) ?? []).find((url) =>
        new URL(url).pathname.startsWith("/cotizacion/"),
      );
      if (link) return link;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("The quote link did not reach the client's sandbox mailbox");
}

async function capture(page: Page, info: TestInfo, name: string): Promise<void> {
  // The setup wizard disables its body while it saves; capture it settled.
  const wizard = page.getByRole("dialog", { name: "Preparar mi serie", exact: true });
  if (await wizard.isVisible())
    await expect(
      wizard.getByRole("button", { name: "Volver a la ficha", exact: true }),
    ).toBeEnabled();
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
    test.use({ viewport, contextOptions: { reducedMotion: "reduce" } });
    test("a new workshop goes from sign-up to its first sent quote with PRO6004", async ({
      page,
      browser,
    }, info) => {
      test.setTimeout(420_000);
      const supabaseUrl = local("SUPABASE_URL");
      const mailpit = local("MAILPIT_URL");
      await requireMailpitHealthy(mailpit);
      const run = crypto.randomUUID();
      const email = `proline-${run}@example.com`;
      const client = `rodrigo-${run}@example.com`;
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
      await workshop
        .getByLabel("Nombre del taller", { exact: true })
        .fill("Ventanas del Sur · ensayo");
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
      await expect(
        page.getByRole("heading", { name: "Prepara tu taller", exact: true }),
      ).toBeVisible();
      await capture(page, info, "f1-hoy");
      await page.getByRole("link", { name: "Empezar", exact: true }).click();

      // 5 · Company: legal identity, commercial terms and documents.
      await expect(
        page.getByRole("heading", { name: "Prepara tu empresa", exact: true }),
      ).toBeVisible();
      await page.getByLabel("RUT legal", { exact: true }).fill("76.123.456-0");
      await page.getByRole("button", { name: "Guardar empresa", exact: true }).click();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Confirmar", exact: true })
        .click();
      await expect(
        page.getByRole("button", { name: "Confirmar y continuar", exact: true }),
      ).toBeEnabled();
      await capture(page, info, "f1-empresa");
      await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
      // The workshop's standing terms; every quote starts from them.
      await expect(
        page.getByLabel("Vigencia comercial para cotizaciones nuevas (días)", { exact: true }),
      ).not.toHaveValue("");
      await page.getByText("Plazo, instalación y condiciones legales", { exact: true }).click();
      for (const [label, text] of [
        ["Plazo de entrega", "15 días hábiles desde la aprobación y el pago del anticipo."],
        ["Instalación", "Incluye instalación y sellado en obra dentro de Temuco."],
        ["Exclusiones", "No incluye obras civiles, retiro de ventanas existentes ni andamios."],
        ["Garantía", "12 meses por defectos de fabricación e instalación."],
      ] as const)
        await page.getByLabel(label, { exact: true }).fill(text);
      await page.getByRole("button", { name: "Guardar condiciones", exact: true }).click();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Confirmar", exact: true })
        .click();
      await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
      await page.getByRole("button", { name: "Guardar documentos", exact: true }).click();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Confirmar", exact: true })
        .click();
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

      // 7 · The workshop's technical sheet through the official template.
      await wizard.getByRole("button", { name: "Continuar a Manual", exact: true }).click();
      await wizard
        .getByLabel("Archivo del catálogo", { exact: true })
        .setInputFiles(fixture("p10-pro6004-ficha-sintetica.xlsx"));
      await wizard.getByRole("button", { name: "Comparar cambios", exact: true }).click();
      await wizard.getByRole("checkbox", { name: /Revisé la referencia y los cambios/ }).check();
      await capture(page, info, "f1-manual");
      await wizard.getByRole("button", { name: "Publicar catálogo revisado", exact: true }).click();
      // Publishing every reviewed row of the sheet is one durable job.
      await expect(wizard.getByText(/Publicación completa:/)).toBeVisible({ timeout: 90_000 });
      lap("ficha-tecnica");

      // 8 · Purchase prices from the workshop's own sheet.
      await wizard.getByRole("button", { name: "Continuar a Precios", exact: true }).click();
      await wizard
        .getByLabel("Archivo de precios", { exact: true })
        .setInputFiles(fixture("p10-pro6004-precios-sinteticos.xlsx"));
      await expect(wizard.getByText(/hoja Precios de ensayo · 19 filas/)).toBeVisible();
      await wizard.getByRole("button", { name: "Crear una lista nueva", exact: true }).click();
      await wizard.getByLabel("Proveedor", { exact: true }).fill("Proline · lista de ensayo");
      await wizard.getByLabel("Vigente desde", { exact: true }).fill(santiagoToday());
      await wizard.getByRole("button", { name: "Crear lista", exact: true }).click();
      await wizard.getByRole("button", { name: "Revisar todos los precios", exact: true }).click();
      await capture(page, info, "f1-precios");
      await wizard
        .getByRole("button", { name: "Confirmar y guardar precios", exact: true })
        .click();
      await expect(
        wizard.getByRole("heading", { name: "Precios guardados", exact: true }),
      ).toBeVisible({ timeout: 30_000 });
      lap("precios");

      // 9 · A trial window checked against the manual.
      await wizard
        .getByRole("button", { name: "Continuar a Ventana de prueba", exact: true })
        .click();
      await wizard.getByRole("button", { name: "Calcular ventana", exact: true }).click();
      // The synthetic sheet is this workshop's manual: 1 200 mm + 2 × 3 mm of weld.
      await wizard
        .getByRole("textbox", { name: /Marco · PRO6004-ENSAYO-MARCO · largo 1 según tu manual/ })
        .fill("1206,00");
      await wizard.getByRole("button", { name: "Comparar medidas", exact: true }).click();
      await expect(wizard.getByText("Coincide", { exact: true })).toBeVisible();
      await wizard
        .getByRole("region", { name: "Despiece de la ventana de prueba", exact: true })
        .scrollIntoViewIfNeeded();
      await capture(page, info, "f1-ventana");
      await wizard.getByRole("checkbox", { name: /He revisado el despiece completo/ }).check();
      // Only template values still «sugeridos» need this; the sheet replaced them.
      const suggested = wizard.getByRole("checkbox", { name: /Confirmo como datos del taller/ });
      if (await suggested.count()) await suggested.check();
      await wizard
        .getByRole("button", { name: "Confirmar ventana de prueba", exact: true })
        .click();
      const first = wizard.getByRole("button", {
        name: "Crear mi primera cotización",
        exact: true,
      });
      await expect(first).toBeEnabled({ timeout: 30_000 });
      lap("ventana-de-prueba");

      // 10 · The first work, with PRO6004 as its series.
      await first.click();
      await page.getByLabel("Nombre del proyecto", { exact: true }).fill("Casa Rodrigo · ensayo");
      await page.getByRole("button", { name: "Guardar", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "Nombre de la obra", exact: true }),
      ).toContainText("Casa Rodrigo · ensayo");
      lap("obra");

      // 11 · Three windows, each priced by the engine with PRO6004.
      const work = new URL(page.url()).pathname;
      for (const [starter, place] of [
        ["Fijo · Ventanal fijo de una pieza", "Living · fijo"],
        ["Una hoja · Oscilobatiente de una hoja", "Dormitorio · una hoja"],
        ["Fijo · Ventanal fijo de una pieza", "Baño · fijo"],
      ] as const) {
        await page.getByRole("link", { name: "Añadir ventana", exact: true }).first().click();
        await page.getByRole("button", { name: starter, exact: true }).click();
        await page.getByLabel("Ubicación de la ventana", { exact: true }).fill(place);
        // Below 1280 px the inspector is a sheet, closed by default.
        if (viewport.width < 1280)
          await page.getByRole("button", { name: "Inspector", exact: true }).click();
        await page
          .getByRole("combobox", { name: "Vidrio", exact: true })
          .selectOption({ label: "4-16-4 Float Incoloro" });
        if (viewport.width < 1280)
          await page.getByRole("button", { name: "Cerrar inspector", exact: true }).click();
        const save = page.getByRole("button", { name: "Guardar", exact: true });
        await expect(save).toBeEnabled({ timeout: 30_000 });
        await save.click();
        await expect(page).toHaveURL(
          (url) => url.pathname === work && url.searchParams.has("position"),
        );
      }
      await capture(page, info, "f1-obra");
      lap("tres-ventanas");

      // 12 · Issue the quote and send its link.
      await page.getByRole("button", { name: "Enviar cotización", exact: true }).click();
      await page.getByLabel("Cliente", { exact: true }).fill("Rodrigo Soto · cliente de ensayo");
      await page.getByLabel("RUT del cliente", { exact: true }).fill("11.111.111-1");
      await page.getByLabel("Correo del cliente", { exact: true }).fill(client);
      await page.getByLabel("Dirección de obra", { exact: true }).fill("Los Aromos 123, Temuco");
      await page.getByRole("button", { name: "Preparar emisión", exact: true }).click();
      await page
        .getByLabel("Condiciones de pago", { exact: true })
        .fill("50 % al aprobar y 50 % contra entrega.");
      await page.getByRole("button", { name: "Preparar PDF para revisar", exact: true }).click();
      await expect(page.getByText(/PDF preparado/)).toBeVisible({ timeout: 30_000 });
      await capture(page, info, "f1-cotizacion");
      await page
        .getByRole("checkbox", {
          name: "Revisé este PDF, el destinatario y las condiciones de emisión",
        })
        .check();
      await page.getByRole("button", { name: "Emitir y enviar al cliente", exact: true }).click();
      await expect(page.getByRole("button", { name: "Copiar enlace", exact: true })).toBeVisible({
        timeout: 60_000,
      });
      lap("emision-y-envio");

      // 13 · The client opens the link from their mail and approves.
      const link = await quoteLinkFor(mailpit, client);
      const visitor = await browser.newContext({ viewport, reducedMotion: "reduce" });
      const portal = await visitor.newPage();
      await portal.goto(link);
      await expect(portal.getByRole("heading", { name: "Casa Rodrigo · ensayo" })).toBeVisible();
      await capture(portal, info, "f1-portal");
      const decision = portal.getByRole("region", { name: "Decidir propuesta", exact: true });
      await decision.getByLabel("Nombre completo", { exact: true }).fill("Rodrigo Soto");
      await decision.getByLabel("RUT", { exact: true }).fill("11.111.111-1");
      await decision.getByRole("checkbox").first().check();
      await decision.getByRole("button", { name: "Aprobar propuesta", exact: true }).click();
      await expect(portal.getByText("Propuesta aprobada").first()).toBeVisible({ timeout: 30_000 });
      await portal.getByText("Propuesta aprobada").first().scrollIntoViewIfNeeded();
      await capture(portal, info, "f1-aprobada");
      await visitor.close();
      lap("aprobacion-del-cliente");
      expect(timings.reduce((total, item) => total + item.ms, 0)).toBeLessThan(420_000);

      console.info(JSON.stringify({ surface: "proline-acceptance", viewport, timings }));
      await info.attach("tiempos", {
        body: JSON.stringify(timings, null, 2),
        contentType: "application/json",
      });
    });
  });
}

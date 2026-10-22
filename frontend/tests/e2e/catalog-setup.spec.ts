import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import { fileURLToPath } from "node:url";
import { test } from "./support/catalog-series-fixture";

async function capture(page: Page, info: TestInfo, name: string) {
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
  test.describe(`Alta reanudable ${viewport.width}`, () => {
    test.use({ viewport, doubleReadManual: true, lightCatalog: true, unpricedCatalog: true });
    test("resumes five steps, preserves drafts and creates a work whose first window inherits the selected series", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(240_000);
      const start = Date.now();
      await page.goto(`/catalogs/systems?system=${catalog.systemId}`);
      await page.getByRole("tab", { name: "Reglas", exact: true }).click();
      const inputs = page
        .getByRole("grid", { name: "Reglas", exact: true })
        .locator("input[data-cell]:not([readonly])");
      for (let index = 0; index < 5; index++)
        await inputs.nth(index).fill((catalog.pasteValues[index] ?? "").replace(".", ","));
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      await expect(page.getByText("Lista para dibujar", { exact: true })).toBeVisible();
      const wizardStart = Date.now();
      await page.getByRole("button", { name: "Continuar alta", exact: true }).click();
      const wizard = page.getByRole("dialog", { name: "Preparar mi serie", exact: true });
      await expect(
        wizard.getByRole("button", { name: "Paso 1: Serie", exact: true }),
      ).toHaveAttribute("aria-current", "step");
      console.info(
        JSON.stringify({
          surface: "series-setup",
          viewport,
          readyMs: Date.now() - start,
          wizardMs: Date.now() - wizardStart,
        }),
      );
      await capture(page, info, "alta-serie");
      await wizard.getByRole("button", { name: "Continuar a Manual", exact: true }).click();
      await wizard
        .getByRole("button", { name: "Revisar referencia y cambios", exact: true })
        .click();
      const review = wizard.getByRole("region", { name: "Diferencias entre las dos lecturas" });
      await review.getByRole("button", { name: "Usar lectura 1", exact: true }).click();
      await review.getByRole("checkbox").check();
      await wizard.getByRole("button", { name: "Continuar a Precios", exact: true }).click();
      await expect(
        wizard.getByRole("heading", { name: "Agrega el manual de tu serie", includeHidden: true }),
      ).toBeHidden();
      await wizard.getByRole("button", { name: "Paso 2: Manual", exact: true }).click();
      await expect(review.getByRole("checkbox")).toBeChecked();
      await expect(review.getByRole("textbox")).toHaveValue("3.00");
      await wizard.getByRole("button", { name: "Comparar cambios", exact: true }).click();
      await wizard.getByRole("checkbox", { name: /Revisé la referencia y los cambios/ }).check();
      await wizard.getByRole("button", { name: "Publicar catálogo revisado", exact: true }).click();
      await expect(wizard.getByText(/Publicación completa:/)).toBeVisible();
      await capture(page, info, "alta-manual");
      await wizard.getByRole("button", { name: "Paso 3: Precios", exact: true }).click();
      await wizard
        .getByLabel("Archivo de precios", { exact: true })
        .setInputFiles(
          fileURLToPath(new URL("./fixtures/p03-alta-precios-sinteticos.xlsx", import.meta.url)),
        );
      await expect(wizard.getByText(/hoja Precios de prueba · 12 filas/)).toBeVisible();
      // Going back keeps the actual File, mapping and selection mounted.
      await wizard.getByRole("button", { name: "Paso 2: Manual", exact: true }).click();
      await wizard.getByRole("button", { name: "Paso 3: Precios", exact: true }).click();
      await expect(wizard.getByText(/hoja Precios de prueba · 12 filas/)).toBeVisible();
      await wizard.getByRole("button", { name: "Crear una lista nueva", exact: true }).click();
      await wizard.getByLabel("Proveedor", { exact: true }).fill("Proveedor de ensayo sintético");
      await wizard
        .getByLabel("Vigente desde", { exact: true })
        .fill(new Date().toISOString().slice(0, 10));
      await wizard.getByRole("button", { name: "Crear lista", exact: true }).click();
      await wizard.getByRole("button", { name: "Revisar todos los precios", exact: true }).click();
      await wizard
        .getByRole("button", { name: "Confirmar y guardar precios", exact: true })
        .click();
      await expect(
        wizard.getByRole("heading", { name: "Precios guardados", exact: true }),
      ).toBeVisible();
      await capture(page, info, "alta-precios");
      await wizard
        .getByRole("button", { name: "Continuar a Ventana de prueba", exact: true })
        .click();
      await wizard.getByRole("button", { name: "Volver a la ficha", exact: true }).click();
      await page.getByRole("button", { name: "Continuar alta", exact: true }).click();
      await expect(
        wizard.getByRole("button", { name: "Paso 4: Ventana de prueba", exact: true }),
      ).toHaveAttribute("aria-current", "step");
      await wizard.getByRole("button", { name: "Calcular ventana", exact: true }).click();
      await wizard
        .getByRole("textbox", { name: /Marco · PRO-F · largo 1 según tu manual/ })
        .fill("1208,00");
      await wizard.getByRole("button", { name: "Comparar medidas", exact: true }).click();
      await wizard.getByRole("button", { name: "Ajustar regla", exact: true }).click();
      await wizard.getByRole("radio", { name: /Adición de soldadura por extremo/ }).check();
      await wizard.getByRole("button", { name: "Aplicar y recalcular", exact: true }).click();
      await expect(wizard.getByText("Coincide", { exact: true })).toBeVisible();
      await wizard
        .getByRole("region", { name: "Despiece de la ventana de prueba", exact: true })
        .scrollIntoViewIfNeeded();
      await capture(page, info, "alta-ventana");
      await wizard.getByRole("checkbox", { name: /He revisado el despiece completo/ }).check();
      await wizard.getByRole("checkbox", { name: /Confirmo como datos del taller/ }).check();
      const verified = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname.endsWith("/trial/verify/") &&
          response.request().method() === "POST",
      );
      await wizard
        .getByRole("button", { name: "Confirmar ventana de prueba", exact: true })
        .click();
      const verifiedResponse = await verified;
      expect(verifiedResponse.status()).toBe(201);
      const headers = await verifiedResponse.request().allHeaders();
      await expect(
        wizard.getByRole("button", { name: "Crear mi primera cotización", exact: true }),
      ).toBeEnabled();
      const golden = await page.request.get(
        `/api/v1/catalogs/series/${catalog.systemId}/references/`,
        {
          headers: {
            Authorization: headers.authorization!,
            "X-Organization-ID": catalog.organizationId,
          },
        },
      );
      expect(golden.ok()).toBe(true);
      const references = (await golden.json()).items;
      expect(references).toHaveLength(1);
      expect(references[0].expected_output.profile_cuts[0].length_mm).toBe("1208.00");
      const finalSheet = await page.request.get(`/api/v1/catalogs/series/${catalog.systemId}/`, {
        headers: {
          Authorization: headers.authorization!,
          "X-Organization-ID": catalog.organizationId,
        },
      });
      expect(finalSheet.ok()).toBe(true);
      const usage = (await finalSheet.json()).usage;
      expect(usage).toMatchObject({ verified: true, suggested_count: 0 });
      expect(usage.levels).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ level: "QUOTABLE", ok: true }),
          expect.objectContaining({ level: "MANUFACTURABLE", ok: true }),
        ]),
      );
      await wizard
        .getByRole("button", { name: "Crear mi primera cotización", exact: true })
        .scrollIntoViewIfNeeded();
      await capture(page, info, "alta-cotizacion");
      await wizard
        .getByRole("button", { name: "Crear mi primera cotización", exact: true })
        .click();
      await expect(
        page.getByRole("combobox", { name: "Serie inicial para las ventanas", exact: true }),
      ).toHaveValue(catalog.systemId);
      await page.getByLabel("Nombre del proyecto", { exact: true }).fill("Primera obra sintética");
      const created = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === "/api/v1/projects/" &&
          response.request().method() === "POST",
      );
      await page.getByRole("button", { name: "Guardar", exact: true }).click();
      const createdResponse = await created;
      expect(createdResponse.status()).toBe(201);
      const work = await createdResponse.json();
      expect(work.design_defaults.system_id).toBe(catalog.systemId);
      await expect(
        page.getByRole("heading", { name: "Nombre de la obra", exact: true }),
      ).toContainText("Primera obra sintética");
      // The empty state repeats the same action; use the section toolbar.
      await page.getByRole("link", { name: "Añadir ventana", exact: true }).first().click();
      // Below 1280 px the series lives in the inspector sheet, closed by default.
      if (viewport.width < 1280)
        await page.getByRole("button", { name: "Inspector", exact: true }).click();
      await page.getByRole("button", { name: "PRO6004 · ensayo sintético", exact: true }).click();
      await expect(
        page.getByRole("combobox", { name: "Serie de perfiles", exact: true }),
      ).toHaveValue(catalog.systemId);
      await page.keyboard.press("Escape");
      await capture(page, info, "alta-primera-ventana");
    });
  });
}

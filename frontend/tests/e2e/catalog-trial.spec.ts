import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  expect(
    (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
      .violations,
  ).toEqual([]);
  if (name === "prueba-ajuste")
    await page
      .getByRole("region", { name: "Ajustes propuestos", exact: true })
      .scrollIntoViewIfNeeded();
  if (name === "prueba-verificada")
    await page.getByRole("status").filter({ hasText: "Prueba guardada" }).scrollIntoViewIfNeeded();
  for (const button of await page.locator(".ui-dialog__footer button").all()) {
    const bounds = (await button.boundingBox())!;
    expect(bounds.x).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(page.viewportSize()!.width);
    expect(bounds.y + bounds.height).toBeLessThanOrEqual(page.viewportSize()!.height);
  }
  const path = info.outputPath(`${name}-${page.viewportSize()!.width}.png`);
  await page.screenshot({ path, animations: "disabled" });
  await info.attach(name, { path, contentType: "image/png" });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Prueba de serie ${viewport.width}`, () => {
    test.use({ viewport });
    test("exact correction, verification and protected future edits", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      await page.goto(`/catalogs/systems?system=${catalog.systemId}`);
      await page.getByRole("tab", { name: "Reglas", exact: true }).click();
      const rules = page.getByRole("grid", { name: "Reglas", exact: true });
      const inputs = rules.locator("input[data-cell]:not([readonly])");
      for (let index = 0; index < 5; index++)
        await inputs.nth(index).fill((catalog.pasteValues[index] ?? "").replace(".", ","));
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      await expect(page.getByText("Lista para cotizar", { exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Ventana de prueba", exact: true }).click();
      const trial = page.getByRole("dialog", { name: "Ventana de prueba", exact: true });
      await trial.getByRole("button", { name: "Calcular ventana", exact: true }).click();
      const manual = trial.getByRole("textbox", {
        name: /Marco · PRO-F · largo 1 según tu manual/,
      });
      await manual.fill("1208,00");
      await trial.getByRole("button", { name: "Comparar medidas", exact: true }).click();
      await expect(trial.getByText("2 mm de diferencia", { exact: true })).toBeVisible();
      await capture(page, info, "prueba-diferencia");
      await trial.getByRole("button", { name: "Ajustar regla", exact: true }).click();
      await trial.getByRole("radio", { name: /Adición de soldadura por extremo/ }).check();
      await capture(page, info, "prueba-ajuste");
      await trial.getByRole("button", { name: "Aplicar y recalcular", exact: true }).click();
      await expect(trial.getByText("Coincide", { exact: true })).toBeVisible();
      await trial.getByRole("checkbox", { name: /He revisado el despiece completo/ }).check();
      await trial.getByRole("checkbox", { name: /Confirmo como datos del taller/ }).check();
      const refreshedSheet = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === `/api/v1/catalogs/series/${catalog.systemId}/` &&
          response.request().method() === "GET",
      );
      const verified = page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          new URL(response.url()).pathname.endsWith("/trial/verify/"),
      );
      await trial.getByRole("button", { name: "Confirmar ventana de prueba", exact: true }).click();
      expect((await verified).status()).toBe(201);
      const refreshed = await refreshedSheet;
      const usage = (await refreshed.json()).usage;
      expect(usage.verified).toBe(true);
      expect(
        usage.levels.find((level: { level: string }) => level.level === "MANUFACTURABLE").ok,
      ).toBe(true);
      await expect(trial.getByRole("status").filter({ hasText: "Prueba guardada" })).toBeVisible();
      await capture(page, info, "prueba-verificada");
      await trial.getByRole("button", { name: "Cerrar", exact: true }).click();
      await expect(page.getByText(/^Lista para (fabricar|máquina)$/)).toBeVisible();

      await page.getByRole("tab", { name: "Reglas", exact: true }).click();
      await inputs.first().fill("9,00");
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      const review = page.getByRole("dialog", {
        name: "Esta edición cambia tu ventana de prueba",
        exact: true,
      });
      await expect(review.getByRole("columnheader", { name: "Antes · mm" })).toBeVisible();
      await capture(page, info, "prueba-edicion-protegida");
      await review.getByRole("button", { name: "Conservar mi borrador", exact: true }).click();
      await expect(inputs.first()).toHaveValue("9,00");
      await expect(page.getByText(/^Lista para (fabricar|máquina)$/)).toBeVisible();
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      await review
        .getByRole("button", { name: "Guardar cambio y volver a verificar", exact: true })
        .click();
      await expect(
        page.getByText("Verifica una ventana de prueba antes de fabricar.", { exact: true }),
      ).toBeVisible();
      await expect(page.getByText("Lista para cotizar", { exact: true })).toBeVisible();
    });
  });
}

import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";

import { test } from "./support/catalog-series-fixture";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  const a11y = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(a11y.violations).toEqual([]);
  const path = info.outputPath(`${name}-${page.viewportSize()!.width}.png`);
  await page.screenshot({ path, animations: "disabled" });
  await info.attach(name, { path, contentType: "image/png" });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Ficha de serie ${viewport.width}`, () => {
    test.use({ viewport });
    test("PRO6004 clipboard, confirmation, exact prices and six tabs", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      const homeStarted = Date.now();
      await page.goto("/catalogs/systems");
      await expect(page.getByRole("heading", { name: "Catálogo", exact: true })).toBeVisible();
      await expect(page.getByRole("button", { name: /PRO6004 · ensayo sintético/ })).toBeVisible();
      console.info(
        JSON.stringify({ viewport, surface: "catalog", loadMs: Date.now() - homeStarted }),
      );
      await expect(page.locator(".series-catalog__examples")).not.toHaveAttribute("open");
      await capture(page, info, "catalogo");
      const started = Date.now();
      await page.getByRole("button", { name: /PRO6004 · ensayo sintético/ }).click();
      await expect(
        page.getByRole("heading", { name: "PRO6004 · ensayo sintético", exact: true }),
      ).toBeVisible();
      console.info(JSON.stringify({ viewport, surface: "sheet", loadMs: Date.now() - started }));
      await expect(page.getByText("Lista para dibujar", { exact: true })).toBeVisible();
      await page.getByRole("tab", { name: "Reglas", exact: true }).click();
      const grid = page.getByRole("grid", { name: "Reglas", exact: true });
      const inputs = grid.locator("input[data-cell]:not([readonly])");
      const values = catalog.pasteValues.map((value) => (value ?? "").replace(".", ","));
      await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
      await page.evaluate((text) => navigator.clipboard.writeText(text), values.join("\n"));
      await inputs.first().focus();
      await inputs.first().press("Control+v");
      for (let index = 0; index < 5; index++)
        await expect(inputs.nth(index)).toHaveValue(values[index]!);
      const saved = page.waitForResponse(
        (response) =>
          response.request().method() === "PATCH" &&
          new URL(response.url()).pathname === `/api/v1/catalogs/series/${catalog.systemId}/cells/`,
      );
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      const update = await saved;
      expect(update.status()).toBe(200);
      const updated = (await update.json()) as {
        usage: { level: string; suggested_count: number };
      };
      expect(updated.usage.level).toBe("QUOTABLE");
      await expect(page.getByText("Lista para cotizar", { exact: true })).toBeVisible();
      const selected = grid.getByRole("checkbox");
      await selected.nth(0).check();
      await selected.nth(1).check();
      const confirmed = page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          new URL(response.url()).pathname ===
            `/api/v1/catalogs/series/${catalog.systemId}/confirm/`,
      );
      await page.getByRole("button", { name: "Confirmar 2 valores", exact: true }).click();
      const confirm = await confirmed;
      expect(confirm.status()).toBe(200);
      const changed = (await confirm.json()) as { usage: { suggested_count: number } };
      expect(changed.usage.suggested_count).toBe(updated.usage.suggested_count - 2);
      await expect(page.locator(".series-sheet__pending")).toContainText(
        `${changed.usage.suggested_count} valores sugeridos`,
      );
      // The full flow above stays on the same document: no reload or mocked API.
      for (const [name, file] of [
        ["Perfiles", "perfiles"],
        ["Reglas", "reglas"],
        ["Herrajes", "herrajes"],
        ["Vidrios y colores", "vidrios-colores"],
        ["Tipologías", "tipologias"],
        ["Precios", "precios"],
      ]) {
        await page.getByRole("tab", { name, exact: true }).click();
        await capture(page, info, `serie-${file}`);
        if (name === "Tipologías") {
          await expect(
            page.getByRole("rowheader", { name: "Abatible izquierda", exact: true }),
          ).toBeVisible();
          await expect(
            page.getByRole("rowheader", { name: "Abatible derecha", exact: true }),
          ).toBeVisible();
        }
        if (name === "Reglas" && viewport.width === 390) {
          await page
            .getByRole("grid", { name: "Reglas", exact: true })
            .locator("input[data-cell]:not([readonly])")
            .first()
            .scrollIntoViewIfNeeded();
          await capture(page, info, "serie-reglas-valores");
          await page.locator(".ui-editable-table__scroll").evaluate((element) => {
            element.scrollLeft = 0;
          });
        }
      }
      const price = page
        .getByRole("grid", { name: "Precios de la serie" })
        .locator("input:not([readonly])")
        .first();
      await price.fill("1234,5678");
      const priced = page.waitForResponse(
        (response) =>
          response.request().method() === "PATCH" &&
          new URL(response.url()).pathname.endsWith("/prices/"),
      );
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      const costResponse = await priced;
      expect(costResponse.status()).toBe(200);
      await expect(price).toHaveValue("1234,5678");
      await page
        .getByRole("button", { name: /Historial de/ })
        .first()
        .click();
      await expect(page.getByRole("dialog")).toContainText("1234,5678");
      await page.getByRole("button", { name: "Cerrar", exact: true }).click();
      await page.getByRole("button", { name: "Deshacer", exact: true }).click();
      await expect(page.locator(".ui-editable-table__status")).toHaveText("Guardado");
      await expect(price).not.toHaveValue("1234,5678");

      await page.getByRole("button", { name: "Ventana de prueba", exact: true }).click();
      const trial = page.getByRole("dialog", { name: "Ventana de prueba" });
      await expect(trial.getByRole("combobox", { name: "Apertura", exact: true })).toBeVisible();
      await trial
        .getByRole("combobox", { name: "Apertura", exact: true })
        .selectOption("TURN_LEFT");
      const calculated = page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          new URL(response.url()).pathname === "/api/v1/engine/calculate/",
      );
      await trial.getByRole("button", { name: "Calcular ventana", exact: true }).click();
      expect((await calculated).status()).toBe(200);
      await expect(trial.getByRole("heading", { name: "Despiece calculado" })).toBeVisible();
      await expect(trial.getByText(/PRO-F:/).first()).toBeVisible();
      await capture(page, info, "ventana-prueba");
      await trial.getByRole("button", { name: "Cerrar", exact: true }).click();

      const stressStarted = Date.now();
      await page.goto(`/catalogs/systems?system=${catalog.stressId}`);
      await expect(
        page.getByRole("heading", { name: "300 perfiles · ensayo sintético", exact: true }),
      ).toBeVisible();
      await expect(page.getByText("1–50 de 300", { exact: true })).toBeVisible();
      await expect(page.getByRole("grid").getByRole("row")).toHaveCount(51);
      await expect(page.getByRole("textbox", { name: /Peso del perfil/ }).first()).toHaveValue(
        "1,2345",
      );
      console.info(
        JSON.stringify({ viewport, surface: "300-profiles", loadMs: Date.now() - stressStarted }),
      );
      await capture(page, info, "serie-300-perfiles");

      await page.getByRole("button", { name: "‹ Catálogo", exact: true }).click();
      await page
        .getByRole("searchbox", { name: "Buscar fabricante o serie" })
        .fill("no coincide con ninguna serie");
      await expect(page.getByRole("heading", { name: "Ninguna serie coincide" })).toBeVisible();
      await page.getByRole("searchbox", { name: "Buscar fabricante o serie" }).fill("");
      await page.locator(".series-catalog__examples > summary").click();
      await expect(page.locator(".series-catalog__examples li").first()).toBeVisible();
      await expect(page.getByText("2 series de tu taller", { exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Agregar serie", exact: true }).click();
      await page.getByRole("button", { name: "Desde una plantilla", exact: true }).click();
      const adding = page.getByRole("dialog", { name: "Desde una plantilla" });
      await adding
        .getByLabel("Nombre de la serie", { exact: true })
        .fill("Mi nueva serie de ensayo");
      await adding.getByLabel("Código", { exact: true }).fill("E2E-NEW-SERIES");
      await adding.getByLabel("Fabricante", { exact: true }).fill("Taller sintético");
      await adding
        .getByRole("combobox", { name: "Plantilla", exact: true })
        .selectOption("pvc-casement-60-70");
      await adding.getByRole("button", { name: "Crear serie", exact: true }).click();
      await expect(
        page.getByRole("heading", { name: "Mi nueva serie de ensayo", exact: true }),
      ).toBeVisible();
      await expect(page.getByText("Completar serie", { exact: true })).toBeVisible();
      await expect(page.getByText("Todavía no hay filas en esta sección.")).toBeVisible();
    });
  });
}

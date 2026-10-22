import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import { fileURLToPath } from "node:url";
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
  const path = info.outputPath(`${name}-${page.viewportSize()!.width}.png`);
  await page.screenshot({ path, animations: "disabled" });
  await info.attach(name, { path, contentType: "image/png" });
}
for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Precios mapeados ${viewport.width}`, () => {
    test.use({ viewport });
    test("reviews all rows without saving, invalidates a changed mapping and explicitly imports exact workshop costs", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      await page.goto(`/catalogs/systems?system=${catalog.systemId}`);
      await page.getByRole("tab", { name: "Precios", exact: true }).click();
      await page
        .getByRole("button", { name: "Importar precios del proveedor", exact: true })
        .click();
      const panel = page.getByRole("dialog", { name: "Precios del proveedor", exact: true });
      await panel
        .getByLabel("Archivo de precios", { exact: true })
        .setInputFiles(
          fileURLToPath(new URL("./fixtures/p03-precios-sinteticos.xlsx", import.meta.url)),
        );
      await expect(panel.getByText(/hoja Precios de prueba · 12 filas/)).toBeVisible();
      await panel.getByRole("button", { name: "Crear una lista nueva", exact: true }).click();
      await panel
        .getByLabel("Proveedor", { exact: true })
        .fill("Proveedor sintético 窗 y taller de ensayo con precios revisados");
      await panel
        .getByLabel("Vigente desde", { exact: true })
        .fill(new Date().toISOString().slice(0, 10));
      const created = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === "/api/v1/pricing/admin/cost-lists/" &&
          response.request().method() === "POST",
      );
      await panel.getByRole("button", { name: "Crear lista", exact: true }).click();
      const createdResponse = await created;
      const result = (await createdResponse.json()) as { items: { id: string }[] };
      const requestHeaders = await createdResponse.request().allHeaders();
      const listId = result.items[0]!.id;
      await expect(
        panel.getByRole("combobox", { name: "Lista de destino", exact: true }),
      ).toHaveValue(listId);
      await capture(page, info, "precios-mapeo");
      const start = Date.now();
      await panel.getByRole("button", { name: "Revisar todos los precios", exact: true }).click();
      await expect(
        panel.getByRole("heading", { name: "Revisa y confirma 12 precios", exact: true }),
      ).toBeVisible();
      console.info(
        JSON.stringify({ surface: "supplier-prices", viewport, reviewMs: Date.now() - start }),
      );
      const table = panel.getByRole("table");
      await expect(table.getByRole("row")).toHaveCount(11);
      await expect(table.getByRole("cell", { name: "001", exact: true })).toBeVisible();
      await expect(table.getByRole("cell", { name: /45\s000,1234 CLP/ })).toBeAttached();
      // Reuse only the ordinary owner's authenticated request, entirely in the runner.
      const listItems = async () => {
        const response = await page.request.get("/api/v1/pricing/admin/cost-items/", {
          headers: {
            Authorization: requestHeaders.authorization!,
            "X-Organization-ID": catalog.organizationId,
          },
        });
        expect(response.ok()).toBe(true);
        const data = (await response.json()) as {
          items: { cost_list_id: string; sku: string; unit_cost: string }[];
        };
        return data.items.filter((item) => item.cost_list_id === listId);
      };
      expect(await listItems()).toEqual([]);
      await panel
        .getByRole("combobox", { name: "Código", exact: true })
        .selectOption("Descripción");
      await expect(panel.getByRole("button", { name: "Confirmar y guardar precios" })).toHaveCount(
        0,
      );
      await expect(panel.getByRole("button", { name: "Revisar todos los precios" })).toBeDisabled();
      await panel.getByRole("combobox", { name: "Código", exact: true }).selectOption("Código");
      await panel.getByRole("button", { name: "Revisar todos los precios", exact: true }).click();
      await panel
        .getByRole("region", { name: "Confirmación de precios", exact: true })
        .scrollIntoViewIfNeeded();
      await capture(page, info, "precios-revision");
      await panel.getByRole("button", { name: "Confirmar y guardar precios", exact: true }).click();
      await expect(
        panel.getByRole("heading", { name: "Precios guardados", exact: true }),
      ).toBeVisible();
      const saved = await listItems();
      expect(saved).toHaveLength(12);
      expect(saved.find((item) => item.sku === "PRO-F")?.unit_cost).toBe("45000.1234");
      expect(saved.find((item) => item.sku === "001")?.unit_cost).toBe("0.2500");
      await capture(page, info, "precios-guardados");
      await panel.getByRole("button", { name: "Volver a la serie", exact: true }).click();
      await expect(
        page.getByRole("grid", { name: "Precios de la serie", exact: true }),
      ).toContainText("Marco sintético");
    });
  });
}

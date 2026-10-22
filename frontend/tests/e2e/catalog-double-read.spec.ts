import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Publicación de doble lectura ${viewport.width}`, () => {
    test.use({ viewport, doubleReadManual: true });
    test("chooses a cited reading, compares the real catalog and publishes only after human confirmation", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      const opened = Date.now();
      const catalogRequests: string[] = [];
      page.on("request", (request) => {
        const path = new URL(request.url()).pathname;
        if (/\/api\/v1\/catalogs\/(systems|articles|glazing|hardware-kits)\/$/.test(path))
          catalogRequests.push(path);
      });
      await page.goto(`/catalogs/systems?import=${catalog.manualImportId}`);
      const review = page.getByRole("region", { name: "Diferencias entre las dos lecturas" });
      await expect(review).toBeVisible();
      console.info(
        JSON.stringify({ surface: "manual-linked", viewport, readyMs: Date.now() - opened }),
      );
      expect(catalogRequests).toEqual([]);
      await expect(review.getByRole("textbox")).toHaveCount(1);
      await expect(review.getByText(/1 diferencia por resolver/)).toBeVisible();
      await expect(review.getByText(/soldadura alternativa: 4.00/)).toBeVisible();
      await review.getByRole("button", { name: "Usar lectura 2", exact: true }).click();
      await expect(review.getByRole("checkbox")).not.toBeChecked();
      await review.getByRole("checkbox").check();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
        viewport.width,
      );
      expect(
        (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
          .violations,
      ).toEqual([]);
      const path = info.outputPath(`manual-revisado-${viewport.width}.png`);
      await review.scrollIntoViewIfNeeded();
      await page.screenshot({ path, animations: "disabled" });
      await info.attach("Revisión con ambas citas", { path, contentType: "image/png" });
      // A separate read proves the proposal did not write the chosen number.
      const other = await page.context().newPage();
      const originalSheet = other.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === `/api/v1/catalogs/series/${catalog.systemId}/`,
      );
      await other.goto(`/catalogs/systems?system=${catalog.systemId}`);
      const original = await (await originalSheet).json();
      expect(
        original.tabs.profiles.find((row: { id: string }) => row.id === catalog.manualArticleId)
          .cut_rule.welding_loss_per_end_mm,
      ).toBe("3.00");
      await other.close();
      await page.getByRole("button", { name: "Comparar cambios", exact: true }).click();
      const publish = page.getByRole("button", { name: "Publicar catálogo revisado", exact: true });
      await expect(publish).toBeDisabled();
      await page.getByRole("checkbox", { name: /Revisé la referencia y los cambios/ }).check();
      const published = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname ===
          `/api/v1/catalog-imports/${catalog.manualImportId}/publish/`,
      );
      await publish.click();
      expect((await published).status()).toBe(200);
      await expect(page.getByText(/Publicación completa:/)).toBeVisible();
      const before = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === `/api/v1/catalogs/series/${catalog.systemId}/`,
      );
      await page.goto(`/catalogs/systems?system=${catalog.systemId}`);
      const sheet = await (await before).json();
      expect(
        sheet.tabs.profiles.find((row: { id: string }) => row.id === catalog.manualArticleId)
          .cut_rule.welding_loss_per_end_mm,
      ).toBe("4.00");
      expect(
        sheet.cells.find(
          (cell: { row_id: string; field: string }) =>
            cell.row_id === catalog.manualArticleId &&
            cell.field === "cut_rule.welding_loss_per_end_mm",
        ).origin,
      ).toBe("MANUAL");
      expect(
        (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
          .violations,
      ).toEqual([]);
    });
  });
}

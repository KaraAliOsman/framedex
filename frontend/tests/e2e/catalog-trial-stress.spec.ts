import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
  { width: 320, height: 844 },
]) {
  test.describe(`Despiece extremo ${viewport.width}`, () => {
    test.use({ viewport });
    test("keeps exact data, pages 500 rows, supports large text and accessible local scrolling", async ({
      page,
    }, info) => {
      await page.goto("/dev/prueba-serie");
      await expect(page.getByRole("heading", { name: "Revisa el despiece" })).toBeVisible();
      for (const mode of ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 piezas"]) {
        const start = Date.now();
        await page.getByRole("button", { name: mode, exact: true }).click();
        const table = page.getByRole("table");
        if (mode === "Vacío") await expect(table).toContainText("El motor no devolvió piezas");
        if (mode === "Uno") await expect(table.getByRole("row")).toHaveCount(2);
        if (mode === "500 piezas") {
          await expect(table.getByRole("row")).toHaveCount(51);
          await page.getByRole("button", { name: "Siguiente", exact: true }).click();
          await expect(
            page.getByRole("status").filter({ hasText: "Página 2 de 10" }),
          ).toBeVisible();
        }
        console.info(
          JSON.stringify({
            surface: "trial-stress",
            viewport,
            mode,
            responseMs: Date.now() - start,
          }),
        );
        for (const textScale of [100, 200]) {
          await page.evaluate((scale) => {
            document.documentElement.style.fontSize = `${scale}%`;
          }, textScale);
          expect(
            await page.evaluate(() => document.documentElement.scrollWidth),
          ).toBeLessThanOrEqual(viewport.width);
          const path = info.outputPath(`despiece-${mode}-${textScale}.png`);
          await page.screenshot({ path, animations: "disabled" });
          await info.attach(`${mode}-${textScale}`, { path, contentType: "image/png" });
        }
        expect(
          (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
            .violations,
        ).toEqual([]);
        await page.evaluate(() => {
          document.documentElement.style.fontSize = "100%";
        });
      }
    });
  });
}

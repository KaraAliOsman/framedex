import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
  { width: 320, height: 844 },
]) {
  test.describe(`Precios extremos ${viewport.width}`, () => {
    test.use({ viewport });
    test("keeps codes and exact prices accessible with large text and zero, one or 500 prices", async ({
      page,
    }, info) => {
      const started = Date.now();
      await page.goto("/dev/precios-proveedor");
      await page
        .getByRole("heading", { name: "Precios del proveedor · ensayo visual", exact: true })
        .waitFor();
      console.info(
        JSON.stringify({ surface: "supplier-prices-dev", viewport, readyMs: Date.now() - started }),
      );
      for (const mode of ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 precios"]) {
        const interaction = Date.now();
        await page.getByRole("button", { name: mode, exact: true }).click();
        const table = page.getByRole("table");
        if (mode === "Vacío")
          await expect(table).toContainText("El archivo no tiene filas de precios");
        if (mode === "Uno") await expect(table.getByRole("row")).toHaveCount(2);
        if (mode === "500 precios") {
          await expect(table.getByRole("row")).toHaveCount(11);
          await expect(table).toContainText("10 / 500");
        }
        console.info(
          JSON.stringify({
            surface: "supplier-prices-dev",
            mode,
            viewport,
            responseMs: Date.now() - interaction,
          }),
        );
        for (const textScale of [100, 200]) {
          await page.evaluate((scale) => {
            document.documentElement.style.fontSize = `${scale}%`;
          }, textScale);
          expect(
            await page.evaluate(() => document.documentElement.scrollWidth),
          ).toBeLessThanOrEqual(viewport.width);
          const scroll = page.getByRole("region", { name: "Muestra de precios", exact: true });
          await scroll.evaluate((element) => {
            element.scrollLeft = 0;
            element.scrollTop = 0;
          });
          await scroll.focus();
          if (viewport.width < 1000) {
            await page.keyboard.press("ArrowRight");
            await expect
              .poll(() => scroll.evaluate((element) => element.scrollLeft))
              .toBeGreaterThan(0);
          }
          await scroll.evaluate((element) => {
            element.scrollLeft = element.scrollWidth;
          });
          await scroll.scrollIntoViewIfNeeded();
          if (mode !== "Vacío") {
            const amount = table.getByRole("cell", { name: /CLP/ }).first();
            await expect(amount).toBeAttached();
            const bounds = (await amount.boundingBox())!;
            expect(bounds.x).toBeGreaterThanOrEqual(0);
            expect(bounds.x + bounds.width).toBeLessThanOrEqual(viewport.width);
          }
          const path = info.outputPath(`precios-${mode}-${textScale}.png`);
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

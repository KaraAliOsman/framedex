import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
  { width: 320, height: 844 },
]) {
  test.describe(`Doble lectura ${viewport.width}`, () => {
    test.use({ viewport });
    test("preserves both citations and choices with large text and zero, one or 500 rows", async ({
      page,
    }, info) => {
      const started = Date.now();
      await page.goto("/dev/lectura-manual");
      await page.getByRole("heading", { name: "Lectura del manual · ensayo visual" }).waitFor();
      console.info(
        JSON.stringify({ surface: "manual-dev", viewport, readyMs: Date.now() - started }),
      );
      for (const mode of ["Datos de ejemplo", "Peor caso", "Vacío", "Uno", "500 filas"]) {
        const interaction = Date.now();
        await page.getByRole("button", { name: mode, exact: true }).click();
        const region = page.getByRole("region", { name: "Diferencias entre las dos lecturas" });
        if (mode === "Vacío")
          await expect(region.getByText(/Ambas lecturas coinciden/)).toBeVisible();
        else {
          const first = region.getByRole("article").first();
          if (mode === "Uno") await expect(region.getByRole("article")).toHaveCount(1);
          if (mode === "500 filas") {
            await expect(region.getByRole("article")).toHaveCount(10);
            await expect(region).toContainText("Página 1 de 50 · 500 filas");
          }
          await expect(first.getByText(/página 8/)).toBeVisible();
          const include = first.getByRole("checkbox");
          await expect(include).toBeDisabled();
          await first.getByRole("button", { name: "Usar lectura 1", exact: true }).click();
          await expect(first.getByRole("textbox")).toHaveValue(
            mode === "Peor caso" ? "200.00" : "60.00",
          );
          await expect(include).not.toBeChecked();
          await include.check();
          await expect(include).toBeChecked();
        }
        console.info(
          JSON.stringify({
            surface: "manual-dev",
            mode,
            viewport,
            responseMs: Date.now() - interaction,
          }),
        );
        for (const scale of [100, 200]) {
          await page.evaluate((value) => {
            document.documentElement.style.fontSize = `${value}%`;
          }, scale);
          expect(
            await page.evaluate(() => document.documentElement.scrollWidth),
          ).toBeLessThanOrEqual(viewport.width);
          await page.evaluate(() => window.scrollTo(0, 0));
          const path = info.outputPath(`manual-${mode}-${scale}.png`);
          await page.screenshot({ path, animations: "disabled" });
          await info.attach(`${mode}-${scale}`, { path, contentType: "image/png" });
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

import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { environment } from "./support/environment";

// Synthetic DEV surface: no tenant session or workshop data is needed.
const base = environment("DK2_TABLE_URL") ?? "http://127.0.0.1:5173/dev/tabla";
const sizes = [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
];

for (const viewport of sizes) {
  test.describe(`EditableTable ${viewport.width}`, () => {
    test.use({ viewport });

    test("renders extreme data without page overflow and meets AA", async ({ page }, testInfo) => {
      for (const [index, mode] of ["ejemplo", "extremo", "vacio", "uno", "300"].entries()) {
        const start = Date.now();
        await page.goto(`${base}?data=${index}`);
        await expect(page.getByRole("heading", { name: "Perfiles", exact: true })).toBeVisible();
        if (index === 2) {
          await expect(page.getByText("Todavía no hay filas en esta sección.")).toBeVisible();
        } else {
          await expect(page.getByRole("grid", { name: "Perfiles de ejemplo" })).toBeVisible();
        }
        const loadMs = Date.now() - start;
        console.info(JSON.stringify({ viewport, mode, loadMs }));
        expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
          viewport.width,
        );
        if (index === 4) {
          await expect(page.getByText("1–50 de 300")).toBeVisible();
          await expect(page.getByRole("grid").getByRole("row")).toHaveCount(51);
          await page.getByRole("button", { name: "Siguiente", exact: true }).click();
          await expect(page.getByText("51–100 de 300")).toBeVisible();
        }
        const accessibility = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        expect(accessibility.violations).toEqual([]);
        await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
        const capture = testInfo.outputPath(`tabla-${mode}-${viewport.width}.png`);
        await page.screenshot({ path: capture });
        await testInfo.attach(`tabla-${mode}-${viewport.width}.png`, {
          path: capture,
          contentType: "image/png",
        });
        await testInfo.attach(`tiempo-${mode}.json`, {
          body: JSON.stringify({ viewport, mode, loadMs }),
          contentType: "application/json",
        });
      }
    });

    test("pastes an exact block, validates, saves, undoes and uses the keyboard", async ({
      page,
    }) => {
      await page.goto(base);
      const cell = page.getByRole("textbox", { name: "Marco · Ancho visible", exact: true });
      await cell.focus();
      // The native clipboard path is also covered by the real-series flow.
      // This accessible dialog works when the browser denies clipboard access.
      await page.getByRole("button", { name: "Pegar desde Excel", exact: true }).click();
      await page
        .getByRole("textbox", { name: "Copia las celdas en Excel y pégalas aquí." })
        .fill("1,2345\n2,0001\n9007199254740993,1234\n0\n5,4321");
      await page.getByRole("button", { name: "Pegar bloque", exact: true }).click();
      await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
      await expect(page.getByRole("status")).toHaveText("Guardado");
      await expect(
        page.getByRole("textbox", { name: "Junquillo · Ancho visible", exact: true }),
      ).toHaveValue("9007199254740993,1234");
      await page.getByRole("button", { name: "Deshacer", exact: true }).click();
      await expect(page.getByRole("status")).toHaveText("Guardado");
      await expect(cell).toHaveValue("60,1234");

      await cell.fill("4,12345");
      await expect(cell).toHaveAttribute("aria-invalid", "true");
      await expect(
        page.getByRole("button", { name: "Guardar cambios", exact: true }),
      ).toBeDisabled();
      await cell.press("Escape");
      await expect(cell).toHaveValue("60,1234");
      await cell.fill("4,1234");
      await cell.press("Enter");
      const next = page.getByRole("textbox", { name: "Hoja · Ancho visible", exact: true });
      await expect(next).toBeFocused();
      await expect(page.getByRole("status")).toHaveText("Guardado");
      await next.press("ArrowRight");
      const length = page.getByRole("textbox", { name: "Hoja · Largo de barra", exact: true });
      await expect(length).toBeFocused();
      await length.press("Tab");
      await expect(
        page.getByRole("textbox", { name: "Junquillo · Código", exact: true }),
      ).toBeFocused();
    });
  });
}

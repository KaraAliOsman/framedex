import { expect } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Lenguaje de producto ${viewport.width}`, () => {
    test.use({ viewport, lightCatalog: true, catalogProjects: true });
    test("keeps absent values explicit across commercial and workshop screens", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(240_000);
      const screens = [
        ["thermal", `/projects/${catalog.projects!.issued}?section=thermal`, ".thermal-panel"],
        ["pricing", `/projects/${catalog.projects!.issued}?section=pricing`, ".project-head"],
        ["payments", `/projects/${catalog.projects!.issued}?section=payments`, ".project-head"],
        ["quote", `/projects/${catalog.projects!.issued}?section=quote`, ".project-head"],
        ["documents", `/projects/${catalog.projects!.issued}?section=documents`, ".project-head"],
        ["assistant", "/assistant", "main h1"],
        ["production", "/production", "main h1"],
        ["field", "/field", "main h1"],
        ["purchasing", "/purchasing", "main h1"],
        ["analytics", "/analytics", "main h1"],
        ["costs", "/pricing/cost-lists", ".pricing-page"],
      ] as const;
      for (const [name, href, ready] of screens) {
        const start = Date.now();
        await page.goto(href);
        await expect(page.locator(ready).first()).toBeVisible();
        await expect(
          page.locator('main .ui-loading:visible, main [aria-busy="true"]:visible'),
        ).toHaveCount(0, {
          timeout: 30_000,
        });
        await expect(
          page
            .getByRole("main")
            .getByRole("status")
            .filter({ hasText: /^(Cargando|Calculando|Procesando)/ }),
        ).toHaveCount(0, { timeout: 30_000 });
        await expect(page.locator("main .ui-empty--error")).toHaveCount(0);
        await page.evaluate(() => document.fonts.ready);
        const tabs = await page.locator(".area-tabs__item").evaluateAll((links) =>
          links.map((link) => {
            const box = link.getBoundingClientRect();
            return { left: box.left, right: box.right };
          }),
        );
        for (const [index, tab] of tabs.entries()) {
          const previous = tabs[index - 1];
          if (previous) expect(tab.left, `${name} tabs`).toBeGreaterThan(previous.right);
        }
        const text = await page.locator("main").innerText();
        expect(text, name).not.toMatch(
          /\b(?:sin datos?|sellad[oa]s?|autoridad(?:es)?|fuentes?|procedencias?)\b/iu,
        );
        expect(
          await page.evaluate(() => document.documentElement.scrollWidth),
          name,
        ).toBeLessThanOrEqual(viewport.width);
        console.log(JSON.stringify({ surface: name, viewport, loadMs: Date.now() - start }));
        await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true });
      }
    });
  });
}

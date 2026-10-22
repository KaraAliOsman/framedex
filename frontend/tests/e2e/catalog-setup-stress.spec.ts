import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";
test.use({ lightCatalog: true });

test("setup layout withstands long identity, 0/1/500 profiles and pending fields at 100/200 percent text", async ({
  page,
  catalog,
}, info) => {
  test.setTimeout(180_000);
  let count = 0;
  let step = 1;
  // UI stress only: no catalog or progress writes. Real acceptance is separate.
  await page.route(`**/api/v1/catalogs/series/${catalog.systemId}/`, async (route) => {
    const response = await route.fetch();
    const sheet = await response.json();
    sheet.tabs.rules.name = "Serie de ensayo del taller 窗 Ñ ".repeat(5).slice(0, 150);
    sheet.tabs.rules.manufacturer = "Fabricante con nombre muy largo y caracteres 窗 Ñ "
      .repeat(5)
      .slice(0, 255);
    sheet.tabs.rules.code = "PRO6004-" + "X".repeat(42);
    sheet.tabs.profiles = Array.from({ length: count }, (_, index) => ({
      ...sheet.tabs.profiles[0],
      id: `stress-${index}`,
      sku: `PERFIL-${index}`,
    }));
    const pending = Array.from({ length: count }, (_, index) => ({
      field: "prices",
      resource: "systems",
      row_id: null,
      origin: null,
      rule: `cost-${index}`,
      required_for: ["QUOTABLE"],
      action: `Completa el precio del perfil ${index} de ensayo 窗 con código ${"X".repeat(100)}.`,
    }));
    sheet.usage.levels = [{ level: "QUOTABLE", ok: false, pending }];
    sheet.usage.pending = pending;
    sheet.usage.verified = false;
    await route.fulfill({ response, json: sheet });
  });
  await page.route(`**/api/v1/catalogs/series/${catalog.systemId}/setup/`, (route) =>
    route.fulfill({ json: { step, revision: 1, state: {} } }),
  );
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
    { width: 320, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    for (const next of [0, 1, 500]) {
      count = next;
      step = next === 0 ? 1 : 5;
      await page.goto(`/catalogs/systems?system=${catalog.systemId}&setup=1`);
      const wizard = page.getByRole("dialog", { name: "Preparar mi serie", exact: true });
      await expect(
        wizard.getByRole("button", {
          name: `Paso ${step}: ${step === 1 ? "Serie" : "Primera cotización"}`,
          exact: true,
        }),
      ).toHaveAttribute("aria-current", "step");
      for (const zoom of [100, 200]) {
        await page.addStyleTag({ content: `html { font-size: ${zoom}%; }` });
        expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
          viewport.width,
        );
        expect(
          (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
            .violations,
        ).toEqual([]);
        if (next === 500 && zoom === 200) {
          const pending = wizard.getByRole("region", { name: "Datos pendientes para cotizar" });
          await pending.scrollIntoViewIfNeeded();
          await pending.focus();
          await pending.press("End");
          await expect(pending.getByRole("listitem").last()).toBeInViewport();
          await expect(
            wizard.getByRole("button", { name: "Crear mi primera cotización", exact: true }),
          ).toBeDisabled();
          const path = info.outputPath(`alta-extremos-${viewport.width}.png`);
          await page.screenshot({ path, animations: "disabled" });
          await info.attach(`Extremos ${viewport.width}`, { path, contentType: "image/png" });
        }
      }
    }
  }
});

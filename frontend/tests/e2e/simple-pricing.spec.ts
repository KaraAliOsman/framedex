import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";
import { environment } from "./support/environment";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => {
    (document.activeElement as HTMLElement | null)?.blur();
    window.scrollTo(0, 0);
  });
  const overflow = await page.evaluate(() =>
    Array.from(document.querySelectorAll(".simple-pricing, .simple-pricing *"))
      .filter((element) => element.getBoundingClientRect().right > innerWidth)
      .map((element) => ({
        tag: element.tagName,
        class: element.className,
        text: element.textContent?.slice(0, 60),
      })),
  );
  if (overflow.length) console.log(JSON.stringify({ name, overflow }));
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  const violations = await new AxeBuilder({ page })
    .include(".simple-pricing")
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(violations.violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Mis precios ${viewport.width}`, () => {
    test.use({ viewport });
    test("configures exact services and previews a PRO6004 window without applying", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      await page.addInitScript(() => {
        const metrics = { lcpMs: 0, cls: 0 };
        Reflect.set(window, "pricingPerformance", metrics);
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) metrics.lcpMs = entry.startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const shift = entry as PerformanceEntry & { value: number; hadRecentInput: boolean };
            if (!shift.hadRecentInput) metrics.cls += shift.value;
          }
        }).observe({ type: "layout-shift", buffered: true });
      });
      const reading = page.waitForRequest(
        (request) =>
          new URL(request.url()).pathname === "/api/v1/pricing/simple-policy/" &&
          request.method() === "GET",
      );
      const started = Date.now();
      await page.goto("/settings/general?section=prices");
      const headers = {
        Authorization: (await reading).headers().authorization!,
        "X-Organization-ID": catalog.organizationId,
      };
      await expect(
        page.getByRole("textbox", { name: "Margen sobre venta", exact: true }),
      ).toBeVisible();
      console.log(
        JSON.stringify({ viewport, surface: "simple-pricing", loadMs: Date.now() - started }),
      );
      await expect(
        page.getByText("Valores sugeridos. Ajústalos a tu taller antes de guardar."),
      ).toBeVisible();
      await expect(
        page.getByRole("link", { name: "Crear una ventana", exact: true }),
      ).toBeVisible();
      await capture(page, info, "01-suggested-empty");
      console.log(
        JSON.stringify({
          viewport,
          surface: "simple-pricing-vitals",
          ...(await page.evaluate(
            () => Reflect.get(window, "pricingPerformance") as { lcpMs: number; cls: number },
          )),
        }),
      );
      await page.getByRole("textbox", { name: "Mano de obra", exact: true }).fill("15000,1234");
      await page.getByLabel("Cobrar mano de obra", { exact: true }).selectOption("WINDOW");
      await page.getByRole("textbox", { name: "Instalación", exact: true }).fill("10000");
      await page.getByLabel("Cobrar instalación", { exact: true }).selectOption("M2");
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("42,75");
      const saved = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === "/api/v1/pricing/simple-policy/" &&
          response.request().method() === "PUT",
      );
      await page.getByRole("button", { name: "Guardar mis precios", exact: true }).click();
      expect((await saved).status()).toBe(200);
      await expect(page.getByText(/Precios guardados/)).toBeVisible();
      const backend = environment("DJANGO_URL")!;
      // Ordinary owner API: restore the fixture's missing cell, then create a
      // real three-window draft. All material prices come from the fixture.
      const sheet = await page.request.get(
        `${backend}/api/v1/catalogs/series/${catalog.systemId}/`,
        { headers },
      );
      expect(sheet.ok()).toBe(true);
      const edit = await page.request.patch(
        `${backend}/api/v1/catalogs/series/${catalog.systemId}/cells/`,
        {
          headers,
          data: {
            revision: (await sheet.json()).revision,
            changes: [
              {
                resource: "systems",
                row_id: catalog.systemId,
                field: "rebate_depth_mm",
                value: catalog.pasteValues[3],
              },
            ],
          },
        },
      );
      expect(edit.status()).toBe(200);
      const created = await page.request.post(`${backend}/api/v1/projects/`, {
        headers,
        data: {
          name: "Casa Wiśniewska-Kowalczyk · PRO6004 de ensayo",
          client_name: "Cliente sintético",
        },
      });
      expect(created.status()).toBe(201);
      const project = await created.json();
      for (const location of ["Living", "Dormitorio principal", "Cocina"]) {
        const response = await page.request.post(
          `${backend}/api/v1/projects/${project.id}/positions/`,
          {
            headers,
            data: {
              location_tag: location,
              quantity: 1,
              design: {
                system_id: catalog.systemId,
                nominal_width_mm: "1200",
                nominal_height_mm: "1100",
                color: "WHITE",
                parametric_tree: {
                  id: "B1",
                  type: "BAY",
                  opening_type: "TURN_LEFT",
                  glass_spec: "4-16-4",
                  glass_thickness_mm: "24",
                  glass_article_sku: "GLASS-24",
                },
              },
            },
          },
        );
        expect(response.status(), await response.text()).toBe(201);
      }
      await page.reload();
      await expect(page.locator(".simple-pricing__total")).toContainText("$");
      await expect(page.getByText("Sin dato", { exact: true })).toHaveCount(0);
      await expect(page.getByRole("textbox", { name: "Mano de obra", exact: true })).toHaveValue(
        "15000,1234",
      );
      await capture(page, info, "02-pro6004-breakdown");
      const before = await page.locator(".simple-pricing__total dd").innerText();
      const changedAt = Date.now();
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("50");
      await expect(page.locator(".simple-pricing__total dd")).not.toHaveText(before);
      console.log(
        JSON.stringify({
          viewport,
          surface: "simple-pricing-example",
          responseMs: Date.now() - changedAt,
        }),
      );
      await capture(page, info, "03-margin-live");
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("100");
      await expect(
        page.getByRole("button", { name: "Guardar mis precios", exact: true }),
      ).toBeDisabled();
      await expect(page.getByText("Escribe un porcentaje menor que 100.")).toBeVisible();
      await capture(page, info, "04-invalid-margin");
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("99,99");
      await page
        .getByRole("textbox", { name: "Mano de obra", exact: true })
        .fill("9999999999,9999");
      await expect(page.locator(".simple-pricing__total")).toBeVisible();
      await expect(page.getByText(/Margen sobre venta: 99,99 %/)).toBeVisible();
      await capture(page, info, "05-large-amounts");
      await page.getByRole("textbox", { name: "Mano de obra", exact: true }).fill("15000,1234");
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("42,75");
      const work = await page.request.get(`${backend}/api/v1/projects/${project.id}/`, { headers });
      const priced = await work.json();
      expect(priced.working_price.state).toBe("READY");
      expect(priced.pricing_current).toBe(false);
      expect(priced.positions).toHaveLength(3);
      await page.getByRole("switch", { name: "Usar precios avanzados", exact: true }).check();
      await expect(page.getByText("Configuración avanzada", { exact: true })).toHaveCount(0);
      await capture(page, info, "06-advanced-opt-in");
      if (viewport.width === 1440) {
        for (const width of [1280, 1024, 320]) {
          await page.setViewportSize({ width, height: 900 });
          await capture(page, info, `07-width-${width}`);
        }
        await page.evaluate(() => {
          document.documentElement.style.fontSize = "200%";
        });
        await capture(page, info, "08-text-200-percent");
      }
    });
  });
}

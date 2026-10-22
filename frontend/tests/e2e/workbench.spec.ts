import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "./support/catalog-series-fixture";
import { environment } from "./support/environment";
import { fmtMm, formatMoney } from "../../src/format";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Mesa de la obra ${viewport.width}`, () => {
    test.use({ viewport, lightCatalog: true });
    test("creates a library window, edits and cancels dimensions, and preserves the engine total", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      const reading = page.waitForRequest(
        (request) =>
          new URL(request.url()).pathname === "/api/v1/pricing/simple-policy/" &&
          request.method() === "GET",
      );
      await page.goto("/settings/general?section=prices");
      const headers = {
        Authorization: (await reading).headers().authorization!,
        "X-Organization-ID": catalog.organizationId,
      };
      const backend = environment("DJANGO_URL")!;
      async function api(path: string, method = "GET", data?: unknown) {
        const response = await page.request.fetch(`${backend}/api/v1/${path}`, {
          method,
          headers,
          data,
        });
        expect(response.ok(), await response.text()).toBe(true);
        return response.json();
      }
      const sheet = await api(`catalogs/series/${catalog.systemId}/`);
      await api(`catalogs/series/${catalog.systemId}/cells/`, "PATCH", {
        revision: sheet.revision,
        changes: [
          {
            resource: "systems",
            row_id: catalog.systemId,
            field: "rebate_depth_mm",
            value: catalog.pasteValues[3],
          },
        ],
      });
      const project = await api("projects/", "POST", {
        name: "Casa Pérez · ensayo sintético de la mesa",
        client_name: "Cliente sintético",
      });
      const path = `/projects/${project.id}`;
      const openedAt = Date.now();
      await page.goto(path);
      await expect(
        page.getByRole("heading", { name: "La obra todavía no tiene ventanas" }),
      ).toBeVisible();
      const loadMs = Date.now() - openedAt;
      await expect(
        page.getByRole("button", { name: "Enviar cotización", exact: true }),
      ).toBeDisabled();
      await page.screenshot({ path: info.outputPath("01-empty.png"), fullPage: true });
      await page.getByRole("link", { name: "Añadir ventana", exact: true }).first().click();
      await expect(
        page.getByRole("heading", { name: "La obra todavía no tiene ventanas" }),
      ).toHaveCount(0);
      const series = page.getByRole("button", { name: /PRO6004 · ensayo sintético/ });
      await series.click();
      await page
        .getByRole("button", { name: "Fijo · Ventanal fijo de una pieza", exact: true })
        .click();
      await page.getByLabel("Ubicación de la ventana", { exact: true }).fill("Living · fijo");
      const save = page.getByRole("button", { name: "Guardar", exact: true });
      await expect(save).toBeEnabled({ timeout: 30_000 });
      await save.click();
      await expect(page).toHaveURL(new RegExp(`${path}\\?position=`));
      await expect(
        page.getByRole("button", { name: "Enviar cotización", exact: true }),
      ).toBeEnabled();
      const saved = await api(`projects/${project.id}/`);
      expect(saved.positions).toHaveLength(1);
      expect(saved.working_price.state).toBe("READY");
      const total = page.locator(".project-head__total strong");
      await expect(total).toHaveText(formatMoney(saved.working_price.project_gross, "CLP"));
      const dimension = page
        .locator('.canvas-sheet [role="button"][aria-label="Ancho total"]')
        .first();
      await dimension.click();
      const field = page.locator('foreignObject input[aria-label="Ancho total"]');
      await field.fill("1400");
      let edits = 0;
      const record = (request: import("@playwright/test").Request) => {
        if (
          request.url().endsWith("/projects/operations/simulate/") &&
          request.postDataJSON()?.ops?.length
        )
          edits++;
      };
      page.on("request", record);
      await field.press("Escape");
      await expect(field).toHaveCount(0);
      await expect(dimension).toContainText(fmtMm(saved.positions[0].design.nominal_width_mm));
      expect(edits).toBe(0);
      await dimension.click();
      await field.fill("1400");
      const simulation = page.waitForResponse(
        (response) =>
          response.url().endsWith("/projects/operations/simulate/") &&
          response
            .request()
            .postDataJSON()
            ?.ops?.some((op: { op: string }) => op.op === "set_total_width"),
      );
      await field.press("Enter");
      expect((await simulation).status()).toBe(200);
      await expect(dimension).toContainText("1\u2009400");
      await expect(save).toBeEnabled({ timeout: 30_000 });
      await save.click();
      const changed = await api(`projects/${project.id}/`);
      expect(changed.working_price.project_gross).not.toBe(saved.working_price.project_gross);
      await expect(total).toHaveText(formatMoney(changed.working_price.project_gross, "CLP"));
      if (viewport.width < 1280)
        await page.getByRole("button", { name: "Inspector", exact: true }).click();
      await expect(page.getByLabel("Cantidad", { exact: true })).toBeEnabled();
      await expect(
        page.getByRole("region", { name: "Precio de la ventana", exact: true }),
      ).toBeVisible();
      const line = changed.positions[0];
      const price = page.getByRole("button", {
        name: `¿De dónde sale el precio de ${line.location_tag}?`,
        exact: true,
      });
      await expect(price).toHaveText(formatMoney(line.commercial.line_net, "CLP"));
      await price.click();
      await expect(
        page.getByRole("heading", { name: "¿De dónde sale?", exact: true }),
      ).toBeVisible();
      await expect(page.getByText("Materiales", { exact: true })).toBeVisible();
      await page.keyboard.press("Escape");
      if (viewport.width < 1280)
        await expect(
          page.getByRole("button", { name: "Cerrar inspector", exact: true }),
        ).toBeVisible();
      await page.locator(".workspace").evaluate((element) => element.scrollTo({ top: 0 }));
      await page.screenshot({ path: info.outputPath("02-inspector.png"), fullPage: true });
      if (viewport.width < 1280)
        await page.getByRole("button", { name: "Cerrar inspector", exact: true }).click();
      await page.getByRole("button", { name: "3D", exact: true }).click();
      await expect(page.locator(".work-model3d")).toBeVisible();
      await expect(page.locator(".model3d-inset")).toHaveCount(0);
      await page
        .locator(".assembly-view-choices")
        .getByRole("button", { name: "Vista exterior", exact: true })
        .click();
      const model = page.locator(".work-model3d .model3d-view");
      await expect(model).toHaveAttribute("data-view", "exterior");
      const modelCanvas = model.locator(".model3d-canvas");
      await modelCanvas.scrollIntoViewIfNeeded();
      expect((await modelCanvas.boundingBox())!.height).toBeGreaterThanOrEqual(200);
      await page.screenshot({ path: info.outputPath("04-3d.png"), fullPage: true });
      await page
        .locator(".assembly-view-choices")
        .getByRole("button", { name: "Vista interior", exact: true })
        .click();
      await expect(model).toHaveAttribute("data-view", "interior");
      await page.getByRole("button", { name: "2D", exact: true }).click();
      await expect(dimension).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(viewport.width);
      expect(
        (
          await new AxeBuilder({ page })
            .include(".project-head, .project-studio")
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
      await page.locator(".canvas-viewport").scrollIntoViewIfNeeded();
      await page.screenshot({ path: info.outputPath("03-workbench.png"), fullPage: true });
      console.log(
        JSON.stringify({
          surface: "workbench",
          viewport,
          loadMs,
          windowId: changed.positions[0].id,
          engineTotal: changed.working_price.project_gross,
        }),
      );
    });
  });
}

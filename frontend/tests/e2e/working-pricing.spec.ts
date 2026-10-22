import AxeBuilder from "@axe-core/playwright";
import { createHash } from "node:crypto";
import { expect, type Page, type TestInfo } from "@playwright/test";
import { formatMoney } from "../../src/format";
import { compareDecimal } from "../../src/decimal";
import { test } from "./support/catalog-series-fixture";
import { environment } from "./support/environment";

async function capture(page: Page, info: TestInfo, name: string) {
  await expect(page.locator(".project-head")).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() =>
    Array.from(document.querySelectorAll(".project-head *, .project-position-collection *"))
      .filter((element) => element.getBoundingClientRect().right > innerWidth + 1)
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
  expect(
    (
      await new AxeBuilder({ page })
        .include(
          ".project-head, .project-position-collection, .working-price-detail, .working-price-panel",
        )
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Precio de trabajo ${viewport.width}`, () => {
    test.use({ viewport });
    test("shows three automatic prices, reprices a draft and preserves the issued PDF", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(240_000);
      await page.addInitScript(() => {
        const metrics = { lcpMs: 0, cls: 0 };
        Reflect.set(window, "workingPricePerformance", metrics);
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
        name: "Casa Wiśniewska-Kowalczyk · tres ventanas de ensayo",
        client_name: "Cliente sintético",
        client_rut: "12345678-5",
        client_email: "quotation-working@example.test",
        delivery_address: "Obra sintética; no despachar",
      });
      const path = `/projects/${project.id}`;
      await page.goto(path);
      await capture(page, info, "01-empty");
      for (const location of ["Living", "Dormitorio principal", "Cocina"]) {
        await api(`projects/${project.id}/positions/`, "POST", {
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
        });
      }
      const current = await api(`projects/${project.id}/`);
      expect(current.pricing_current).toBe(false);
      expect(current.current_pricing_operation_id).toBeNull();
      expect(current.working_price.state).toBe("READY");
      const started = Date.now();
      await page.reload();
      const total = page.locator(".project-head__total strong");
      await expect(total).toHaveText(
        formatMoney(current.working_price.project_gross, current.working_price.currency),
      );
      console.log(
        JSON.stringify({
          viewport,
          surface: "working-price",
          loadMs: Date.now() - started,
          ...(await page.evaluate(() => Reflect.get(window, "workingPricePerformance"))),
        }),
      );
      await expect(page.getByText("Falta calcular el precio", { exact: true })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Aplicar", exact: true })).toHaveCount(0);
      await capture(page, info, "02-three-windows");
      const source = page.getByRole("button", {
        name: "¿De dónde sale el precio de Living?",
        exact: true,
      });
      await source.click();
      const detail = page.getByRole("region", { name: "Precio de Living", exact: true });
      await expect(detail.getByText("Materiales", { exact: true })).toBeVisible();
      await expect(detail.getByText(/La serie usa valores sugeridos/)).toBeVisible();
      await capture(page, info, "03-breakdown");
      await page.keyboard.press("Escape");
      await expect(source).toBeFocused();
      // Same SPA session: saving company policy invalidates the shared project cache.
      await page.goto("/settings/general?section=prices");
      await page.getByRole("textbox", { name: "Margen sobre venta", exact: true }).fill("50");
      const saved = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === "/api/v1/pricing/simple-policy/" &&
          response.request().method() === "PUT",
      );
      await page.getByRole("button", { name: "Guardar mis precios", exact: true }).click();
      expect((await saved).status()).toBe(200);
      await page.getByText(/Precios guardados/).waitFor();
      const repriced = await api(`projects/${project.id}/`);
      expect(repriced.working_price.project_gross).not.toBe(current.working_price.project_gross);
      expect(repriced.pricing_current).toBe(false);
      await page.goto(path);
      await expect(total).toHaveText(
        formatMoney(repriced.working_price.project_gross, repriced.working_price.currency),
      );
      await capture(page, info, "04-margin-recalculated");
      await page.goto(`${path}?section=pricing`);
      await expect(page.locator(".working-price-totals")).toContainText(
        formatMoney(repriced.working_price.project_gross, repriced.working_price.currency),
      );
      await expect(page.getByRole("button", { name: "Aplicar", exact: true })).toHaveCount(0);
      await capture(page, info, "04-price-panel");
      await page.getByRole("tab", { name: "Cotización", exact: true }).click();
      await page.getByRole("button", { name: "Preparar emisión", exact: true }).click();
      await page
        .getByLabel("Condiciones de pago", { exact: true })
        .fill("Transferencia sintética, 50 % al aprobar y 50 % contra entrega.");
      await page.getByLabel("Cotización válida hasta", { exact: true }).fill("2026-12-31");
      await page.getByText("Plazo, instalación y condiciones legales", { exact: true }).click();
      for (const [label, value] of [
        ["Plazo de entrega", "20 días hábiles"],
        ["Instalación", "Incluida según medidas"],
        ["Exclusiones", "Pintura"],
        ["Garantía", "12 meses"],
      ]) {
        await page.getByLabel(label!, { exact: true }).fill(value!);
      }
      const previewing = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname ===
            `/api/v1/documents/projects/${project.id}/quotation-preview/` &&
          response.request().method() === "POST",
      );
      await page.getByRole("button", { name: "Preparar PDF para revisar", exact: true }).click();
      const previewResponse = await previewing;
      expect(previewResponse.status(), await previewResponse.text()).toBe(201);
      expect(previewResponse.request().postDataJSON()).toEqual({});
      const preview = await previewResponse.json();
      const pdf = await page.request.get(preview.pdf_url);
      const bytes = await pdf.body();
      expect(createHash("sha256").update(bytes).digest("hex")).toBe(preview.file_sha256);
      const stillDraft = await api(`projects/${project.id}/`);
      expect(stillDraft.pricing_current).toBe(false);
      await capture(page, info, "05-reviewed-pdf");
      await page.locator(".quotation-review").screenshot({
        path: info.outputPath("05-pdf-confirmation.png"),
      });
      const issue = page.getByRole("button", { name: "Emitir y enviar al cliente", exact: true });
      await expect(issue).toBeDisabled();
      await page
        .getByLabel("Revisé este PDF, el destinatario y las condiciones de emisión")
        .check();
      const issuing = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === `/api/v1/documents/projects/${project.id}/issue/` &&
          response.request().method() === "POST",
      );
      await issue.click();
      const issuedResponse = await issuing;
      expect(issuedResponse.status(), await issuedResponse.text()).toBe(201);
      const issued = await issuedResponse.json();
      expect(issued.file_sha256).toBe(preview.file_sha256);
      const frozen = await api(`projects/${project.id}/`);
      expect(frozen.status).toBe("QUOTED");
      expect(frozen.pricing_current).toBe(true);
      expect(compareDecimal(frozen.total_price_gross, repriced.working_price.project_gross)).toBe(
        0,
      );
      const policy = await api("pricing/simple-policy/");
      const {
        revision,
        saved: _saved,
        suggested_fields: _suggested,
        updated_at: _updated,
        ...values
      } = policy;
      await api("pricing/simple-policy/", "PUT", {
        expected_revision: revision,
        reason: "Solo borradores",
        values: { ...values, margin: ".60" },
      });
      const after = await api(`projects/${project.id}/`);
      expect(after.total_price_gross).toBe(frozen.total_price_gross);
      expect(after.versions).toEqual(frozen.versions);
      const access = await api(`documents/artifacts/${issued.artifact_id}/access/`, "POST");
      const unchanged = await page.request.get(access.signed_url);
      expect(await unchanged.body()).toEqual(bytes);
      await page.goto(path);
      await expect(total).toHaveText(formatMoney(frozen.total_price_gross, frozen.currency));
      await expect(source).toHaveText(
        formatMoney(repriced.positions[0].commercial.line_net, frozen.currency),
      );
      await capture(page, info, "06-issued-unchanged");

      // Explicit visual fixture only: no invented amount is sent to the API.
      // The real three-window calculation and issuance above remain untouched.
      const stress = structuredClone(current);
      const amount = "999999999999999.99";
      const longName = "日本の窓 🪟 " + "UbicacionSinEspacios".repeat(8);
      stress.name = "Ensayo visual · " + "Wiśniewska-Kowalczyk ".repeat(8);
      stress.client_name = "客户 🪟 " + "ApellidoMuyLargo".repeat(8);
      stress.position_count = 500;
      stress.working_price.project_gross = amount;
      stress.positions = Array.from({ length: 500 }, (_, index) => ({
        ...structuredClone(current.positions[0]),
        id: crypto.randomUUID(),
        position_index: index + 1,
        location_tag: `${index + 1} · ${longName}`,
        commercial: {
          ...current.positions[0].commercial,
          line_net: amount,
          unit_net: amount,
          source: "Dato sintético exclusivo del ensayo visual; no guardado.",
        },
      }));
      await page.route(
        (url) => url.pathname === `/api/v1/projects/${project.id}/`,
        (route) => route.fulfill({ json: stress }),
      );
      const stressStarted = Date.now();
      await page.goto(path);
      await expect(page.locator(".project-positions-count")).toHaveText("500", { timeout: 15_000 });
      expect(await page.locator(".position-row").count()).toBeLessThan(40);
      console.log(
        JSON.stringify({
          viewport,
          surface: "500-visual-rows",
          loadMs: Date.now() - stressStarted,
        }),
      );
      await capture(page, info, "07-500-windows");
      const search = page.getByPlaceholder("Buscar ventana", { exact: true });
      const searchStarted = Date.now();
      await search.fill("500 ·");
      await expect(page.locator(".position-row")).toHaveCount(1);
      console.log(
        JSON.stringify({ viewport, surface: "500-search", responseMs: Date.now() - searchStarted }),
      );
      await page
        .getByRole("button", {
          name: `¿De dónde sale el precio de 500 · ${longName}?`,
          exact: true,
        })
        .click();
      await capture(page, info, "08-large-breakdown");
      await page.keyboard.press("Escape");
      if (viewport.width === 1440) {
        for (const width of [1280, 1024, 320]) {
          await page.setViewportSize({ width, height: 900 });
          await capture(page, info, `09-width-${width}`);
        }
        await page.evaluate(() => {
          document.documentElement.style.fontSize = "200%";
        });
        await capture(page, info, "10-text-200-percent");
      }
    });
  });
}

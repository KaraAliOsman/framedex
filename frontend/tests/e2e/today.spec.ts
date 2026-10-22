import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, type Page, type TestInfo } from "@playwright/test";
import type { TodayResponse } from "../../src/api/generated/models";
import { test } from "./support/catalog-series-fixture";
import { environment } from "./support/environment";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  expect(
    (
      await new AxeBuilder({ page })
        .include(".today-page, .ui-dialog")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: false });
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`Hoy ${viewport.width}`, () => {
    test.use({ viewport });
    test("reviews a saved AI quotation, preserves the human send and starts a manual draft", async ({
      page,
      catalog,
    }, info) => {
      test.setTimeout(180_000);
      const contextRequest = page.waitForRequest(
        (request) => new URL(request.url()).pathname === "/api/v1/auth/me/",
      );
      await page.goto("/dashboard");
      const contextResponse = await (await contextRequest).response();
      const context = (await contextResponse!.json()) as { user: { id: string } };
      await expect(page.getByRole("heading", { name: "Todo al día", exact: true })).toBeVisible();
      const seeded = JSON.parse(
        execFileSync(
          environment("PYTHON") ?? "python",
          ["scripts/seed_today_e2e.py", catalog.organizationId, context.user.id],
          {
            cwd: fileURLToPath(new URL("../../../", import.meta.url)),
            encoding: "utf8",
            timeout: 120_000,
            env: { ...process.env, PYTHONUTF8: "1" },
          },
        ).trim(),
      ) as { issued: string; draft: string };
      const start = Date.now();
      await page.addInitScript(() => {
        const values = { lcpMs: 0, cls: 0 };
        Reflect.set(window, "todayPerformance", values);
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) values.lcpMs = entry.startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const shift = entry as PerformanceEntry & { value: number; hadRecentInput: boolean };
            if (!shift.hadRecentInput) values.cls += shift.value;
          }
        }).observe({ type: "layout-shift", buffered: true });
      });
      const response = page.waitForRequest(
        (request) => new URL(request.url()).pathname === "/api/v1/analytics/today/",
      );
      await page.reload();
      const today = (await (await (await response).response())!.json()) as TodayResponse;
      await expect(
        page.getByRole("heading", { name: "DEKOPEN preparó 1 cosa", exact: true }),
      ).toBeVisible();
      await expect(page.getByRole("heading", { name: /Juan$/ })).toBeVisible();
      expect(today.prepared.count).toBe(1);
      const send = today.actions.find((action) => action.kind === "quote_send")!;
      expect(send.href).toContain(seeded.issued);
      console.log(JSON.stringify({ viewport, surface: "Hoy", loadMs: Date.now() - start }));
      await capture(page, info, "01-today-real");
      console.log(
        JSON.stringify({
          viewport,
          surface: "Hoy-vitals",
          ...(await page.evaluate(
            () => Reflect.get(window, "todayPerformance") as { lcpMs: number; cls: number },
          )),
        }),
      );
      await page.getByRole("button", { name: "Revisar", exact: true }).click();
      const dialog = page.getByRole("dialog", { name: "Cotizaciones preparadas" });
      await expect(dialog.getByRole("link", { name: /Ventanas de la terraza/ })).toHaveAttribute(
        "href",
        `/projects/${seeded.draft}?section=quote`,
      );
      await capture(page, info, "02-prepared");
      await page.keyboard.press("Escape");
      await expect(page.getByRole("button", { name: "Revisar", exact: true })).toBeFocused();
      const writes: string[] = [];
      page.on("request", (request) => {
        if (request.method() !== "GET" && new URL(request.url()).pathname.startsWith("/api/"))
          writes.push(request.url());
      });
      await page.getByRole("link", { name: send.verb, exact: true }).click();
      await expect(page).toHaveURL(new RegExp(`/projects/${seeded.issued}\\?section=quote`));
      expect(writes).toEqual([]);
      await page.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Para hacer", exact: true })).toBeVisible();
      const created = page.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === "/api/v1/projects/" &&
          response.request().method() === "POST",
      );
      await page.getByRole("button", { name: "Nueva cotización", exact: true }).click();
      const result = (await (await created).json()) as { id: string };
      await expect(page).toHaveURL(new RegExp(`/projects/${result.id}/positions/new`));
      // P06 edits at every width: the first decision opens on phones too.
      await expect(
        page.getByRole("heading", {
          name: /Biblioteca de tipologías|¿Con qué serie la fabricas/,
        }),
      ).toBeVisible();
      await page.goto("/dashboard");

      // Stress data enters only through this test's API boundary. The picker is
      // injected by Playwright and never ships in the application bundle.
      const stress: TodayResponse = {
        ...today,
        actions: Array.from({ length: 1000 }, (_, index) => ({
          ...send,
          key: `fixture:${index}`,
          entity_code: `P-${index}`,
          entity_name: index === 0 ? "Ñ".repeat(255) : `Obra sintética ${index}`,
          title: index === 1 ? "Revisar " + "W".repeat(180) : send.title,
          amount: "99999999999999999999.99",
          currency: "CLP",
          consequence: index % 2 ? "blocking" : "overdue",
        })),
      };
      await page.route("**/api/v1/analytics/today/", (route) => {
        const mode = new URL(page.url()).searchParams.get("data");
        return route.fulfill({
          json:
            mode === "worst"
              ? stress
              : mode === "empty"
                ? { ...today, actions: [], pipeline: [], prepared: { count: 0, items: [] } }
                : today,
        });
      });
      await page.addInitScript(() => {
        window.addEventListener("DOMContentLoaded", () => {
          const picker = document.createElement("select");
          picker.setAttribute("aria-label", "Datos de prueba");
          picker.style.cssText =
            "position:fixed;bottom:8px;left:50%;transform:translateX(-50%);z-index:99999;background:white;color:black";
          for (const [value, label] of [
            ["demo", "Demo data"],
            ["worst", "Worst case · 1000"],
            ["empty", "Empty"],
          ])
            picker.add(new Option(label, value));
          picker.value = new URL(location.href).searchParams.get("data") ?? "demo";
          picker.onchange = () => {
            const url = new URL(location.href);
            url.searchParams.set("data", picker.value);
            location.assign(url);
          };
          document.body.append(picker);
        });
      });
      await page.goto("/dashboard?data=worst");
      await expect(
        page.getByRole("list", { name: "Acciones pendientes" }).getByRole("listitem"),
      ).toHaveCount(50);
      await expect(
        page.getByRole("button", { name: "Atención pendiente" }),
      ).toHaveAccessibleDescription("1000 acciones pendientes");
      await capture(page, info, "03-worst-1000");
      await page.getByRole("button", { name: "Siguiente", exact: true }).click();
      await expect(page.getByText("51–100 de 1000 acciones", { exact: true })).toBeVisible();
      await page.setViewportSize({ width: 320, height: 844 });
      await page.getByRole("button", { name: "Anterior", exact: true }).click();
      await capture(page, info, "04-worst-320");
      await page.evaluate(() => {
        document.documentElement.style.fontSize = "200%";
        window.scrollTo(0, 0);
      });
      await capture(page, info, "05-worst-200");
      await page.getByRole("combobox", { name: "Datos de prueba" }).selectOption("empty");
      await expect(page.getByRole("heading", { name: "Todo al día", exact: true })).toBeVisible();
      await capture(page, info, "06-empty");
    });
  });
}

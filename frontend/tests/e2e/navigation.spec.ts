import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import type { MembershipRoleEnum } from "../../src/api/generated/models";
import { test } from "./support/catalog-series-fixture";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  expect(
    (
      await new AxeBuilder({ page })
        .include(".app-rail, .app-topbar, .advanced-features")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true });
}

for (const role of [
  "OWNER",
  "ESTIMATOR",
  "WORKSHOP_MANAGER",
  "OPERATOR",
  "INSTALLER",
] as MembershipRoleEnum[]) {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    test.describe(`${role} ${viewport.width}`, () => {
      test.use({ catalogRole: role, viewport, lightCatalog: true });
      test("opens Hoy, filters destinations by role and retains legacy links", async ({
        page,
        catalog,
      }, info) => {
        test.setTimeout(180_000);
        expect(catalog.organizationId).toBeTruthy();
        const office = ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(role);
        await page.goto("/");
        await expect(page).toHaveURL(/\/dashboard$/);
        await expect(page.getByRole("heading", { name: "Pendientes", exact: true })).toBeVisible();
        const rail = page.locator(".app-rail");
        const navigation = page.getByRole("navigation", {
          name: "Navegación principal",
          exact: true,
        });
        if (viewport.width < 600)
          await page.getByRole("button", { name: "Menú de navegación", exact: true }).click();
        await expect(navigation.getByRole("link")).toHaveText(
          office ? ["Hoy", "Obras", "Taller", "Catálogo"] : ["Hoy", "Taller"],
        );
        await expect(rail.getByRole("link", { name: "Empresa", exact: true })).toHaveCount(
          office ? 1 : 0,
        );
        await expect(rail.getByRole("link", { name: "Clientes", exact: true })).toHaveCount(0);
        await expect(navigation.getByRole("link", { name: "Hoy", exact: true })).toHaveAttribute(
          "aria-current",
          "page",
        );
        await capture(page, info, "01-navigation");
        if (viewport.width < 600) {
          await page.keyboard.press("Escape");
          await expect(
            page.getByRole("button", { name: "Menú de navegación", exact: true }),
          ).toBeFocused();
        }
        if (office) {
          if (role !== "WORKSHOP_MANAGER") {
            await page.goto("/quotes?q=ensayo");
            await expect(
              page.getByRole("heading", { name: "Cotizaciones", exact: true, level: 1 }),
            ).toBeVisible();
            await expect(
              page.getByRole("searchbox", { name: "Buscar proyecto o cliente", exact: true }),
            ).toHaveValue("ensayo");
          }
          await page.goto("/projects");
          await expect(
            page.getByRole("heading", { name: "Obras", exact: true, level: 1 }),
          ).toBeVisible();
          await page.goto("/clients");
          await expect(
            page.getByRole("heading", { name: "Clientes", exact: true, level: 1 }),
          ).toBeVisible();
          await page
            .getByRole("button", { name: "Buscar o ejecutar un comando", exact: true })
            .click();
          await page.getByRole("combobox").fill("Clientes");
          await expect(page.getByRole("option", { name: /Clientes/ }).first()).toBeVisible();
          await page.keyboard.press("Escape");
          await page.goto("/settings/advanced");
          await expect(
            page.getByRole("heading", { name: "Funciones avanzadas", exact: true }),
          ).toBeVisible();
          await expect(page.getByRole("link", { name: "Mecanizado CNC", exact: true })).toHaveCount(
            role === "ESTIMATOR" ? 0 : 1,
          );
          await expect(
            page.getByRole("link", { name: "Listas de costos y reglas avanzadas", exact: true }),
          ).toHaveCount(role === "OWNER" ? 1 : 0);
          await capture(page, info, "02-advanced");
        } else {
          await page.goto("/settings/advanced");
          await expect(
            page.getByText("El dueño, vendedor o jefe de taller consulta estas funciones."),
          ).toBeVisible();
          await expect(page.getByRole("link", { name: "Mecanizado CNC", exact: true })).toHaveCount(
            0,
          );
        }
      });
    });
  }
}

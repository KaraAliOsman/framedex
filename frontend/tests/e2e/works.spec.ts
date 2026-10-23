import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";
import type { MembershipRoleEnum, WorksResponse, StageEnum } from "../../src/api/generated/models";
import { test } from "./support/catalog-series-fixture";

async function capture(page: Page, info: TestInfo, name: string) {
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );
  expect(
    (
      await new AxeBuilder({ page })
        .include(".projects-home")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: false });
}

for (const role of ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"] as MembershipRoleEnum[]) {
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    test.describe(`${role} Works ${viewport.width}`, () => {
      test.use({ catalogRole: role, catalogProjects: true, lightCatalog: true, viewport });
      test("opens real works by stage and keeps 500 extreme records usable", async ({
        page,
        catalog,
      }, info) => {
        test.setTimeout(180_000);
        const response = page.waitForResponse(
          (response) =>
            new URL(response.url()).pathname === "/api/v1/projects/works/" &&
            response.request().method() === "GET",
        );
        const start = Date.now();
        await page.goto("/projects");
        const real = (await (await response).json()) as WorksResponse;
        const works = page.getByRole("list", { name: "Obras", exact: true });
        await expect(works.getByRole("link")).toHaveCount(2);
        expect(real.items).toHaveLength(2);
        expect(real.items.every((item) => item.progress?.stage === "QUOTING")).toBe(true);
        const issued = real.items.find((item) => item.id === catalog.projects!.issued)!;
        expect(issued.progress?.quoted_total).not.toBeNull();
        await expect(
          page.getByRole("button", { name: "Cotizando · 2", exact: true }),
        ).toBeVisible();
        await expect(
          page.getByRole("button", { name: "Nueva cotización", exact: true }),
        ).toHaveCount(role === "WORKSHOP_MANAGER" ? 0 : 1);
        console.log(
          JSON.stringify({ surface: "Obras", role, viewport, loadMs: Date.now() - start }),
        );
        await capture(page, info, "01-works-real");
        const link = works.getByRole("link", { name: /Casa Pérez/ });
        await link.focus();
        await page.keyboard.press("Enter");
        await expect(page).toHaveURL(new RegExp(`/projects/${catalog.projects!.issued}$`));
        await page.goBack();
        await expect(works).toBeVisible();
        await page.getByRole("searchbox", { name: "Buscar obra o cliente" }).fill("terraza");
        await expect(works.getByRole("link")).toHaveCount(1);
        await expect(works.getByRole("link")).toContainText("Ventanas de la terraza");
        await page.getByRole("searchbox", { name: "Buscar obra o cliente" }).fill("");

        if (role !== "WORKSHOP_MANAGER") {
          await page.goto("/quotes?q=REV-A&attention=unshared&phase=QUOTED&currency=CLP&offset=0");
          await expect(page).toHaveURL(/\/projects\?.*view=quotes/);
          const legacy = new URL(page.url()).searchParams;
          for (const [key, value] of Object.entries({
            q: "REV-A",
            attention: "unshared",
            phase: "QUOTED",
            currency: "CLP",
            offset: "0",
          }))
            expect(legacy.get(key)).toBe(value);
          await expect(works.getByRole("link")).toHaveCount(1);
          await expect(works.getByRole("link")).toHaveAttribute(
            "href",
            `/projects/${catalog.projects!.issued}?section=quote`,
          );
          await expect(works).toContainText("Pendiente de envío");
          await capture(page, info, "01b-works-quotation");
          await page.getByLabel("Seguimiento", { exact: true }).selectOption("viewed");
          await expect(page.getByText("Ninguna obra coincide", { exact: true })).toBeVisible();
          await page.goto("/projects");
          await expect(works.getByRole("link")).toHaveCount(2);
        }

        // API-bound stress evidence only: no numeric fixture or picker ships.
        const stages: StageEnum[] = [
          "QUOTING",
          "SENT",
          "ACCEPTED",
          "WORKSHOP",
          "INSTALLED",
          "TO_COLLECT",
          "CLOSED",
          "CANCELLED",
        ];
        const worst = {
          items: Array.from({ length: 500 }, (_, index) => ({
            ...issued,
            id: `fixture-${String(index).padStart(3, "0")}`,
            code: `P-${index}`,
            name:
              index === 0 ? "Ñ".repeat(255) : `Obra sintética ${String(index).padStart(3, "0")}`,
            client_name: index === 1 ? "W".repeat(255) : "Cliente de prueba",
            position_count: index === 0 ? 0 : 500,
            quotation: null,
            progress: {
              stage: stages[index % stages.length]!,
              reason: "Etapa sintética para romper la vista",
              quoted_total: "99999999999999999999.99",
              currency: "CLP",
            },
          })),
        };
        await page.route("**/api/v1/projects/works/**", (route) => {
          const query = new URL(route.request().url()).searchParams;
          const data = new URL(page.url()).searchParams.get("data");
          if (!data || data === "demo") return route.fulfill({ json: real });
          const matching = data === "empty" ? [] : worst.items;
          const counts = Object.fromEntries(
            stages.map((stage) => [
              stage,
              matching.filter((item) => item.progress.stage === stage).length,
            ]),
          );
          const filtered = matching.filter(
            (item) => !query.get("stage") || item.progress.stage === query.get("stage"),
          );
          const offset = Number(query.get("offset") ?? 0);
          return route.fulfill({
            json: {
              items: filtered.slice(offset, offset + 50),
              counts,
              matching: matching.length,
              total: filtered.length,
              offset,
              limit: 50,
            },
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
              ["worst", "Worst case · 500"],
              ["empty", "Empty"],
            ])
              picker.add(new Option(label, value));
            picker.value = new URL(location.href).searchParams.get("data") ?? "worst";
            picker.onchange = () => {
              const url = new URL(location.href);
              url.search = `?data=${picker.value}`;
              location.assign(url);
            };
            document.body.append(picker);
          });
        });
        await page.goto("/projects?data=worst");
        await expect(works.getByRole("link")).toHaveCount(50);
        await expect(page.getByRole("button", { name: "Todas · 500", exact: true })).toBeVisible();
        await capture(page, info, "02-works-500");
        await page.getByRole("button", { name: "Siguiente", exact: true }).click();
        await expect(page.getByText("51–100 de 500 obras", { exact: true })).toBeVisible();
        await page.goto("/projects?data=worst&offset=450");
        await expect(page.getByText("451–500 de 500 obras", { exact: true })).toBeVisible();
        await expect(page.getByRole("button", { name: "Siguiente", exact: true })).toBeDisabled();
        await page.getByRole("button", { name: "En taller · 63", exact: true }).click();
        await expect(page).toHaveURL(/stage=WORKSHOP/);
        await expect(page).not.toHaveURL(/offset=/);
        await expect(works.getByRole("link")).toHaveCount(50);
        await expect(works).toContainText("En taller");
        await capture(page, info, "03-works-stage");
        await page.setViewportSize({ width: 320, height: 844 });
        await page.evaluate(() => {
          document.documentElement.style.fontSize = "200%";
          window.scrollTo(0, 0);
        });
        await capture(page, info, "04-works-320-200");
        await page.getByRole("combobox", { name: "Datos de prueba" }).selectOption("empty");
        await expect(page.getByText("Aún no hay cotizaciones", { exact: true })).toBeVisible();
        await capture(page, info, "05-works-empty");
      });
    });
  }
}

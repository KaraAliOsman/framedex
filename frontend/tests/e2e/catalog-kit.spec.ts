import { expect, type Page } from "@playwright/test";

import type { KitResponse } from "../../src/api/generated/models";
import { t } from "../../src/i18n/es-CL";
import { test } from "./support/manual-project-fixture";

test.use({
  fixtureRole: "WORKSHOP_MANAGER",
  viewport: { width: 1366, height: 768 },
});

const collection = "/api/v1/catalogs/hardware-kits/";

async function exchange(
  page: Page,
  method: string,
  path: string,
  status: number,
  action: () => Promise<unknown>,
) {
  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) =>
        candidate.request().method() === method && new URL(candidate.url()).pathname === path,
    ),
    action(),
  ]);
  expect(response.status(), `${method} ${path}`).toBe(status);
  return response;
}

async function loadCatalog(page: Page): Promise<KitResponse[]> {
  const response = await exchange(page, "GET", collection, 200, () =>
    page.goto("/catalogs/systems"),
  );
  await expect(
    page.getByRole("heading", {
      name: t("catalog.title"),
      exact: true,
    }),
  ).toBeVisible();
  return ((await response.json()) as { items: KitResponse[] }).items;
}

async function openKit(page: Page, name: string): Promise<void> {
  await page
    .getByRole("button", {
      name: t("catalog.unassignedKits"),
      exact: true,
    })
    .click();
  await page
    .getByRole("button", {
      name: `${t("catalog.edit")} ${name}`,
      exact: true,
    })
    .click();
  await expect(page.locator("form.catalog-editor")).toBeVisible();
}

test("manager persists exact typed kit contents through real UI and DB", async ({
  page,
  manual,
}, info) => {
  test.setTimeout(120_000);

  const existing = await loadCatalog(page);
  const source = existing.find(
    (kit) => kit.system_id === manual.systemId && kit.sku === "KIT-TURN",
  );
  expect(source).toBeDefined();

  const name = `E2E SYNTHETIC kit ${crypto.randomUUID()}`;
  const quantity = "1.00000000000000000001";
  const updatedQuantity = "2.00000000000000000003";
  const form = page.locator("form.catalog-editor");

  // Standalone kits are explicitly supported by the current nullable system_id.
  // This slice tests catalog persistence, not engine selection of generic kits.
  await page
    .getByRole("button", {
      name: t("catalog.unassignedKits"),
      exact: true,
    })
    .click();
  await page
    .getByRole("button", {
      name: t("catalog.create"),
      exact: true,
    })
    .click();

  const values: Record<string, unknown> = {
    ...source,
    system_id: null,
    sku: `E2E-${crypto.randomUUID()}`,
    name,
    is_active: false,
  };
  const fields = [
    "system_id",
    "sku",
    "name",
    "opening_type",
    "rail_type",
    "is_active",
    "min_leaf_width_mm",
    "max_leaf_width_mm",
    "min_leaf_height_mm",
    "max_leaf_height_mm",
    "max_leaf_weight_kg",
    "carriages_qty",
    "stay_arms_qty",
    "weight_kg",
    "carriage_capacity_kg",
  ];

  // Explicit writable fields only; synthetic dimensional authorities are copied
  // from the real API as strings, never calculated in the browser test.
  for (const field of fields) {
    const control = form.locator(`#catalog-hardware-kits-${field}`);
    const value = values[field] == null ? "" : String(values[field]);
    if (await control.evaluate((element) => element.tagName === "SELECT")) {
      await control.selectOption(value);
    } else {
      await control.fill(value);
    }
  }

  await form
    .getByRole("button", {
      name: t("catalog.addComponent"),
      exact: true,
    })
    .click();

  const component = {
    sku: "E2E-PART",
    name: 'Componente sintético "exacto"',
    qty: quantity,
    unit: "unit",
    // Components without a declared category persist the serializer default.
    category: "OTHER",
  };
  const componentLabel = (key: "sku" | "name" | "qty" | "unit") =>
    `${t(`catalog.field.${key}`)} · ${t("catalog.component")} 1`;

  for (const key of ["sku", "name", "qty", "unit"] as const) {
    await form.getByLabel(componentLabel(key), { exact: true }).fill(component[key]);
  }

  const createdResponse = await exchange(page, "POST", collection, 201, () =>
    form
      .getByRole("button", {
        name: t("catalog.save"),
        exact: true,
      })
      .click(),
  );
  const created = (await createdResponse.json()) as KitResponse;
  expect(created).toMatchObject({
    name,
    system_id: null,
    is_active: false,
    read_only: false,
    contents: [component],
  });
  await expect(form).toHaveCount(0);

  // Reload the entire application, then reopen from persisted catalog data.
  const reloaded = await loadCatalog(page);
  expect(reloaded.find((kit) => kit.id === created.id)).toEqual(created);
  await openKit(page, name);
  await expect(form.getByLabel(componentLabel("qty"), { exact: true })).toHaveValue(quantity);

  await form.getByLabel(componentLabel("qty"), { exact: true }).fill(updatedQuantity);
  const updatedResponse = await exchange(page, "PATCH", `${collection}${created.id}/`, 200, () =>
    form
      .getByRole("button", {
        name: t("catalog.save"),
        exact: true,
      })
      .click(),
  );
  expect(updatedResponse.request().headers()["if-match"]).toBe(`"${created.revision}"`);
  const updated = (await updatedResponse.json()) as KitResponse;
  expect(updated.contents).toEqual([{ ...component, qty: updatedQuantity }]);
  await expect(form).toHaveCount(0);

  const reopened = await loadCatalog(page);
  expect(reopened.find((kit) => kit.id === created.id)).toEqual(updated);
  await openKit(page, name);
  await expect(form.getByLabel(componentLabel("qty"), { exact: true })).toHaveValue(
    updatedQuantity,
  );

  // Read JSONB as text: assert an exact JSON NUMBER without JSON.parse rounding.
  const rows = await manual.readRows(
    "hardware_kits",
    `id=eq.${created.id}&org_id=eq.${manual.organizationId}&select=contents::text`,
  );
  expect(rows).toHaveLength(1);
  expect(typeof rows[0]!.contents).toBe("string");
  expect(rows[0]!.contents).toMatch(/"qty"\s*:\s*2\.00000000000000000003\s*[,}]/);

  await form.getByLabel(componentLabel("qty"), { exact: true }).scrollIntoViewIfNeeded();
  await page.evaluate(() => document.fonts.ready);
  const screenshot = info.outputPath("catalog-exact-kit-1366x768.png");
  await page.screenshot({
    path: screenshot,
    fullPage: false,
    animations: "disabled",
  });
  await info.attach("catalog-exact-kit-1366x768", {
    path: screenshot,
    contentType: "image/png",
  });

  const deleted = await exchange(page, "DELETE", `${collection}${created.id}/`, 204, async () => {
    await form
      .getByRole("button", {
        name: t("catalog.delete"),
        exact: true,
      })
      .click();
    // §F: in-app ConfirmDialog replaced window.confirm — assert the same
    // warning text, then confirm through the product surface.
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText(t("catalog.confirmDelete"));
    await dialog.getByRole("button", { name: t("ui.confirm"), exact: true }).click();
  });
  expect(deleted.request().headers()["if-match"]).toBe(`"${updated.revision}"`);
  await expect(form).toHaveCount(0);

  expect(
    await manual.readRows(
      "hardware_kits",
      `id=eq.${created.id}&org_id=eq.${manual.organizationId}&select=id`,
    ),
  ).toEqual([]);
});

import { api, browser, context, fs, expect, base } from "./p12-fixture.mjs";
import { collectPresentationFindings } from "./ux-capture/collect.ts";
import { detectTextFindings } from "./ux-capture/detectors.ts";

const out = "docs/redesign/captures/produccion-estaciones/estados";
const b = await browser(),
  records = [];
async function capture(page, state) {
  const findings = [
    ...detectTextFindings(await page.locator(".production-page").innerText()),
    ...(await collectPresentationFindings(page, true, ".production-page,.production-page *")),
  ];
  expect(findings).toEqual([]);
  await page.screenshot({ path: `${out}/${state}.png`, fullPage: true });
  records.push({ state, findings, result: "PASA" });
}
try {
  await fs.mkdir(out, { recursive: true });
  await api("/production/operator-station/", "PUT", { station_code: "PACK" }, "operator");
  const c = await context(b, "operator", 1024, "dark"),
    page = await c.newPage();
  await page.goto(base + "/production");
  await expect(page.getByText("Tu estación no tiene OT pendientes", { exact: true })).toBeVisible();
  await capture(page, "vacio");
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/production/operator-station/", async (route) => {
    await gate;
    await route.continue();
  });
  await page.reload();
  await expect(page.getByLabel("Cargando tu estación", { exact: true })).toBeVisible();
  await capture(page, "carga");
  release();
  await page.waitForLoadState("networkidle");
  await page.unroute("**/production/operator-station/");
  await page.route("**/production/operator-station/", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        error: { code: "transport_unavailable", detail: "La conexión de taller falló. Reintenta." },
      }),
    }),
  );
  await page.reload();
  await expect(page.getByText("No se pudo cargar la estación", { exact: true })).toBeVisible();
  await capture(page, "error");
  await page.unroute("**/production/operator-station/");
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.getByText("Tu estación no tiene OT pendientes", { exact: true })).toBeVisible();
  records.push({ flow: "error de transporte y reintento real", result: "PASA" });
  await page.route("**/production/operator-station/", (route) =>
    route.fulfill({
      status: 403,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "role_forbidden",
          detail: "Tu rol no tiene permiso de taller. Pide al dueño que revise tu membresía.",
        },
      }),
    }),
  );
  await page.reload();
  await expect(page.locator(".ui-empty--denied")).toBeVisible();
  await capture(page, "sin-permiso");
  await page.unroute("**/production/operator-station/");
  const state = JSON.parse(await fs.readFile(".run/p12-fixture.json", "utf8"));
  await api("/production/operator-station/", "PUT", { station_code: "QC" }, "operator");
  await page.goto(`${base}/production?order=${state.orderId}`);
  await expect(page.locator(".production-station-task .ui-empty--blocked")).toBeVisible();
  await capture(page, "bloqueado");
  const sessionOrder = await api(
    `/production/orders/${state.orderId}/`,
    "GET",
    undefined,
    "operator",
  );
  expect(sessionOrder).not.toHaveProperty("delivery_address");
  const trace = await api(
    `/production/orders/${state.orderId}/trace/`,
    "GET",
    undefined,
    "operator",
  );
  expect(trace.project).not.toHaveProperty("client_name");
  for (const [path, method, body] of [
    ["/production/prep/", "GET"],
    [
      `/production/orders/${state.orderId}/qc-remake/`,
      "POST",
      {
        confirmed: true,
        operation_key: crypto.randomUUID(),
        note: "P12 DEMO · rechazo de permiso",
        item_code: "",
      },
    ],
  ]) {
    await expect(api(path, method, body, "operator")).rejects.toThrow(/403/);
  }
  records.push({ flow: "proyecciones privadas y dos permisos reales de API", result: "PASA" });
} finally {
  await fs.writeFile(`${out}/informe.json`, JSON.stringify(records, null, 2));
  await b.close();
}
console.log("P12 cinco estados, reintento y permisos PASA");

import { chromium, expect } from "@playwright/test";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { detectTextFindings } from "./ux-capture/detectors.ts";

const base = "http://127.0.0.1:5173";
const api = "http://127.0.0.1:8000/api/v1";
const supa = process.env.SUPABASE_URL;
const anon = process.env.SUPABASE_ANON_KEY;
const org = "548b9ce5-746b-5a4a-9127-733c4dcd0582";
if (new URL(supa).port !== "25331")
  throw new Error("P02 requires the owned framedex-cola fixture.");
const flowOut = fileURLToPath(
  new URL("../../docs/redesign/captures/identificadores-humanos/recorrido", import.meta.url),
);
const reviewOnly = process.argv.includes("--review-only");
const out = reviewOnly ? flowOut + "/revision" : flowOut;
const state = JSON.parse(await fs.readFile(flowOut + "/http-flow.json", "utf8"));
const browser = await chromium.launch({ headless: true });
const sessions = new Map();
const records = [];
let lastPage;

async function auth(role) {
  if (!sessions.has(role)) {
    const response = await fetch(supa + "/auth/v1/token?grant_type=password", {
      method: "POST",
      headers: { apikey: anon, "Content-Type": "application/json" },
      body: JSON.stringify({
        email: `demo-${role}@fixture.dekopen.local`,
        password: "Demo-Fixture-2026!",
      }),
    });
    if (!response.ok) throw new Error("Local login failed: " + response.status);
    sessions.set(role, await response.json());
  }
  return sessions.get(role);
}
async function request(role, path) {
  const session = await auth(role);
  const response = await fetch(api + path, {
    headers: { Authorization: "Bearer " + session.access_token, "X-Organization-ID": org },
  });
  if (!response.ok) throw new Error(path + ": " + response.status);
  return response.json();
}
async function pageFor(role, theme, viewport) {
  const session = await auth(role);
  const context = await browser.newContext({
    viewport,
    storageState: {
      cookies: [],
      origins: [
        {
          origin: base,
          localStorage: [
            { name: "sb-127-auth-token", value: JSON.stringify(session) },
            { name: `dekopen.active_org.${session.user.id}`, value: org },
            { name: "dekopen.theme", value: theme },
          ],
        },
      ],
    },
  });
  const page = await context.newPage();
  lastPage = page;
  page.errors = [];
  page.on("pageerror", (error) => page.errors.push(error.message));
  page.on("dialog", (dialog) => dialog.accept());
  return page;
}
async function capture(page, name, scope, simulation = null) {
  if ([".production-packing", ".production-action-error"].includes(scope))
    await page.locator(scope).evaluate((node) => node.scrollIntoView({ block: "start" }));
  if ([".inventory-label", ".purchasing-receipts", ".production-labels"].includes(scope))
    await page.locator(scope).scrollIntoViewIfNeeded();
  await page.mouse.move(2, 2);
  await page.screenshot({ path: out + "/" + name + ".png" });
  const text = await page.locator(scope).innerText();
  const numeric = detectTextFindings(text).filter((issue) =>
    ["uuid", "hex", "decimal-precision", "percent-precision"].includes(issue.kind),
  );
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  records.push({ name, scope, simulation, numeric, overflow, errors: [...page.errors] });
  expect(numeric).toEqual([]);
  expect(page.errors).toEqual([]);
  expect(overflow).toBe(false);
}
async function palette(page, code) {
  await page.keyboard.press("Control+k");
  await page.locator(".command-palette input").fill(code);
  const option = page.getByRole("option").filter({ hasText: code }).first();
  await expect(option).toBeVisible({ timeout: 15000 });
  await option.click();
  await page.waitForLoadState("networkidle");
}

try {
  await fs.mkdir(out, { recursive: true });
  const first = state.work_orders[0];
  const labels = await request("manager", `/production/orders/${first.order}/labels/`);
  const piece = labels.piece_labels[0];
  const viewports = [
    { width: 1440, height: 900 },
    { width: 1280, height: 800 },
    { width: 1024, height: 768 },
    { width: 390, height: 844 },
  ];
  if (
    !["--units-only", "--print-only", "--labels-only", "--review-only"].some((flag) =>
      process.argv.includes(flag),
    )
  ) {
    for (const viewport of viewports)
      for (const theme of ["light", "dark"]) {
        const key = `${viewport.width}-${theme}`;
        const page = await pageFor("manager", theme, viewport);
        await page.goto(base + "/purchasing");
        await page.waitForLoadState("networkidle");
        for (const [code, path] of Object.entries(state.addresses)) {
          await palette(page, code);
          const url = new URL(page.url());
          const expected = new URL(path, base);
          expect(url.pathname).toBe(expected.pathname);
          for (const parameter of ["order", "remnant", "receipt"]) {
            if (expected.searchParams.has(parameter))
              expect(url.searchParams.get(parameter)).toBe(expected.searchParams.get(parameter));
          }
          if (code.startsWith("REC-")) {
            await expect(page.locator(".purchasing-receipts tr[aria-current=true]")).toContainText(
              code,
            );
            await capture(page, `recepcion-${key}`, ".purchasing-receipts");
          } else if (code.startsWith("RT-")) {
            const row = page.locator(".inventory-remnants tr[aria-current=true]");
            await expect(row).toContainText(code);
            await row.getByRole("button", { name: "Etiqueta", exact: true }).click();
            await expect(page.locator(".inventory-label")).toContainText(code);
            await expect(page.locator(".inventory-label svg")).toBeVisible();
            expect(
              await page
                .locator(".inventory-label svg")
                .evaluate((svg) => getComputedStyle(svg).backgroundColor),
            ).toBe("rgb(255, 255, 255)");
            await capture(page, `etiqueta-retazo-${key}`, ".inventory-label");
          } else if (code.startsWith("OC-")) {
            await expect(
              page.locator(".purchasing-order").filter({ hasText: code }).first(),
            ).toBeVisible();
            await capture(page, `compra-${key}`, ".purchasing-orders");
          } else {
            await expect(page.locator(".production-detail")).toContainText(code, {
              timeout: 15000,
            });
            await capture(page, `orden-taller-${key}`, ".production-detail");
          }
        }
        await page.goto(new URL(piece.qr_payload, base).href);
        await page.waitForLoadState("networkidle");
        await expect(page.locator(".production-trace-matches")).toContainText(piece.code);
        await expect(page.locator(".production-detail")).toContainText(first.code, {
          timeout: 15000,
        });
        expect(new URL(page.url()).searchParams.get("order")).toBe(first.order);
        await capture(page, `qr-directo-${key}`, ".production-trace-matches");
        await page.goto(base + "/production");
        await page.waitForLoadState("networkidle");
        const scan = page.locator(".production-trace-lookup");
        await scan.locator("input").fill(piece.qr_payload);
        await scan.getByRole("button").click();
        await expect(page.locator(".production-trace-matches")).toContainText(piece.code);
        await expect(page).toHaveURL(new RegExp("order=" + first.order));
        await expect(page.locator(".production-detail")).toContainText(first.code, {
          timeout: 15000,
        });
        await capture(page, `qr-escaneado-${key}`, ".production-trace-matches");
        await page.context().close();
      }

    const readonly = await pageFor("estimator", "light", viewports[0]);
    await readonly.goto(
      base + state.addresses[Object.keys(state.addresses).find((code) => code.startsWith("RT-"))],
    );
    await expect(readonly.locator(".inventory-workspace")).toContainText("Solo lectura");
    await expect(
      readonly
        .locator(".inventory-workspace")
        .getByRole("button", { name: "Registrar retazo", exact: true }),
    ).toHaveCount(0);
    await capture(readonly, "solo-lectura", ".inventory-workspace");
    await readonly.context().close();

    const denied = await pageFor("operator", "dark", viewports[3]);
    await denied.goto(base + "/purchasing");
    await expect(denied.getByText("Sin acceso", { exact: true })).toBeVisible();
    await capture(denied, "sin-permiso", "main");
    await denied.context().close();

    const missing = await pageFor("manager", "light", viewports[0]);
    await missing.goto(base + "/purchasing?remnant=00000000-0000-0000-0000-000000000000");
    await expect(missing.locator(".inventory-workspace")).toContainText(
      "No se encontró el retazo en esta organización",
    );
    await capture(missing, "direccion-no-disponible", ".inventory-workspace");
    await missing.context().close();

    for (const mode of ["vacio", "error", "cargando"]) {
      const page = await pageFor("manager", "dark", viewports[0]);
      let release;
      const hold = new Promise((resolve) => {
        release = resolve;
      });
      const pattern = "**/api/v1/inventory/remnants/**";
      await page.route(pattern, async (route) => {
        if (mode === "cargando") {
          await hold;
          await route.continue();
        } else if (mode === "vacio")
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ remnants: [] }),
          });
        else
          await route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({
              code: "unavailable",
              detail: "Network failure injected by P02 verifier",
            }),
          });
      });
      await page.goto(base + "/purchasing");
      const stock = page.locator(".inventory-workspace");
      await expect(stock).toBeVisible();
      if (mode === "cargando") await expect(stock).toContainText("Cargando retazos y movimientos");
      else if (mode === "error")
        await expect(stock).toContainText("No se pudo cargar el inventario");
      else await expect(stock).toContainText("No hay retazos");
      await capture(
        page,
        `estado-${mode}`,
        ".inventory-workspace",
        "HTTP response controlled by test; business flow uses real fixture",
      );
      release();
      await page.unrouteAll({ behavior: "wait" });
      if (mode === "error") {
        await stock.getByRole("button", { name: "Reintentar" }).click();
        await expect(stock.locator(".inventory-remnants")).toBeVisible();
      }
      await page.context().close();
    }
  }
  if (reviewOnly) {
    for (const viewport of viewports)
      for (const theme of ["light", "dark"]) {
        const key = `${viewport.width}-${theme}`;
        const page = await pageFor("manager", theme, viewport);
        await page.goto(new URL(piece.qr_payload, base).href);
        await expect(page.locator(".production-trace-matches")).toContainText(piece.code);
        const scan = page.locator(".production-trace-lookup");
        await scan.locator("input").fill("https://[invalid/production?order=bad&piece=P01-U01-M01");
        const malformedResponse = page.waitForResponse(
          (response) =>
            response.url().includes("/production/pieces/") && response.request().method() === "GET",
        );
        await scan.getByRole("button").click();
        expect((await malformedResponse).status()).toBe(422);
        await expect(page.locator(".production-action-error")).toContainText(
          "La dirección escaneada no es válida. Vuelve a escanear la etiqueta de la pieza.",
        );
        await expect(page.locator(".production-trace-matches")).toHaveCount(0);
        await capture(page, `direccion-invalida-${key}`, ".production-action-error");

        const tracePattern = "**/api/v1/production/pieces/**/trace/";
        await page.route(tracePattern, (route) =>
          route.fulfill({
            status: 422,
            contentType: "application/json",
            body: JSON.stringify({
              error: {
                code: "work_order_piece_order_required",
                detail:
                  "El código necesita una orden para buscar en este historial. Escanea el QR de la etiqueta, que incluye la OT.",
              },
            }),
          }),
        );
        await scan.locator("input").fill(piece.code);
        await scan.getByRole("button").click();
        await expect(page.locator(".production-action-error")).toContainText(
          "El código necesita una orden",
        );
        await expect(page.locator(".production-trace-matches")).toHaveCount(0);
        await capture(
          page,
          `requiere-orden-${key}`,
          ".production-action-error",
          "HTTP 422 injected; the real 101-order boundary is verified by PostgreSQL integration.",
        );
        await page.unrouteAll({ behavior: "wait" });
        await scan.locator("input").fill(piece.qr_payload);
        await scan.getByRole("button").click();
        await expect(page.locator(".production-trace-matches")).toContainText(piece.code);
        await expect(page.locator(".production-action-error")).toHaveCount(0);
        await expect(page.locator(".production-detail")).toContainText(first.code);

        const labelsPattern = `**/api/v1/production/orders/${first.order}/labels/`;
        for (const mode of ["invalidado", "sin-plan"]) {
          const reason =
            (mode === "invalidado"
              ? "El plan de corte fue invalidado al liberar material. "
              : "Sin dato · la orden no tiene un plan de corte vigente. ") +
            "Optimiza la orden antes de imprimir etiquetas de piezas.";
          await page.route(labelsPattern, (route) =>
            route.fulfill({
              status: 200,
              contentType: "application/json",
              body: JSON.stringify({
                ...labels,
                piece_labels: [],
                piece_labels_blocked_reason: reason,
              }),
            }),
          );
          await page.getByRole("button", { name: "Etiquetas", exact: true }).click();
          const packing = page.locator(".production-packing");
          await expect(packing.getByRole("status")).toContainText(reason);
          const codes = await packing
            .locator(".production-labels .production-label-code")
            .allTextContents();
          expect(codes).toEqual(labels.labels.map((label) => label.label_code));
          expect(codes).not.toContain(piece.code);
          await capture(
            page,
            `etiquetas-${mode}-${key}`,
            ".production-packing",
            "HTTP labels response injected from the real fixture manifest; stale/missing plans are covered in backend tests.",
          );
          await packing.getByRole("link", { name: "Revisar plan de corte" }).click();
          await expect(page).toHaveURL(/#production-cut-plan$/);
          await expect(page.locator("#production-cut-plan")).toBeInViewport();
          await page.unrouteAll({ behavior: "wait" });
        }
        await page.getByRole("button", { name: "Etiquetas", exact: true }).click();
        await expect(page.locator(".production-labels")).toContainText(piece.code);
        await expect(page.locator(".production-packing").getByRole("status")).toHaveCount(0);
        await page.context().close();
      }
  }
  if (process.argv.includes("--units-only")) {
    const unit = labels.labels[0];
    for (const viewport of viewports)
      for (const theme of ["light", "dark"]) {
        const page = await pageFor("manager", theme, viewport);
        await page.goto(new URL(unit.qr_payload, base).href);
        await expect(page.locator(".production-trace-matches")).toContainText(first.code, {
          timeout: 15000,
        });
        await expect(page.locator(".production-detail")).toContainText(first.code, {
          timeout: 15000,
        });
        expect(new URL(page.url()).searchParams.get("order")).toBe(first.order);
        await page.getByRole("button", { name: "Etiquetas", exact: true }).click();
        await expect(page.locator(".production-labels")).toContainText(piece.code);
        await capture(page, `etiquetas-unidad-${viewport.width}-${theme}`, ".production-labels");
        if (viewport.width === 1440) {
          await page.evaluate(() => {
            window.print = () =>
              document.documentElement.setAttribute("data-print-requested", "true");
          });
          await page.getByRole("button", { name: "Imprimir", exact: true }).click();
          await expect(page.locator("html")).toHaveAttribute("data-print-requested", "true");
          await page.emulateMedia({ media: "print" });
          await expect(page.locator(".production-labels")).toBeVisible();
          expect(
            await page
              .locator(".production-labels")
              .evaluate((list) => getComputedStyle(list).color),
          ).toBe("rgb(22, 28, 31)");
          await page.pdf({
            path: out + `/etiquetas-impresas-${theme}.pdf`,
            format: "Letter",
            printBackground: true,
          });
        }
        await page.context().close();
      }
  }
  if (process.argv.includes("--labels-only")) {
    for (const viewport of viewports)
      for (const theme of ["light", "dark"]) {
        const page = await pageFor("manager", theme, viewport);
        await page.goto(base + state.addresses[state.remnant.code]);
        const row = page.locator(".inventory-remnants tr[aria-current=true]");
        await expect(row).toContainText(state.remnant.code);
        await row.getByRole("button", { name: "Etiqueta", exact: true }).click();
        await expect(page.locator(".inventory-label")).toContainText(state.remnant.code);
        await capture(page, `etiqueta-retazo-${viewport.width}-${theme}`, ".inventory-label");
        await page.context().close();
      }
  }
  if (process.argv.includes("--print-only")) {
    const address = state.addresses[state.remnant.code];
    for (const theme of ["light", "dark"]) {
      const page = await pageFor("manager", theme, viewports[0]);
      await page.goto(base + address);
      const row = page.locator(".inventory-remnants tr[aria-current=true]");
      await expect(row).toContainText(state.remnant.code);
      await row.getByRole("button", { name: "Etiqueta", exact: true }).click();
      await expect(page.locator(".inventory-label")).toContainText(state.remnant.code);
      await page.evaluate(() => {
        window.print = () => document.documentElement.setAttribute("data-print-requested", "true");
      });
      await page.getByRole("button", { name: "Imprimir etiqueta", exact: true }).click();
      await expect(page.locator("html")).toHaveAttribute("data-print-requested", "true");
      await page.emulateMedia({ media: "print" });
      await expect(page.locator(".inventory-label")).toBeVisible();
      expect(
        await page
          .locator(".inventory-label-id")
          .evaluate((label) => getComputedStyle(label).color),
      ).toBe("rgb(22, 28, 31)");
      await capture(page, `retazo-impreso-${theme}`, ".inventory-label");
      await page.pdf({
        path: out + `/retazo-impreso-${theme}.pdf`,
        format: "Letter",
        printBackground: true,
      });
      await page.context().close();
    }
  }
  const report = reviewOnly
    ? "review-browser-flow"
    : process.argv.includes("--units-only")
      ? "unit-browser-flow"
      : process.argv.includes("--print-only")
        ? "print-browser-flow"
        : process.argv.includes("--labels-only")
          ? "label-browser-flow"
          : "browser-flow";
  await fs.writeFile(out + `/${report}.json`, JSON.stringify({ result: "PASS", records }, null, 2));
  console.log(
    "P02 browser flow PASS:",
    records.length,
    reviewOnly
      ? "captures; malformed scan, order requirement, blocked cut labels and recovery."
      : process.argv.includes("--units-only")
        ? "captures; unit QR, physical labels and print."
        : "captures; four codes, direct/scanned QR, permissions and states.",
  );
} catch (error) {
  if (lastPage && !lastPage.isClosed()) {
    console.log(
      "Failure surface:",
      lastPage.url(),
      (await lastPage.locator(".inventory-workspace").allInnerTexts()).map((text) =>
        text.slice(0, 1300),
      ),
    );
  }
  if (lastPage && !lastPage.isClosed())
    await lastPage.screenshot({ path: out + "/verification-failure.png" });
  await fs.writeFile(
    out + "/browser-failure.json",
    JSON.stringify({ error: String(error), records }, null, 2),
  );
  throw new Error(String(error).split("Call log:")[0].slice(0, 800));
} finally {
  await browser.close();
}

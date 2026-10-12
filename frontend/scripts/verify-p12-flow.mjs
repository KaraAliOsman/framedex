import { api, browser, context, fs, expect, base } from "./p12-fixture.mjs";
const b = await browser();
const out = "docs/redesign/captures/produccion-estaciones/recorrido";
const report = [];
async function shot(page, name) {
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
}
async function detail(id) {
  return api(`/production/orders/${id}/`, "GET", undefined, "manager");
}
try {
  await fs.mkdir(out, { recursive: true });
  const state = JSON.parse(await fs.readFile(".run/p12-fixture.json", "utf8"));
  const oc = await context(b, "operator", 1024, "dark");
  const op = await oc.newPage();
  const mc = await context(b, "manager", 1024, "dark");
  const manager = await mc.newPage();
  await api("/production/operator-station/", "PUT", { station_code: "CUT" }, "operator");
  let d = await detail(state.orderId);
  await op.goto(`${base}/production?order=${d.id}`);
  const qr = d.payload.optimization.bars.workshop_cut_plan[0].cuts[0];
  if (d.steps.find((s) => s.code === "CUT").status !== "DONE") {
    await op.locator(".production-station-task").waitFor();
    await op.getByLabel("Código de etiqueta").fill(qr.piece_qr);
    await op.getByRole("button", { name: "Abrir pieza", exact: true }).click();
    await expect(op.locator(".production-piece-code")).toHaveText(qr.piece_code);
    await shot(op, "01-qr-real");
    await expect(op.getByLabel("Tu puesto")).toHaveValue("CUT");
    if (d.steps.find((s) => s.code === "CUT").status === "READY") {
      await op.getByRole("button", { name: "Iniciar", exact: true }).click();
      await expect(op.getByRole("button", { name: "Completar", exact: true })).toBeVisible();
    }
    await op.locator(".production-touch-operations summary").click();
    for (const checkbox of await op.locator(".production-touch-operations input").all())
      await checkbox.check();
    await expect(op.getByRole("button", { name: "Completar", exact: true })).toBeEnabled();
    await op.getByRole("button", { name: "Completar", exact: true }).click();
    await expect
      .poll(async () => (await detail(d.id)).steps.find((s) => s.code === "CUT").status)
      .toBe("DONE");
  }
  d = await detail(state.orderId);
  if (d.steps.find((s) => s.code === "WELD").status !== "DONE") {
    await op.getByLabel("Tu puesto").selectOption("WELD");
    await op.getByLabel("OT de tu estación", { exact: true }).selectOption(state.orderId);
    await expect(op.locator(".production-station-task")).toContainText("Soldadura");
    if (d.steps.find((s) => s.code === "WELD").status !== "BLOCKED") {
      await op.getByRole("button", { name: "Bloquear", exact: true }).click();
      await op.getByLabel("Motivo", { exact: true }).selectOption("Equipo detenido");
      await op
        .getByLabel("Detalle del bloqueo")
        .fill("P12 DEMO · revisión del equipo de soldadura");
      await op.getByRole("button", { name: "Guardar", exact: true }).click();
      await expect.poll(async () => (await detail(d.id)).status).toBe("HOLD");
    }
    await op.reload();
    await expect(op.locator(".production-station-task")).toContainText("Equipo detenido");
    await shot(op, "02-operario-bloqueado");
    await manager.goto(base + "/production");
    const card = manager.locator(".production-board-order").filter({ hasText: d.order_code });
    await expect(card).toContainText("Equipo detenido");
    await shot(manager, "03-tablero-bloqueado");
    await manager.goto(base + "/dashboard");
    await expect(manager.locator(".today-page")).toContainText(d.order_code);
    await shot(manager, "04-hoy-bloqueo");
    await manager.goto(`${base}/production?order=${d.id}`);
    await manager.getByRole("button", { name: "Desbloquear", exact: true }).click();
    await expect.poll(async () => (await detail(d.id)).status).not.toBe("HOLD");
    await op.getByRole("button", { name: "Actualizar estación", exact: true }).first().click();
  }
  report.push({
    flow: "1024 oscuro: QR real, cola de Corte, completar, cambiar puesto, bloqueo con motivo, tablero y Hoy, supervisor desbloquea",
    result: "PASA",
  });
  d = await detail(state.orderId);
  for (const code of ["WELD", "CLEAN", "GLAZE"]) {
    if (d.steps.find((s) => s.code === code).status === "DONE") continue;
    await op.getByLabel("Tu puesto").selectOption(code);
    await op.getByLabel("OT de tu estación", { exact: true }).selectOption(state.orderId);
    await expect(op.locator(".production-station-task")).toBeVisible();
    if (d.steps.find((s) => s.code === code).status === "READY")
      await op.getByRole("button", { name: "Iniciar", exact: true }).click();
    await expect(op.getByRole("button", { name: "Completar", exact: true })).toBeEnabled();
    await op.getByRole("button", { name: "Completar", exact: true }).click();
    await expect
      .poll(async () => (await detail(state.orderId)).steps.find((s) => s.code === code).status)
      .toBe("DONE");
    d = await detail(state.orderId);
  }
  await op.getByLabel("Tu puesto").selectOption("QC");
  await op.getByLabel("OT de tu estación", { exact: true }).selectOption(state.orderId);
  await expect(op.locator(".production-station-task")).toContainText("Control de calidad");
  async function measurement(block) {
    await op.getByRole("button", { name: "Registrar medición", exact: true }).click();
    await op.getByLabel("Qué verificaste").fill("Escuadra · prueba sintética P12 DEMO");
    await op.getByLabel("Esperado según ficha").fill("Medida de la ficha sellada");
    await op.getByLabel("Medición real").fill("Fuera de especificación · prueba P12 DEMO");
    await op.getByLabel("Resultado", { exact: true }).selectOption("FAIL");
    if (block) await op.getByLabel("Bloquear la OT y avisar al jefe").check();
    await op
      .getByRole("button", { name: block ? "Guardar y bloquear" : "Guardar", exact: true })
      .click();
    await expect(op.locator(".production-station-form")).toHaveCount(0);
  }
  if (d.status !== "HOLD") {
    await measurement(false);
    await expect.poll(async () => (await detail(state.orderId)).status).not.toBe("HOLD");
    await measurement(true);
    await expect.poll(async () => (await detail(state.orderId)).status).toBe("HOLD");
  }
  await shot(op, "05-medicion-bloquea-explicitamente");
  await manager.goto(`${base}/production?order=${state.orderId}&section=calidad`);
  await manager.getByRole("tab", { name: "Calidad", exact: true }).click();
  const selectedPiece = await op.locator(".production-piece-code").innerText();
  await manager.getByLabel("Pieza que se rechaza", { exact: true }).selectOption(selectedPiece);
  const existing = (await api("/production/orders/", "GET", undefined, "manager")).orders.filter(
    (o) => o.payload?.remake_of === state.orderId,
  );
  let remake;
  if (!existing.some((r) => r.remake_reason?.qc_item === selectedPiece)) {
    await manager.getByRole("button", { name: "Rechazar y crear remake", exact: true }).click();
    await expect(manager.getByRole("dialog")).toBeVisible();
    await manager
      .getByLabel("Motivo del rechazo", { exact: true })
      .fill("P12 DEMO · escuadra rechazada en control final");
    await shot(manager, "06-confirmacion-remake");
    const req = manager.waitForRequest(
      (r) => r.url().endsWith("/qc-remake/") && r.method() === "POST",
    );
    const res = manager.waitForResponse(
      (r) => r.url().endsWith("/qc-remake/") && r.request().method() === "POST",
    );
    await manager.getByRole("button", { name: "Confirmar rechazo y remake", exact: true }).click();
    const body = (await req).postDataJSON();
    expect(body.item_code).toBe(selectedPiece);
    remake = await (await res).json();
    expect(remake.id).toBeTruthy();
    const retry = await api(
      `/production/orders/${state.orderId}/qc-remake/`,
      "POST",
      body,
      "manager",
    );
    expect(retry.id).toBe(remake.id);
    expect(retry.payload.remake_reason.qc_item).toBe(selectedPiece);
    expect(
      (await api("/production/orders/", "GET", undefined, "manager")).orders.filter(
        (o) => o.payload?.remake_of === state.orderId,
      ),
    ).toHaveLength(existing.length + 1);
  } else {
    remake = await detail(existing.find((r) => r.remake_reason?.qc_item === selectedPiece).id);
  }
  await manager.goto(`${base}/production?order=${remake.id}`);
  await manager.getByRole("tablist").waitFor();
  await shot(manager, "07-remake-con-pieza");
  report.push({
    flow: "Ruta real hasta QC; medición falla sin bloqueo, bloqueo explícito, remake confirmado y retry idempotente conserva pieza",
    result: "PASA",
    order: d.order_code,
    remake: remake.order_code,
    piece: selectedPiece,
  });
  await fs.writeFile(".run/p12-flow-state.json", JSON.stringify({ remakeId: remake.id }));
} finally {
  await fs.writeFile(`${out}/informe.json`, JSON.stringify(report, null, 2));
  await b.close();
}
console.log("P12 flujo real PASA");

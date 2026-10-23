import { describe, expect, it } from "vitest";
import type { TodayAction } from "../api/generated/models";
import { todayDate, todayGreeting, todayMetrics } from "./todaySummary";

const action = (kind: string, entity_code = "OT-1", consequence = "today", blocking = false) =>
  ({ kind, entity_code, consequence, blocking }) as TodayAction;

describe("Hoy summary", () => {
  it("uses Santiago time and a safe optional first name", () => {
    expect(todayGreeting("  Juan  Pérez ", new Date("2026-10-22T13:00:00Z"))).toBe(
      "Buenos días, Juan",
    );
    expect(todayGreeting("Ali", new Date("2026-10-22T18:00:00Z"))).toBe("Buenas tardes, Ali");
    expect(todayGreeting(undefined, new Date("2026-10-23T01:00:00Z"))).toBe("Buenas noches");
    expect(todayGreeting("x".repeat(100), new Date("2026-10-22T13:00:00Z"))).toBe("Buenos días");
    expect(todayDate("2026-10-22")).toBe("jueves, 22 de octubre");
  });
  it("counts unique entities and never implies a weekly acceptance metric", () => {
    const actions = [
      action("quote_send", "P-1"),
      action("quote_send", "P-1"),
      action("quote_send", "P-2"),
      action("quote_approved", "P-3"),
      action("delivery", "OT-2", "overdue"),
    ];
    expect(todayMetrics(actions, "OWNER")).toEqual([
      { label: "Por enviar", count: 2, tier: "" },
      { label: "Aceptadas por coordinar", count: 1, tier: "" },
      { label: "Atrasos en taller", count: 1, tier: "overdue" },
    ]);
    expect(todayMetrics(actions, "ESTIMATOR")).toHaveLength(2);
    expect(todayMetrics([], "OWNER")).toEqual([]);
  });
  it("shows only the field or workshop metrics useful for the role", () => {
    const actions = [
      action("work_order_blocked", "OT-1", "blocking", true),
      action("station_work", "OT-1"),
      action("delivery", "OT-2", "overdue"),
      action("field_incident", "IN-1"),
    ];
    expect(todayMetrics(actions, "OPERATOR")).toEqual([
      { label: "Órdenes por atender", count: 2, tier: "" },
      { label: "Bloqueos", count: 1, tier: "blocking" },
      { label: "Compromisos vencidos", count: 1, tier: "overdue" },
    ]);
    expect(todayMetrics(actions, "WORKSHOP_MANAGER")).toHaveLength(3);
    expect(todayMetrics(actions, "INSTALLER").map((item) => item.label)).toEqual([
      "Entregas e instalaciones",
      "Incidencias abiertas",
    ]);
  });
});

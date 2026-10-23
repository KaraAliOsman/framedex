import type { MembershipRoleEnum, TodayAction } from "../api/generated/models";

/** The API already supplies the tenant's calendar day; do not shift it again. */
export function todayDate(day: string): string {
  return new Intl.DateTimeFormat("es-CL", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(`${day}T12:00:00Z`));
}

export function todayGreeting(name: unknown, now = new Date()): string {
  const hour = Number(
    new Intl.DateTimeFormat("es-CL", {
      hour: "numeric",
      hourCycle: "h23",
      timeZone: "America/Santiago",
    }).format(now),
  );
  const greeting = hour < 12 ? "Buenos días" : hour < 20 ? "Buenas tardes" : "Buenas noches";
  const first = typeof name === "string" ? name.trim().split(/\s+/)[0] : "";
  return first && first.length <= 80 ? `${greeting}, ${first}` : greeting;
}

export function todayMetrics(actions: TodayAction[], role: MembershipRoleEnum) {
  const count = (matches: (item: TodayAction) => boolean) =>
    new Set(actions.filter(matches).map((item) => item.entity_code)).size;
  const workshop = (item: TodayAction) =>
    /^(work_order_|station_|dispatch_|remake|delivery|installation)/.test(item.kind);
  const metrics =
    role === "OWNER" || role === "ESTIMATOR"
      ? [
          { label: "Por enviar", count: count((item) => item.kind === "quote_send"), tier: "" },
          {
            label: "Aceptadas por coordinar",
            count: count((item) => item.kind === "quote_approved"),
            tier: "",
          },
          role === "OWNER"
            ? {
                label: "Atrasos en taller",
                count: count((item) => workshop(item) && item.consequence === "overdue"),
                tier: "overdue",
              }
            : {
                label: "Clientes por responder",
                count: count((item) => item.kind === "quote_response"),
                tier: "blocking",
              },
        ]
      : role === "INSTALLER"
        ? [
            {
              label: "Entregas e instalaciones",
              count: count((item) => ["delivery", "installation"].includes(item.kind)),
              tier: "",
            },
            {
              label: "Visitas por hacer",
              count: count((item) => item.kind === "field_visit"),
              tier: "",
            },
            {
              label: "Incidencias abiertas",
              count: count((item) => item.kind === "field_incident"),
              tier: "blocking",
            },
          ]
        : [
            { label: "Órdenes por atender", count: count(workshop), tier: "" },
            {
              label: "Bloqueos",
              count: count((item) => workshop(item) && item.blocking),
              tier: "blocking",
            },
            {
              label: "Compromisos vencidos",
              count: count((item) => item.consequence === "overdue"),
              tier: "overdue",
            },
          ];
  return metrics.filter((metric) => metric.count > 0);
}

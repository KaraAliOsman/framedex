import type { OperationalSummary, ProjectResponse } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";

export type AttentionEntry = {
  key: TranslationKey;
  count: number;
  to: string;
  warn: boolean;
};

/** One definition of "what needs a human right now" — the dashboard queue
 * and the shell bell render the same feed so the surfaces can never drift. */
export function attentionEntries(
  ops: OperationalSummary | undefined,
  projects: ProjectResponse[],
): AttentionEntry[] {
  const workOrders = (ops?.work_orders ?? {}) as Record<string, number>;
  const deliveries = (ops?.deliveries ?? {}) as Record<string, number>;
  const prep = (ops?.prep ?? {}) as Record<string, number>;
  const candidates: AttentionEntry[] = [
    {
      key: "dashboard.prepVersions",
      count: Number(prep.versions_ready ?? 0),
      to: "/production",
      warn: false,
    },
    {
      key: "dashboard.prepShortage",
      count: Number(prep.work_orders_shortage ?? 0),
      to: "/production?shortage=1",
      warn: true,
    },
    {
      key: "dashboard.prepDispatch",
      count: Number(prep.dispatch_ready ?? 0),
      to: "/production?dispatch_ready=1",
      warn: false,
    },
    {
      key: "dashboard.catalogGaps",
      count: Number(prep.catalog_gaps ?? 0),
      to: "/catalogs/systems",
      warn: true,
    },
    {
      key: "dashboard.deliveriesOverdue",
      count: Number(deliveries.overdue ?? 0),
      to: "/production?status=DISPATCHED",
      warn: true,
    },
    {
      key: "dashboard.deliveriesToday",
      count: Number(deliveries.today ?? 0),
      to: "/production?status=DISPATCHED",
      warn: false,
    },
    {
      key: "dashboard.ordersHold",
      count: Number(workOrders.HOLD ?? 0),
      to: "/production?status=HOLD",
      warn: true,
    },
    {
      key: "dashboard.quotesWaiting",
      count: projects.filter((item) => item.status === "QUOTED").length,
      to: "/projects?status=QUOTED",
      warn: false,
    },
  ];
  return candidates.filter((entry) => entry.count > 0);
}

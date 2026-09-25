import type { OperationalSummary, ProjectResponse } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";

export type AttentionEntry = {
  /** Label of the queue row ("4 cotizaciones esperan envío"). */
  key: TranslationKey;
  /** Verb for the row's CTA — the action that resolves the attention. */
  action: TranslationKey;
  count: number;
  to: string;
  warn: boolean;
};

/** One definition of "what needs a human right now" — the dashboard queue
 * and the shell bell render the same feed so the surfaces can never drift.
 * Order is the working order of the day: commercial attention first (a client
 * waiting beats an internal queue), then blockers, then routine work. */
export function attentionEntries(
  ops: OperationalSummary | undefined,
  projects: ProjectResponse[],
): AttentionEntry[] {
  const workOrders = (ops?.work_orders ?? {}) as Record<string, number>;
  const deliveries = (ops?.deliveries ?? {}) as Record<string, number>;
  const prep = (ops?.prep ?? {}) as Record<string, number>;
  const projectsByStatus = projects.reduce<Record<string, number>>((counts, project) => {
    const status = project.status ?? "";
    counts[status] = (counts[status] ?? 0) + 1;
    return counts;
  }, {});
  const candidates: AttentionEntry[] = [
    {
      key: "dashboard.approvalsPending",
      action: "attention.action.viewApproval",
      count: Number(prep.approvals_pending ?? 0),
      to: "/projects?status=QUOTED",
      warn: false,
    },
    {
      // QUOTED projects whose current revision still has no live approval
      // link — already-sent links belong to approvalsPending, not here.
      key: "dashboard.quotesWaiting",
      action: "attention.action.sendQuote",
      count: Number(prep.quotes_unsent ?? 0),
      to: "/projects?status=QUOTED",
      warn: false,
    },
    {
      key: "dashboard.stepsBlocked",
      action: "attention.action.unblock",
      count: Number(prep.steps_blocked ?? 0),
      to: "/production?blocked=1",
      warn: true,
    },
    {
      key: "dashboard.jobsFailed",
      action: "attention.action.retryJobs",
      count: Number(prep.jobs_failed ?? 0),
      to: "/jobs",
      warn: true,
    },
    {
      key: "dashboard.prepShortage",
      action: "attention.action.buyMaterial",
      count: Number(prep.work_orders_shortage ?? 0),
      to: "/production?shortage=1",
      warn: true,
    },
    {
      key: "dashboard.ordersHold",
      action: "attention.action.review",
      count: Number(workOrders.HOLD ?? 0),
      to: "/production?status=HOLD",
      warn: true,
    },
    {
      key: "dashboard.deliveriesOverdue",
      action: "attention.action.reschedule",
      count: Number(deliveries.overdue ?? 0),
      to: "/production?status=DISPATCHED",
      warn: true,
    },
    {
      key: "dashboard.catalogGaps",
      action: "attention.action.completeCatalog",
      count: Number(prep.catalog_gaps ?? 0),
      to: "/catalogs/systems",
      warn: true,
    },
    {
      key: "dashboard.prepVersions",
      action: "attention.action.prepare",
      count: Number(prep.versions_ready ?? 0),
      to: "/production",
      warn: false,
    },
    {
      key: "dashboard.prepDispatch",
      action: "attention.action.dispatch",
      count: Number(prep.dispatch_ready ?? 0),
      to: "/production?dispatch_ready=1",
      warn: false,
    },
    {
      key: "dashboard.deliveriesToday",
      action: "attention.action.coordinate",
      count: Number(deliveries.today ?? 0),
      to: "/production?status=DISPATCHED",
      warn: false,
    },
    {
      key: "dashboard.draftsToQuote",
      action: "attention.action.quoteNow",
      count: projectsByStatus.DRAFT ?? 0,
      to: "/projects?status=DRAFT",
      warn: false,
    },
  ];
  return candidates.filter((entry) => entry.count > 0);
}

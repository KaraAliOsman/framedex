import { useQuery } from "@tanstack/react-query";

import { organizationPlan } from "../api/generated/dekopen";
import type { OrganizationPlan, PlanFeatureEnum } from "../api/generated/models";
import { ApiError } from "../api/apiMutator";
import { t } from "../i18n/es-CL";

export function organizationPlanKey(orgId: string | undefined): readonly unknown[] {
  return ["organization-plan", orgId ?? null];
}

/** What the workshop's plan includes: people, roles and features. The server
 * enforces seats and roles; the interface only adapts to them. */
export function useOrganizationPlan(orgId: string | undefined) {
  return useQuery({
    queryKey: organizationPlanKey(orgId),
    enabled: Boolean(orgId),
    staleTime: 60_000,
    queryFn: async ({ signal }): Promise<OrganizationPlan> => {
      const response = await organizationPlan({
        signal,
        headers: { "X-Organization-ID": orgId! },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
}

export function planIncludes(
  plan: OrganizationPlan | undefined,
  feature: PlanFeatureEnum,
): boolean {
  // Until the plan loads, nothing is hidden: the server still decides.
  return !plan || plan.features.includes(feature);
}

const PLAN_KEYS = {
  TRIAL: "billing.TRIAL",
  STARTER: "billing.STARTER",
  PRO: "billing.PRO",
  BUSINESS: "billing.BUSINESS",
  BUSINESS_2X: "billing.BUSINESS_2X",
} as const;

export function planName(code: string): string {
  const key = PLAN_KEYS[code as keyof typeof PLAN_KEYS];
  return key ? t(key) : code;
}

/** «1 de 3 personas · 1 invitación pendiente» or «Personas ilimitadas». */
export function seatsText(plan: OrganizationPlan): string {
  const pending = plan.pending_invitations
    ? ` · ${plan.pending_invitations} ${plan.pending_invitations === 1 ? "invitación pendiente" : "invitaciones pendientes"}`
    : "";
  if (plan.seats === null) {
    return `${plan.active_members} ${plan.active_members === 1 ? "persona" : "personas"} · sin límite${pending}`;
  }
  return `${plan.active_members} de ${plan.seats} ${plan.seats === 1 ? "persona" : "personas"}${pending}`;
}

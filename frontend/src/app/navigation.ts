import type { MembershipRoleEnum } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";

const commercial = ["OWNER", "ESTIMATOR"] as const;
const office = [...commercial, "WORKSHOP_MANAGER"] as const;
const inventory = [...office, "OPERATOR"] as const;
const everyone = [...inventory, "INSTALLER"] as const;

type NavEntry = { to: string; label: TranslationKey; roles: readonly MembershipRoleEnum[] };
export type NavGroup = {
  id: string;
  title?: TranslationKey;
  secondary?: boolean;
  items: NavEntry[];
};

/** Relevance and permissions are separate. Secondary tools stay searchable;
 * every request is still authorized by the server. */
const flow: NavGroup[] = [
  { id: "home", items: [{ to: "/dashboard", label: "nav.dashboard", roles: everyone }] },
  {
    id: "sales",
    title: "nav.groupSales",
    items: [
      { to: "/projects", label: "nav.projects", roles: office },
      { to: "/clients", label: "nav.clients", roles: commercial },
    ],
  },
  {
    id: "engineering",
    secondary: true,
    title: "nav.groupEngineering",
    items: [{ to: "/catalogs/systems", label: "nav.technicalCatalog", roles: office }],
  },
  {
    id: "operations",
    title: "nav.groupOps",
    items: [
      { to: "/purchasing", label: "nav.purchasing", roles: ["OWNER", "WORKSHOP_MANAGER"] },
      { to: "/production", label: "nav.production", roles: everyone },
      { to: "/field", label: "nav.field", roles: ["WORKSHOP_MANAGER", "INSTALLER"] },
    ],
  },
  {
    id: "assistant",
    items: [{ to: "/assistant", label: "nav.assistant", roles: office }],
  },
  {
    id: "analytics",
    secondary: true,
    items: [{ to: "/analytics", label: "nav.analytics", roles: ["OWNER", "WORKSHOP_MANAGER"] }],
  },
  {
    id: "tools",
    secondary: true,
    items: [
      { to: "/quotes", label: "nav.quotes", roles: commercial },
      { to: "/pricing/commercial", label: "nav.prices", roles: commercial },
      { to: "/inventory", label: "nav.inventory", roles: inventory },
      { to: "/dispatch", label: "nav.dispatch", roles: office },
      { to: "/field", label: "nav.field", roles: commercial },
      { to: "/purchasing", label: "nav.purchasing", roles: ["ESTIMATOR"] },
      { to: "/clients", label: "nav.clients", roles: ["WORKSHOP_MANAGER"] },
      { to: "/jobs", label: "nav.jobs", roles: office },
      { to: "/settings/general", label: "nav.settings", roles: office },
    ],
  },
];

export function navigationFor(role: MembershipRoleEnum | undefined): NavGroup[] {
  if (!role) return [];
  return flow
    .map((group) => ({ ...group, items: group.items.filter((item) => item.roles.includes(role)) }))
    .filter((group) => group.items.length > 0);
}

export function homeFor(role: MembershipRoleEnum | undefined): string {
  return role === "OPERATOR" ? "/production" : "/dashboard";
}

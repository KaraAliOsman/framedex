import type { MembershipRoleEnum } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";

const commercial = ["OWNER", "ESTIMATOR"] as const;
const office = [...commercial, "WORKSHOP_MANAGER"] as const;
const inventory = [...office, "OPERATOR"] as const;
const everyone = [...inventory, "INSTALLER"] as const;

type NavEntry = { to: string; label: TranslationKey; roles: readonly MembershipRoleEnum[] };
export type NavGroup = { id: string; title?: TranslationKey; items: NavEntry[] };

/** Mirrors the domain API's read capabilities, including read-only access.
 * The server still authorizes every request; this list grants nothing. */
const flow: NavGroup[] = [
  { id: "home", items: [{ to: "/dashboard", label: "nav.dashboard", roles: everyone }] },
  {
    id: "sales",
    title: "nav.groupSales",
    items: [
      { to: "/clients", label: "nav.clients", roles: office },
      { to: "/projects", label: "nav.projects", roles: office },
      { to: "/quotes", label: "nav.quotes", roles: commercial },
      { to: "/pricing/commercial", label: "nav.prices", roles: commercial },
    ],
  },
  {
    id: "engineering",
    title: "nav.groupEngineering",
    items: [{ to: "/catalogs/systems", label: "nav.technicalCatalog", roles: office }],
  },
  {
    id: "operations",
    title: "nav.groupOps",
    items: [
      { to: "/purchasing", label: "nav.purchasing", roles: office },
      { to: "/inventory", label: "nav.inventory", roles: inventory },
      { to: "/production", label: "nav.production", roles: everyone },
    ],
  },
  {
    id: "assistant",
    title: "nav.groupAssistant",
    items: [
      { to: "/assistant", label: "nav.assistant", roles: office },
      { to: "/jobs", label: "nav.jobs", roles: office },
    ],
  },
  { id: "settings", items: [{ to: "/settings/general", label: "nav.settings", roles: office }] },
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

import type { MembershipRoleEnum } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";
import type { IconName } from "../ui/Icon";

const commercial = ["OWNER", "ESTIMATOR"] as const;
const office = [...commercial, "WORKSHOP_MANAGER"] as const;
const inventory = [...office, "OPERATOR"] as const;
const everyone = [...inventory, "INSTALLER"] as const;

export type NavSection = {
  to: string;
  label: TranslationKey;
  roles: readonly MembershipRoleEnum[];
};
export type NavArea = {
  id: "projects" | "clients" | "catalogs" | "workshop" | "company";
  label: TranslationKey;
  icon: IconName;
  /** Paths that belong to the area even when they are not a listed section. */
  owns: readonly string[];
  sections: NavSection[];
};

/** Four everyday areas and Empresa (constitution §5.1). The list mirrors the
 * domain API's read capabilities; the server still authorizes every request
 * and this list grants nothing. Sections render as the area's own tabs. */
const AREAS: NavArea[] = [
  {
    id: "projects",
    label: "nav.projects",
    icon: "projects",
    owns: ["/projects", "/quotes", "/dashboard", "/onboarding", "/pricing/commercial"],
    sections: [
      { to: "/projects", label: "nav.projects", roles: office },
      { to: "/quotes", label: "nav.quotes", roles: commercial },
    ],
  },
  {
    id: "clients",
    label: "nav.clients",
    icon: "clients",
    owns: ["/clients"],
    sections: [{ to: "/clients", label: "nav.clients", roles: office }],
  },
  {
    id: "catalogs",
    label: "nav.catalogs",
    icon: "catalogs",
    owns: ["/catalogs"],
    sections: [
      { to: "/catalogs/systems", label: "nav.catalogs", roles: office },
      { to: "/catalogs/finish-samples", label: "nav.finishSamples", roles: office },
      { to: "/catalogs/sheet-formats", label: "nav.sheetFormats", roles: office },
    ],
  },
  {
    id: "workshop",
    label: "nav.workshop",
    icon: "workshop",
    owns: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    sections: [
      { to: "/production", label: "nav.orders", roles: everyone },
      { to: "/purchasing", label: "nav.purchasing", roles: office },
      { to: "/inventory", label: "nav.inventory", roles: inventory },
      { to: "/dispatch", label: "nav.dispatch", roles: office },
      { to: "/field", label: "nav.field", roles: [...office, "INSTALLER"] },
    ],
  },
  {
    id: "company",
    label: "nav.company",
    icon: "company",
    owns: ["/settings", "/analytics", "/pricing/cost-lists", "/jobs", "/assistant"],
    sections: [
      { to: "/settings/general", label: "nav.preferences", roles: office },
      // Cost lists are owner-only; the estimator lands on the commercial
      // rules it can actually use instead of a denied page.
      { to: "/pricing/cost-lists", label: "nav.costs", roles: ["OWNER"] },
      { to: "/pricing/commercial", label: "nav.costs", roles: ["ESTIMATOR"] },
      { to: "/analytics", label: "nav.analytics", roles: ["OWNER", "WORKSHOP_MANAGER"] },
      { to: "/settings/billing", label: "nav.plan", roles: office },
    ],
  },
];

export type VisibleArea = NavArea & { to: string };

/** Areas a role can open, each pointing at its first readable section. */
export function navigationFor(role: MembershipRoleEnum | undefined): VisibleArea[] {
  if (!role) return [];
  return AREAS.flatMap((area) => {
    const sections = area.sections.filter((section) => section.roles.includes(role));
    const first = sections[0];
    return first ? [{ ...area, sections, to: first.to }] : [];
  });
}

/** The area that owns a pathname, for the active rail item and its tabs. */
export function areaFor(
  pathname: string,
  role: MembershipRoleEnum | undefined,
): VisibleArea | null {
  return (
    navigationFor(role).find((area) =>
      area.owns.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)),
    ) ?? null
  );
}

/** Each role starts with its own work (owner/estimator: projects; workshop:
 * orders; operator: station; installer: agenda). */
export function homeFor(role: MembershipRoleEnum | undefined): string {
  if (role === "OPERATOR" || role === "WORKSHOP_MANAGER") return "/production";
  if (role === "INSTALLER") return "/field";
  return "/projects";
}

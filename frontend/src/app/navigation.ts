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
  id: "today" | "projects" | "catalogs" | "workshop" | "company";
  label: TranslationKey;
  icon: IconName;
  /** Paths that belong to the area even when they are not a listed section. */
  owns: readonly string[];
  sections: NavSection[];
};

/** Five destinations, filtered by role (constitution §5.1). The list mirrors the
 * domain API's read capabilities; the server still authorizes every request
 * and this list grants nothing. Sections render as the area's own tabs. */
const AREAS: NavArea[] = [
  {
    id: "today",
    label: "nav.today",
    icon: "today",
    owns: ["/dashboard"],
    sections: [{ to: "/dashboard", label: "nav.today", roles: everyone }],
  },
  {
    id: "projects",
    label: "nav.projects",
    icon: "projects",
    owns: ["/projects", "/quotes", "/clients", "/onboarding"],
    sections: [{ to: "/projects", label: "nav.projects", roles: office }],
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
    owns: ["/settings", "/analytics", "/pricing", "/jobs", "/assistant"],
    sections: [
      { to: "/settings/general", label: "nav.preferences", roles: office },
      { to: "/analytics", label: "nav.analytics", roles: ["OWNER", "WORKSHOP_MANAGER"] },
      { to: "/settings/advanced", label: "nav.advanced", roles: office },
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
  }).sort(
    (a, b) =>
      ["today", "projects", "workshop", "catalogs", "company"].indexOf(a.id) -
      ["today", "projects", "workshop", "catalogs", "company"].indexOf(b.id),
  );
}

/** Clients remain searchable without becoming a sixth rail destination. */
export function paletteNavigationFor(role: MembershipRoleEnum | undefined): NavSection[] {
  const sections = navigationFor(role).flatMap((area) => area.sections);
  return role && office.some((allowed) => allowed === role)
    ? [...sections, { to: "/clients", label: "nav.clients", roles: office }]
    : sections;
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

/** All roles start with their actionable day, with workshop/agenda one click away. */
export function homeFor(role: MembershipRoleEnum | undefined): string {
  return role ? "/dashboard" : "/projects";
}

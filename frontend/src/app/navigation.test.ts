import { expect, it } from "vitest";
import { areaFor, homeFor, navigationFor } from "./navigation";
import type { MembershipRoleEnum } from "../api/generated/models";

const expected: Record<MembershipRoleEnum, Record<string, string[]>> = {
  OWNER: {
    projects: ["/projects", "/quotes"],
    clients: ["/clients"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/pricing/cost-lists", "/analytics", "/settings/billing"],
  },
  ESTIMATOR: {
    projects: ["/projects", "/quotes"],
    clients: ["/clients"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/pricing/commercial", "/settings/billing"],
  },
  WORKSHOP_MANAGER: {
    projects: ["/projects"],
    clients: ["/clients"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/analytics", "/settings/billing"],
  },
  OPERATOR: { workshop: ["/production", "/inventory"] },
  INSTALLER: { workshop: ["/production", "/field"] },
};
const home: Record<MembershipRoleEnum, string> = {
  OWNER: "/projects",
  ESTIMATOR: "/projects",
  WORKSHOP_MANAGER: "/production",
  OPERATOR: "/production",
  INSTALLER: "/field",
};

it.each(Object.keys(expected) as MembershipRoleEnum[])(
  "shows four everyday areas plus Empresa within the read capabilities of %s",
  (role) => {
    const areas = navigationFor(role);
    expect(
      Object.fromEntries(areas.map((area) => [area.id, area.sections.map((item) => item.to)])),
    ).toEqual(expected[role]);
    expect(areas.every((area) => area.to === area.sections[0]!.to)).toBe(true);
    expect(homeFor(role)).toBe(home[role]);
  },
);

it("keeps replaced destinations inside their area", () => {
  expect(areaFor("/pricing/commercial", "OWNER")?.id).toBe("projects");
  expect(areaFor("/projects/abc/positions/1/edit", "ESTIMATOR")?.id).toBe("projects");
  expect(areaFor("/jobs", "OWNER")?.id).toBe("company");
  expect(areaFor("/inventory", "OPERATOR")?.id).toBe("workshop");
});

it("offers no domain entry before a tenant role resolves", () => {
  expect(navigationFor(undefined)).toEqual([]);
});

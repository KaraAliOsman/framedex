import { expect, it } from "vitest";
import { areaFor, homeFor, navigationFor, paletteNavigationFor } from "./navigation";
import type { MembershipRoleEnum } from "../api/generated/models";

const expected: Record<MembershipRoleEnum, Record<string, string[]>> = {
  OWNER: {
    today: ["/dashboard"],
    projects: ["/projects"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/analytics", "/settings/advanced", "/settings/billing"],
  },
  ESTIMATOR: {
    today: ["/dashboard"],
    projects: ["/projects"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/settings/advanced", "/settings/billing"],
  },
  WORKSHOP_MANAGER: {
    today: ["/dashboard"],
    projects: ["/projects"],
    catalogs: ["/catalogs/systems", "/catalogs/finish-samples", "/catalogs/sheet-formats"],
    workshop: ["/production", "/purchasing", "/inventory", "/dispatch", "/field"],
    company: ["/settings/general", "/analytics", "/settings/advanced", "/settings/billing"],
  },
  OPERATOR: { today: ["/dashboard"], workshop: ["/production", "/inventory"] },
  INSTALLER: { today: ["/dashboard"], workshop: ["/production", "/field"] },
};

it.each(Object.keys(expected) as MembershipRoleEnum[])(
  "shows the new destinations within the read capabilities of %s",
  (role) => {
    const areas = navigationFor(role);
    expect(
      Object.fromEntries(areas.map((area) => [area.id, area.sections.map((item) => item.to)])),
    ).toEqual(expected[role]);
    expect(areas.every((area) => area.to === area.sections[0]!.to)).toBe(true);
    expect(homeFor(role)).toBe("/dashboard");
  },
);

it("keeps replaced destinations inside their area", () => {
  expect(areaFor("/pricing/commercial", "OWNER")?.id).toBe("company");
  expect(areaFor("/projects/abc/positions/1/edit", "ESTIMATOR")?.id).toBe("projects");
  expect(areaFor("/jobs", "OWNER")?.id).toBe("company");
  expect(areaFor("/inventory", "OPERATOR")?.id).toBe("workshop");
});

it("offers no domain entry before a tenant role resolves", () => {
  expect(navigationFor(undefined)).toEqual([]);
});

it("keeps clients in search for office roles and preserves a stable destination order", () => {
  expect(navigationFor("OWNER").map((area) => area.id)).toEqual([
    "today",
    "projects",
    "workshop",
    "catalogs",
    "company",
  ]);
  expect(paletteNavigationFor("ESTIMATOR").some((entry) => entry.to === "/clients")).toBe(true);
  expect(paletteNavigationFor("INSTALLER").some((entry) => entry.to === "/clients")).toBe(false);
  expect(areaFor("/clients/123", "OWNER")?.id).toBe("projects");
});

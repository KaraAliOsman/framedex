import { expect, it } from "vitest";
import { homeFor, navigationFor } from "./navigation";
import type { MembershipRoleEnum } from "../api/generated/models";

const expected: Record<MembershipRoleEnum, string[]> = {
  OWNER: [
    "/dashboard",
    "/clients",
    "/projects",
    "/quotes",
    "/pricing/commercial",
    "/catalogs/systems",
    "/purchasing",
    "/inventory",
    "/production",
    "/assistant",
    "/jobs",
    "/settings/general",
  ],
  ESTIMATOR: [
    "/dashboard",
    "/clients",
    "/projects",
    "/quotes",
    "/pricing/commercial",
    "/catalogs/systems",
    "/purchasing",
    "/inventory",
    "/production",
    "/assistant",
    "/jobs",
    "/settings/general",
  ],
  WORKSHOP_MANAGER: [
    "/dashboard",
    "/clients",
    "/projects",
    "/catalogs/systems",
    "/purchasing",
    "/inventory",
    "/production",
    "/assistant",
    "/jobs",
    "/settings/general",
  ],
  OPERATOR: ["/dashboard", "/inventory", "/production"],
  INSTALLER: ["/dashboard", "/production"],
};
it.each(Object.keys(expected) as MembershipRoleEnum[])(
  "reflects the read capabilities and workflow for %s",
  (role) => {
    const groups = navigationFor(role);
    expect(groups.flatMap((group) => group.items.map((item) => item.to))).toEqual(expected[role]);
    expect(groups.every((group) => group.items.length > 0)).toBe(true);
    expect(homeFor(role)).toBe(role === "OPERATOR" ? "/production" : "/dashboard");
  },
);
it("offers no domain entry before a tenant role resolves", () => {
  expect(navigationFor(undefined)).toEqual([]);
});

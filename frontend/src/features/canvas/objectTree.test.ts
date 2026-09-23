import { expect, it } from "vitest";

import type { ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { resolveMembers } from "./members";
import { buildObjectTree } from "./objectTree";
import { makeBayTree, makeBowProduct } from "./productEditing";

const members = resolveMembers(undefined);

it("lists modules interleaved with couplings, human names only", () => {
  const product = makeBowProduct({ moduleCount: 3, widthMm: 3000, heightMm: 1400, angleDeg: 25 });
  const tree = buildObjectTree(product, members, [], t);
  const labels = tree.children.map((node) => node.label);
  expect(labels[0]).toBe("Módulo 1");
  expect(labels[1]).toBe("Acoplador");
  expect(labels[2]).toBe("Módulo 2");
  expect(labels[4]).toBe("Módulo 3");
  expect(tree.detail).toContain("3000");
  expect(labels.join("|")).not.toMatch(/\bm\d\b|\bc\d\b/);
});

it("nests the member hierarchy under each module", () => {
  const product = makeBowProduct({
    moduleCount: 1,
    widthMm: 1200,
    heightMm: 1400,
    angleDeg: 0,
    opening: "TILT_TURN_RIGHT",
  });
  const tree = buildObjectTree(product, members, [], t);
  const moduleRow = tree.children[0]!;
  const kinds = moduleRow.children.map((node) => node.kind);
  expect(kinds).toEqual(["member", "bay"]);
  const bay = moduleRow.children[1]!;
  const leafKinds = bay.children.map((node) => node.kind);
  expect(leafKinds).toContain("member"); // sash
  expect(leafKinds).toContain("handle");
  expect(leafKinds).toContain("glazing");
});

it("maps issue severities onto module and coupling rows", () => {
  const product = makeBowProduct({ moduleCount: 2, widthMm: 2000, heightMm: 1200, angleDeg: 30 });
  const issues: ProductIssue[] = [
    { code: "x", severity: "error", target: "module:m1", params: {} },
    { code: "y", severity: "warning", target: "coupling:c1", params: {} },
  ];
  const tree = buildObjectTree(product, members, issues, t);
  expect(tree.children[0]!.severity).toBe("error");
  expect(tree.children[1]!.severity).toBe("warning");
  expect(tree.children[2]!.severity).toBeNull();
});

it("marks mullions for split intents", () => {
  const product = makeBowProduct({ moduleCount: 1, widthMm: 1600, heightMm: 1200, angleDeg: 0 });
  const module = product.assembly.modules[0]!;
  module.tree = {
    id: "m1",
    type: "SPLIT_V",
    width_mm: "1600.00",
    height_mm: "1200.00",
    split_offset_mm: "800.00",
    children: [makeBayTree("m1a", "FIXED", "4.00", "4"), makeBayTree("m1b", "TURN_LEFT", "4.00", "4")],
  };
  const tree = buildObjectTree(product, members, [], t);
  const mullionRow = tree.children[0]!.children.find((node) => node.kind === "mullion");
  expect(mullionRow?.label).toBe("Mullión vertical");
});

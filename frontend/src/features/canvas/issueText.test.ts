import { describe, expect, it } from "vitest";

import type { ProductIssue } from "../../api/generated/models";
import { issueText } from "./AssemblyEditor";
import { makeBowProduct } from "./productEditing";

const product = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 15 });
const modules = product.assembly.modules;
const couplings = product.assembly.couplings;

function geometryFailure(target: string, reason: string): ProductIssue {
  return {
    code: "module_geometry_failed",
    severity: "WARNING",
    target,
    params: { reason },
  } as ProductIssue;
}

describe("issueText — human-readable, internals never leak", () => {
  it("names the module by its ordinal, not its raw id", () => {
    const issue = geometryFailure(
      `module:${modules[1].id}`,
      `BAY 6c60197a-1234 requires glass_thickness_mm and glass_spec`,
    );
    const text = issueText(issue, modules, couplings);
    expect(text).toContain("Módulo 2");
    expect(text).not.toContain(modules[1].id);
    expect(text).not.toContain("6c60197a");
    expect(text).not.toContain("glass_thickness_mm");
    expect(text).toContain("espesor y vidrio");
  });

  it("maps unknown engine errors to the generic phrase", () => {
    const issue = geometryFailure(`module:${modules[0].id}`, "WEIRD 123 internal marker");
    const text = issueText(issue, modules, couplings);
    expect(text).toContain("revisa los parámetros");
    expect(text).not.toContain("WEIRD");
  });

  it("names couplings by ordinal", () => {
    const issue: ProductIssue = {
      code: "coupler_profile_missing",
      severity: "ERROR",
      target: `coupling:${couplings[1].id}`,
      params: {},
    } as ProductIssue;
    const text = issueText(issue, modules, couplings);
    expect(text).toContain("Unión 2");
    expect(text).not.toContain(couplings[1].id);
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  AssemblyMeasure,
  CouplerChoice,
  PlanGeometry,
  ProductIssue,
} from "../../api/generated/models";
import { BowPlanSvg, ANGLE_SNAPS, snapPlanAngle, planDisplay } from "./BowPlanSvg";
import { AssemblyPlanPane } from "./AssemblyPlanPane";
import { compatibleCouplers } from "./couplerAuthority";
import { assemblyIssueDestination } from "./assemblyIssueNavigation";
import { frontLayout } from "./ProductFrontSvg";
import { makeBowProduct } from "./productEditing";
import { resolveMembers } from "./members";
import cases from "../../../../engine/tests/golden_assemblies.json";

const product = makeBowProduct({ moduleCount: 3, widthMm: 2400, heightMm: 1200, angleDeg: 22.5 });
const plan = cases.bow_22_5.plan as PlanGeometry;
const measures = cases.bow_22_5.measures as AssemblyMeasure;
const choices = [
  {
    sku: "ARTICULO-A",
    name: "Regulable con fuente",
    coupling_rule: {
      min_angle_deg: "0",
      max_angle_deg: "60",
      development_mm: "0",
      source: "Ficha A",
    },
  },
  {
    sku: "ARTICULO-B",
    name: "Esquina con fuente",
    coupling_rule: {
      min_angle_deg: "90",
      max_angle_deg: "90",
      development_mm: "0",
      source: "Ficha B",
    },
  },
  { sku: "ARTICULO-SIN-DATO", coupling_rule: null },
] as CouplerChoice[];

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  );
});
const props = () => ({
  plan,
  couplings: product.assembly.couplings,
  modules: product.assembly.modules,
  measures,
  members: resolveMembers(undefined),
  selectedModuleId: "m2",
  selectedCouplingId: null,
  issues: [],
  disabled: false,
  onSelectModule: vi.fn(),
  onSelectCoupling: vi.fn(),
  onCommitAngle: vi.fn(),
});

describe("Planta acoplada", () => {
  it.each(ANGLE_SNAPS)("snaps to %s degrees including the exact corner", (angle) => {
    expect(snapPlanAngle(angle + 1)).toBe(String(angle));
    expect(snapPlanAngle(-angle - 1)).toBe(String(-angle));
  });
  it("filters by declared authority, independent of SKU names", () => {
    expect(compatibleCouplers(choices, "22.5").map((item) => item.sku)).toEqual(["ARTICULO-A"]);
    expect(compatibleCouplers(choices, "89")).toEqual([]);
    expect(compatibleCouplers(choices, "-90").map((item) => item.sku)).toEqual(["ARTICULO-B"]);
  });
  it("keeps the chord horizontal without changing the motor points", () => {
    const before = JSON.stringify(plan),
      display = planDisplay(plan);
    expect(display.point(plan.front_chain.at(-1)!)[1]).toBeCloseTo(0);
    expect(JSON.stringify(plan)).toBe(before);
  });
  it("selects a module by keyboard and edits the joint with Chilean decimal input", () => {
    const callbacks = props();
    render(<BowPlanSvg {...callbacks} />);
    fireEvent.keyDown(screen.getByRole("button", { name: "Módulo 2 en planta" }), { key: "Enter" });
    expect(callbacks.onSelectModule).toHaveBeenCalledWith("m2");
    fireEvent.keyDown(screen.getByRole("button", { name: "Ángulo de unión 1" }), { key: "Enter" });
    const input = screen.getByRole("textbox", { name: "Ángulo de unión 1" });
    fireEvent.change(input, { target: { value: "30,0" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(callbacks.onCommitAngle).toHaveBeenCalledWith("c1", "30");
  });
  it("resizes by keyboard, exposes source-backed dimensions and routes the issue", () => {
    const issue: ProductIssue = {
      code: "coupler_angle_incompatible",
      severity: "error",
      target: "coupling:c1",
      params: {},
    };
    const onReviewIssue = vi.fn();
    render(
      <AssemblyPlanPane
        {...props()}
        issues={[issue]}
        onHide={vi.fn()}
        preview={false}
        pending={false}
        onReviewIssue={onReviewIssue}
        issueLabel={() => "Unión 1: revisa el ángulo"}
      />,
    );
    const resize = screen.getByRole("separator");
    fireEvent.keyDown(resize, { key: "ArrowUp" });
    expect(resize).toHaveAttribute("aria-valuenow", "276");
    expect(screen.getByText("Frente / cuerda")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Unión 1: revisa el ángulo" }));
    expect(onReviewIssue).toHaveBeenCalledWith(issue);
  });
  it("developed and projected elevations use the exact module placements", () => {
    const spaced = cases.bow_espaciado.measures as AssemblyMeasure;
    const developed = frontLayout(product, spaced),
      projected = frontLayout(product, spaced, true);
    expect(developed.totalW).toBe(Number(spaced.developed_width_mm));
    expect(developed.rects[1]!.x).toBe(Number(spaced.modules[1]!.developed_x_mm));
    expect(developed.joints[0]!.x).toBe(612);
    expect(developed.joints[1]!.x).toBe(1836);
    expect(projected.rects[0]!.w).toBe(Number(spaced.modules[0]!.projected_width_mm));
  });
  it("coincident stacked footprints have one legible label and both module selections", () => {
    const callbacks = props();
    const modules = product.assembly.modules
      .slice(0, 2)
      .map((module) => ({ ...module, width_mm: "600" }));
    const stackedPlan = {
      ...plan,
      modules: modules.map((module) => ({ ...plan.modules[0]!, module_id: module.id })),
      couplings: [],
    };
    render(
      <AssemblyPlanPane
        {...callbacks}
        plan={stackedPlan}
        modules={modules}
        couplings={[{ ...product.assembly.couplings[0]!, kind: "STACKED" }]}
        preview={false}
        pending={false}
        onHide={vi.fn()}
        onReviewIssue={vi.fn()}
        issueLabel={() => ""}
      />,
    );
    expect(screen.getByText("M1 / M2 · 600 mm")).toBeInTheDocument();
    const choices = screen.getByRole("group", { name: "Seleccionar módulos apilados" });
    const buttons = choices.querySelectorAll("button");
    fireEvent.click(buttons[0]!);
    expect(callbacks.onSelectModule).toHaveBeenLastCalledWith("m1");
    fireEvent.click(buttons[1]!);
    expect(callbacks.onSelectModule).toHaveBeenLastCalledWith("m2");
    expect(buttons[1]).toHaveAttribute("aria-pressed", "true");
  });
  it.each([
    ["coupler_angle_incompatible", "coupling:c1", "Acoplador"],
    ["coupler_profile_missing", "coupling:c1", "Acoplador"],
    ["coupler_profile_unknown", "coupling:c1", "Acoplador"],
    ["coupler_height_mismatch", "module:m1", "Alto"],
    ["coupler_width_mismatch", "module:m1", "Ancho"],
    ["assembly_folds_back", "coupling:c1", "Ángulo"],
    ["coupler_reinforcement_nonpositive", "coupling:c1", undefined],
  ])("%s navigates to the repair field", (code, target, label) => {
    const result = assemblyIssueDestination(
      { code: code!, target: "coupling:c1", severity: "error", params: {} },
      product,
    );
    expect(result.target).toBe(target);
    expect(result.label).toBe(label);
    if (code === "coupler_reinforcement_nonpositive") expect(result.catalog).toBe(true);
  });
});

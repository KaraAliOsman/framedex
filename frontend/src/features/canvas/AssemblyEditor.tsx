import { useEffect, useMemo, useState } from "react";

import "./canvas.css";

import type {
  DesignOptions,
  EngineAssemblyCalculateResponse,
  ProductIssue,
} from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { useCanvasStore, type CanvasDesignInputs } from "./canvasStore";
import { BowPlanContent, planBounds } from "./BowPlanSvg";
import { CanvasViewport } from "./CanvasViewport";
import { ObjectTree } from "./ObjectTree";
import { buildObjectTree } from "./objectTree";
import { resolveMembers } from "./members";
import {
  frontBounds,
  frontLayout,
  frontModuleBox,
  OpeningGlyph,
  ProductFrontContent,
} from "./ProductFrontSvg";

import { useAssemblyCalculation } from "./useAssemblyCalculation";
import type { SplitType } from "./intentEditing";
import {
  addAdjacentUnit,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  makeBowProduct,
  moduleGlassSku,
  moduleGlassThicknessMm,
  moduleOpening,
  modulePanelSku,
  removeUnit,
  scaleModuleWidths,
  setAllModuleHeights,
  setModuleGlass,
  setModuleGlassThickness,
  setModulePanel,
  setCouplerSku,
  setCouplingAngle,
  setModuleOpening,
  setModuleWidth,
  splitModuleBay,
  type CouplingJson,
  type ProductJson,
} from "./productEditing";

const OPENING_OPTIONS = [
  ["FIXED", "intent.fixed"],
  ["TURN_LEFT", "intent.turnLeft"],
  ["TURN_RIGHT", "intent.turnRight"],
  ["TILT_TURN_LEFT", "intent.tiltLeft"],
  ["TILT_TURN_RIGHT", "intent.tiltRight"],
  ["AWNING", "intent.awning"],
  ["SLIDING_2L", "intent.sliding"],
  ["DOOR_ENTRY", "intent.door"],
] as const;

const ISSUE_KEYS: Record<string, TranslationKey> = {
  couplings_count_mismatch: "assembly.issue.couplingsCountMismatch",
  assembly_folds_back: "assembly.issue.assemblyFoldsBack",
  plan_self_intersection: "assembly.issue.planSelfIntersection",
  module_geometry_failed: "assembly.issue.moduleGeometryFailed",
  coupler_profile_missing: "assembly.issue.couplerProfileMissing",
  coupler_profile_unknown: "assembly.issue.couplerProfileUnknown",
  coupler_height_mismatch: "assembly.issue.couplerHeightMismatch",
  coupler_reinforcement_nonpositive: "assembly.issue.couplerReinforcementNonpositive",
};

function issueText(issue: ProductIssue): string {
  const key = ISSUE_KEYS[issue.code];
  let text = key ? t(key) : issue.code;
  for (const [name, value] of Object.entries(issue.params)) {
    text = text.replace(`{${name}}`, value);
  }
  text = text.replace("{target}", issue.target.replace("coupling:", "").replace("module:", ""));
  const reason = issue.params["reason"];
  if (reason && !text.includes(reason)) text += ` — ${reason}`;
  return text;
}

function normalizeMm(candidate: string): string | null {
  const value = Number(candidate.replace(",", "."));
  if (!Number.isFinite(value) || value <= 0) return null;
  return value.toFixed(2);
}

function normalizeAngle(candidate: string): string | null {
  const value = Number(candidate.replace(",", "."));
  if (!Number.isFinite(value) || Math.abs(value) >= 90) return null;
  return value.toFixed(1);
}

type DraftFieldProps = {
  label?: string;
  value: string;
  unit: string;
  disabled: boolean;
  onCommit(value: string): void;
  normalize(candidate: string): string | null;
};

function DraftField({
  label,
  value,
  unit,
  disabled,
  onCommit,
  normalize,
}: DraftFieldProps): JSX.Element {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  return (
    <label className="assembly-field">
      {label ? <span>{label}</span> : null}
      <input
        value={draft}
        disabled={disabled}
        inputMode="decimal"
        onChange={(event) => setDraft(event.target.value)}
        onBlur={() => {
          const normalized = normalize(draft);
          if (normalized === null) setDraft(value);
          else if (normalized !== value) onCommit(normalized);
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") event.currentTarget.blur();
          if (event.key === "Escape") setDraft(value);
        }}
      />
      <span className="assembly-unit">{unit}</span>
    </label>
  );
}

export function createBowFromInputs(
  inputs: CanvasDesignInputs,
  glassThicknessMm = "4.00",
  glassSpec = "4",
  glassArticleSku: string | null = null,
): ProductJson {
  return makeBowProduct({
    moduleCount: 3,
    widthMm: Math.max(Number(inputs.nominalWidthMm) || 2100, 600),
    heightMm: Math.max(Number(inputs.nominalHeightMm) || 1400, 400),
    angleDeg: 15,
    glassThicknessMm,
    glassSpec,
    glassArticleSku,
  });
}

function statusKey(status: string | undefined): TranslationKey {
  if (status === "VALID") return "assembly.statusValid";
  if (status === "MANUFACTURING_INCOMPLETE") return "assembly.statusIncomplete";
  return "assembly.statusInvalid";
}

function ModuleInspector({
  module,
  product,
  glassSkus,
  glazingThicknesses,
  panelSkus,
  mullionSkus,
  busy,
  commit,
}: {
  module: ProductJson["assembly"]["modules"][number];
  product: ProductJson;
  glassSkus: string[];
  glazingThicknesses: string[];
  panelSkus: string[];
  mullionSkus: Partial<Record<SplitType, string>>;
  busy: boolean;
  commit(next: ProductJson): void;
}): JSX.Element {
  const opening = moduleOpening(module);
  const isDoor = opening === "DOOR_ENTRY";
  const ordinal = product.assembly.modules.findIndex((item) => item.id === module.id) + 1;
  return (
    <section className="assembly-inspector" aria-label={t("assembly.module")}>
      <header className="assembly-inspector__header">
        <h4>
          {t("assembly.module")} {ordinal}
        </h4>
        <button
          type="button"
          className="ghost-button is-danger"
          disabled={busy || product.assembly.modules.length <= 1}
          title={t("assembly.removeUnit")}
          aria-label={t("assembly.removeUnit")}
          onClick={() => commit(removeUnit(product, module.id))}
        >
          ×
        </button>
      </header>
      <details className="inspector-section" open>
        <summary>{t("assembly.opening")}</summary>
        <div className="opening-grid" role="group" aria-label={t("assembly.opening")}>
          {OPENING_OPTIONS.map(([value, labelKey]) => (
            <button
              key={value}
              type="button"
              className={`opening-choice${opening === value ? " is-active" : ""}`}
              title={t(labelKey)}
              aria-label={t(labelKey)}
              aria-pressed={opening === value}
              disabled={busy}
              onClick={() => commit(setModuleOpening(product, module.id, value))}
            >
              <svg viewBox="0 0 100 100" aria-hidden="true">
                <rect className="opening-choice__frame" x={4} y={4} width={92} height={92} />
                <OpeningGlyph opening={value} x={4} y={4} w={92} h={92} />
              </svg>
            </button>
          ))}
        </div>
        <div className="inspector-actions">
          <button
            type="button"
            className="ghost-button"
            disabled={busy || mullionSkus.SPLIT_V === undefined || isDoor}
            onClick={() =>
              commit(
                splitModuleBay(product, module.id, {
                  type: "SPLIT_V",
                  mullionSku: mullionSkus.SPLIT_V ?? "",
                }),
              )
            }
          >
            {t("assembly.splitV")}
          </button>
          <button
            type="button"
            className="ghost-button"
            disabled={busy || mullionSkus.SPLIT_H === undefined || isDoor}
            onClick={() =>
              commit(
                splitModuleBay(product, module.id, {
                  type: "SPLIT_H",
                  mullionSku: mullionSkus.SPLIT_H ?? "",
                }),
              )
            }
          >
            {t("assembly.splitH")}
          </button>
        </div>
      </details>
      <details className="inspector-section" open>
        <summary>{t("inspector.dimensions")}</summary>
        <DraftField
          label={t("assembly.width")}
          value={module.width_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) => commit(setModuleWidth(product, module.id, value))}
        />
        <DraftField
          label={t("assembly.height")}
          value={module.height_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) => commit(setAllModuleHeights(product, value))}
        />
      </details>
      <details className="inspector-section" open>
        <summary>{t("inspector.glazing")}</summary>
        <label className="assembly-field">
          <span>{t("assembly.glassThickness")}</span>
          <select
            aria-label={t("assembly.glassThickness")}
            disabled={busy}
            value={moduleGlassThicknessMm(module) ?? ""}
            onChange={(event) =>
              commit(setModuleGlassThickness(product, module.id, event.target.value || null))
            }
          >
            <option value="">{t("assembly.chooseThickness")}</option>
            {glazingThicknesses.map((thickness) => (
              <option key={thickness} value={thickness}>
                {thickness} mm
              </option>
            ))}
          </select>
        </label>
        <label className="assembly-field">
          <span>{t("assembly.glass")}</span>
          <select
            aria-label={t("assembly.glass")}
            disabled={busy}
            value={moduleGlassSku(module) ?? ""}
            onChange={(event) =>
              commit(setModuleGlass(product, module.id, event.target.value || null))
            }
          >
            <option value="">{t("assembly.noGlass")}</option>
            {glassSkus.map((sku) => (
              <option key={sku} value={sku}>
                {sku}
              </option>
            ))}
          </select>
        </label>
        {isDoor && (
          <label className="assembly-field">
            <span>{t("assembly.panel")}</span>
            <select
              aria-label={t("assembly.panel")}
              disabled={busy}
              value={modulePanelSku(module) ?? ""}
              onChange={(event) =>
                commit(setModulePanel(product, module.id, event.target.value || null))
              }
            >
              <option value="">{t("assembly.noPanel")}</option>
              {panelSkus.map((sku) => (
                <option key={sku} value={sku}>
                  {sku}
                </option>
              ))}
            </select>
          </label>
        )}
      </details>
    </section>
  );
}

function CouplingInspector({
  coupling,
  product,
  ordinal,
  couplerSkus,
  busy,
  commit,
}: {
  coupling: CouplingJson;
  product: ProductJson;
  ordinal: number;
  couplerSkus: string[];
  busy: boolean;
  commit(next: ProductJson): void;
}): JSX.Element {
  return (
    <section className="assembly-inspector" aria-label={t("assembly.coupling")}>
      <header className="assembly-inspector__header">
        <h4>
          {t("assembly.coupling")} {ordinal}
        </h4>
      </header>
      <DraftField
        label={t("assembly.angle")}
        value={coupling.angle_deg}
        unit="°"
        disabled={busy}
        normalize={normalizeAngle}
        onCommit={(value) => commit(setCouplingAngle(product, coupling.id, value))}
      />
      <label className="assembly-field">
        <span>{t("assembly.coupler")}</span>
        <select
          aria-label={t("assembly.coupler")}
          disabled={busy}
          value={coupling.coupler_profile_sku ?? ""}
          onChange={(event) =>
            commit(setCouplerSku(product, coupling.id, event.target.value || null))
          }
        >
          <option value="">{t("assembly.noCoupler")}</option>
          {couplerSkus.map((sku) => (
            <option key={sku} value={sku}>
              {sku}
            </option>
          ))}
        </select>
      </label>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button"
          disabled={busy || Number(coupling.angle_deg) === 0}
          onClick={() => commit(setCouplingAngle(product, coupling.id, "0"))}
        >
          {t("assembly.straighten")}
        </button>
      </div>
    </section>
  );
}

type EditorTool = "select" | "split_v" | "split_h";

function ToolIcon({ name }: { name: string }): JSX.Element {
  const strokes: Record<string, JSX.Element> = {
    select: <path d="M4 2l10 5.5-4.2 1.2L12 13l-2 1.4-2.2-4.3-3.8 2.9z" />,
    split_v: <path d="M3 3h10v10H3z M8 3v10" />,
    split_h: <path d="M3 3h10v10H3z M3 8h10" />,
    couple_left: <path d="M6 3h7v10H6z M5.5 8H1 M2.5 5.5L1 8l1.5 2.5" />,
    couple_right: <path d="M3 3h7v10H3z M10.5 8H15 M13.5 5.5L15 8l-1.5 2.5" />,
    equalize: <path d="M3 5h10 M8 2.5L10.5 5 8 7.5 M3 11h10 M8 8.5L10.5 11 8 13.5" />,
    tree: <path d="M4 3h9 M4 8h9 M4 13h9 M1 3h.5 M1 8h.5 M1 13h.5" />,
  };
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className="tool-icon">
      {strokes[name]}
    </svg>
  );
}

export function AssemblyEditor({
  organizationId,
  couplerSkus,
  glassSkus,
  panelSkus,
  options,
  disabled,
  onChanged,
  onEvaluationChange,
  positionPanel,
}: {
  organizationId: string;
  couplerSkus: string[];
  glassSkus: string[];
  panelSkus: string[];
  options: DesignOptions | undefined;
  disabled: boolean;
  onChanged(): void;
  onEvaluationChange(evaluation: EngineAssemblyCalculateResponse | null): void;
  positionPanel?: JSX.Element;
}): JSX.Element | null {
  const inputs = useCanvasStore((state) => state.inputs);
  const commitInputs = useCanvasStore((state) => state.commitInputs);
  const selection = useCanvasStore((state) => state.selection);
  const select = useCanvasStore((state) => state.select);
  const product = inputs.product;
  const { evaluation, isPending, errorCode } = useAssemblyCalculation(organizationId, inputs);
  const issues = evaluation?.issues ?? [];
  const members = useMemo(() => resolveMembers(options), [options]);
  const [tool, setTool] = useState<EditorTool>("select");
  const [treeOpen, setTreeOpen] = useState(true);
  const [planOpen, setPlanOpen] = useState(true);

  useEffect(() => {
    onEvaluationChange(evaluation);
  }, [evaluation, onEvaluationChange]);

  function commit(next: ProductJson): void {
    if (next === product) return;
    commitInputs({ ...inputs, product: next });
    onChanged();
  }

  if (!product) {
    return (
      <section className="assembly-editor assembly-editor--empty">
        <div className="assembly-canvas canvas-empty">
          <p className="assembly-hint">{t("assembly.pickStarter")}</p>
        </div>
        <aside className="assembly-side">
          {positionPanel ?? <p className="assembly-hint">{t("assembly.elementHint")}</p>}
        </aside>
      </section>
    );
  }
  const productJson = product;
  const modules = product.assembly.modules;
  const couplings = product.assembly.couplings;
  const selectedModule = modules.find((module) => module.id === selection);
  const selectedCoupling = couplings.find((coupling) => coupling.id === selection);
  // isPending also holds while the query is disabled (no system/product yet):
  // only an actual in-flight evaluation locks editing.
  const evaluating = isPending && inputs.systemId !== null;
  const busy = disabled || evaluating;
  const mullionSkus: Partial<Record<SplitType, string>> = {
    SPLIT_V: options?.profiles.find((profile) => profile.role === "MULLION_V")?.sku,
    SPLIT_H: options?.profiles.find((profile) => profile.role === "MULLION_H")?.sku,
  };

  const front = frontLayout(product);
  const frontBox = frontBounds(product);
  const planBox = couplings.length > 0 && evaluation?.plan ? planBounds(evaluation.plan) : null;
  const selectionBox = frontModuleBox(product, selectedModule?.id ?? null);
  const statusText = `${front.totalW.toFixed(0)} × ${front.height.toFixed(0)} mm`;
  const selectedLabel = selection?.startsWith("coupling-")
    ? null
    : selectedModule
      ? `${t("assembly.module")} ${modules.findIndex((item) => item.id === selection) + 1}`
      : selectedCoupling
        ? `${t("assembly.coupling")} ${couplings.findIndex((item) => item.id === selection) + 1}`
        : null;

  // Divide tool: the next module click applies the pending split instead of
  // only selecting. Any other edit returns the tool to select.
  function pickModule(id: string): void {
    const type = tool === "split_v" ? "SPLIT_V" : tool === "split_h" ? "SPLIT_H" : null;
    const sku =
      type === "SPLIT_V"
        ? mullionSkus.SPLIT_V
        : type === "SPLIT_H"
          ? mullionSkus.SPLIT_H
          : undefined;
    if (type !== null && sku !== undefined) {
      commit(splitModuleBay(productJson, id, { type, mullionSku: sku }));
      setTool("select");
    }
    select(id);
  }
  const objectTree = useMemo(
    () => buildObjectTree(product, members, issues, t),
    [product, members, issues],
  );

  function coupleUnit(side: "left" | "right"): void {
    const next = addAdjacentUnit(productJson, side);
    commit(next);
    select(
      next.assembly.modules[side === "left" ? 0 : next.assembly.modules.length - 1]?.id ?? null,
    );
  }

  const splitReady = { SPLIT_V: mullionSkus.SPLIT_V, SPLIT_H: mullionSkus.SPLIT_H };
  return (
    <div
      className={`assembly-editor${treeOpen ? "" : " assembly-editor--tree-closed"}`}
      aria-label={t("assembly.frontView")}
    >
      <div className="assembly-tools" role="toolbar" aria-label={t("assembly.tools")}>
        <button
          type="button"
          className={`tool-button${tool === "select" ? " is-active" : ""}`}
          title={t("assembly.toolSelect")}
          aria-label={t("assembly.toolSelect")}
          aria-pressed={tool === "select"}
          onClick={() => setTool("select")}
        >
          <ToolIcon name="select" />
        </button>
        <button
          type="button"
          className={`tool-button${tool === "split_v" ? " is-active" : ""}`}
          title={t("assembly.toolDivideV")}
          aria-label={t("assembly.toolDivideV")}
          aria-pressed={tool === "split_v"}
          disabled={busy || splitReady.SPLIT_V === undefined}
          onClick={() => setTool(tool === "split_v" ? "select" : "split_v")}
        >
          <ToolIcon name="split_v" />
        </button>
        <button
          type="button"
          className={`tool-button${tool === "split_h" ? " is-active" : ""}`}
          title={t("assembly.toolDivideH")}
          aria-label={t("assembly.toolDivideH")}
          aria-pressed={tool === "split_h"}
          disabled={busy || splitReady.SPLIT_H === undefined}
          onClick={() => setTool(tool === "split_h" ? "select" : "split_h")}
        >
          <ToolIcon name="split_h" />
        </button>
        <span className="assembly-tools__divider" aria-hidden="true" />
        <button
          type="button"
          className="tool-button"
          title={t("assembly.addUnitLeft")}
          aria-label={t("assembly.addUnitLeft")}
          disabled={busy}
          onClick={() => coupleUnit("left")}
        >
          <ToolIcon name="couple_left" />
        </button>
        <button
          type="button"
          className="tool-button"
          title={t("assembly.addUnitRight")}
          aria-label={t("assembly.addUnitRight")}
          disabled={busy}
          onClick={() => coupleUnit("right")}
        >
          <ToolIcon name="couple_right" />
        </button>
        <span className="assembly-tools__divider" aria-hidden="true" />
        <button
          type="button"
          className="tool-button"
          title={t("assembly.equalizeModules")}
          aria-label={t("assembly.equalizeModules")}
          disabled={busy || modules.length <= 1}
          onClick={() => commit(equalizeModuleWidths(product))}
        >
          <ToolIcon name="equalize" />
        </button>
        <button
          type="button"
          className="tool-button"
          title={t("assembly.equalizeAngles")}
          aria-label={t("assembly.equalizeAngles")}
          disabled={busy || couplings.length === 0}
          onClick={() => commit(equalizeCouplingAngles(product))}
        >
          <ToolIcon name="equalize" />
        </button>
        <span className="assembly-tools__spacer" aria-hidden="true" />
        <button
          type="button"
          className={`tool-button${treeOpen ? " is-active" : ""}`}
          title={t("assembly.toggleTree")}
          aria-label={t("assembly.toggleTree")}
          aria-pressed={treeOpen}
          onClick={() => setTreeOpen((open) => !open)}
        >
          <ToolIcon name="tree" />
        </button>
      </div>
      {treeOpen && (
        <div className="assembly-tree">
          <ObjectTree
            root={objectTree}
            selection={selection}
            onSelect={(id) => {
              if (id !== null && modules.some((module) => module.id === id)) pickModule(id);
              else select(id);
            }}
            title={t("tree.title")}
          />
        </div>
      )}
      <div className="assembly-canvas">
        <CanvasViewport contentBox={frontBox} selectionBox={selectionBox} status={statusText}>
          <ProductFrontContent
            product={product}
            members={members}
            selectedId={selectedModule?.id ?? null}
            issues={issues}
            disabled={busy}
            onSelectModule={pickModule}
            onAddUnit={coupleUnit}
            onCommitModuleWidth={(moduleId, widthMm) =>
              commit(setModuleWidth(product, moduleId, widthMm))
            }
            onCommitTotalWidth={(totalMm) => commit(scaleModuleWidths(product, totalMm))}
            onCommitHeight={(heightMm) => commit(setAllModuleHeights(product, heightMm))}
          />
        </CanvasViewport>
        {couplings.length > 0 && evaluation?.plan && planBox && planOpen && (
          <div className="plan-inset" role="complementary" aria-label={t("assembly.planView")}>
            <div className="plan-inset__header">
              <span>{t("assembly.planView")}</span>
              <button
                type="button"
                aria-label={t("assembly.hidePlan")}
                onClick={() => setPlanOpen(false)}
              >
                ×
              </button>
            </div>
            <svg
              className="plan-inset__svg"
              viewBox={`${planBox.x} ${planBox.y} ${planBox.w} ${planBox.h}`}
              preserveAspectRatio="xMidYMid meet"
            >
              <BowPlanContent
                plan={evaluation.plan}
                couplings={couplings}
                members={members}
                selectedModuleId={selectedModule?.id ?? null}
                selectedCouplingId={selectedCoupling?.id ?? null}
                issues={issues}
                disabled={busy}
                onSelectModule={pickModule}
                onSelectCoupling={select}
                onCommitAngle={(couplingId, angleDeg) =>
                  commit(setCouplingAngle(product, couplingId, angleDeg))
                }
              />
            </svg>
          </div>
        )}
        {couplings.length > 0 && evaluation?.plan && !planOpen && (
          <button type="button" className="plan-toggle" onClick={() => setPlanOpen(true)}>
            {t("assembly.planView")}
          </button>
        )}
      </div>
      <div className="assembly-side">
        {selectedModule ? (
          <ModuleInspector
            module={selectedModule}
            product={product}
            glassSkus={glassSkus}
            glazingThicknesses={options?.glazing_thicknesses ?? []}
            panelSkus={panelSkus}
            mullionSkus={mullionSkus}
            busy={busy}
            commit={commit}
          />
        ) : selectedCoupling ? (
          <CouplingInspector
            coupling={selectedCoupling}
            product={product}
            ordinal={couplings.findIndex((item) => item.id === selectedCoupling.id) + 1}
            couplerSkus={couplerSkus}
            busy={busy}
            commit={commit}
          />
        ) : (
          !positionPanel && (
            <section className="assembly-inspector">
              <p className="assembly-hint">{t("assembly.elementHint")}</p>
            </section>
          )
        )}
        {positionPanel}
        {issues.length > 0 && (
          <ul className="assembly-issues" aria-label={t("assembly.issues")}>
            {issues.map((issue, index) => (
              <li key={`${issue.code}-${index}`}>
                <button
                  type="button"
                  className={`issue-chip issue-chip--${issue.severity}`}
                  onClick={() => {
                    const target = issue.target;
                    if (target.startsWith("module:") || target.startsWith("coupling:")) {
                      select(target.slice(target.indexOf(":") + 1));
                    }
                  }}
                >
                  {issueText(issue)}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <footer className="assembly-statusbar">
        <span
          className={`assembly-status assembly-status--${
            inputs.systemId === null ? "idle" : (evaluation?.status ?? "INVALID").toLowerCase()
          }`}
          data-testid="assembly-status"
        >
          {evaluating
            ? t("assembly.calculating")
            : inputs.systemId === null
              ? t("assembly.chooseSystemHint")
            : errorCode
              ? t("assembly.calculateError")
              : t(statusKey(evaluation?.status))}
        </span>
        <span className="assembly-statusbar__dims">{statusText}</span>
        {selectedLabel && <span className="assembly-statusbar__selection">{selectedLabel}</span>}
        {issues.length > 0 && (
          <button
            type="button"
            className="assembly-statusbar__issues"
            onClick={() => {
              const first = issues[0];
              if (
                first &&
                (first.target.startsWith("module:") || first.target.startsWith("coupling:"))
              ) {
                select(first.target.slice(first.target.indexOf(":") + 1));
              }
            }}
          >
            {t("assembly.issueCount").replace("{count}", String(issues.length))}
          </button>
        )}
      </footer>
    </div>
  );
}

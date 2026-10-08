import { fmtMm, formatDecimal, parseLocaleNumber } from "../../format";
import { lazy, Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import "./canvas.css";

import type {
  DesignOptions,
  EngineAssemblyCalculateResponse,
  GlassSpecChoice,
  PanelChoice,
  ProductIssue,
} from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { domainLabel } from "../../i18n/domainLabels";
import {
  formatShortcut,
  resolveCommands,
  useCommandShortcuts,
  useRegisterCommands,
} from "../commands/registry";
import type { CommandContext, EditorTool } from "../commands/types";
import { useCanvasStore } from "./canvasStore";
import { assemblyCommands } from "./assemblyCommands";
import { AlternativesPanel } from "./AlternativesPanel";
import { AssistantPanel } from "./AssistantPanel";
import { applyOperationEffects } from "./designOps";
import { bayOperations, slidingOperation } from "./operationIntents";
import { designOperationsSimulate } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { DesignOperationRequest } from "../../api/generated/models";
import type { CommandArgs, CommandSpec } from "../commands/types";
import { useRegisterDesignOpsBridge } from "../assistant/assistantContext";
import type { DesignOperation } from "../../api/generated/models";
import { BowPlanContent, planBounds } from "./BowPlanSvg";
import { CanvasViewport } from "./CanvasViewport";
import { ObjectTree } from "./ObjectTreeView";
import { buildObjectTree } from "./objectTree";
import { resolveMembers, type MemberGeometry } from "./members";
import { EditorFlyout } from "./EditorFlyout";
import { useEditorMedia } from "./useEditorLayout";
import { dividerNudge } from "./dividerNudge";
import { dismissFloatingLayers, useFloatingLayer } from "../../ui/floatingLayer";
import { decimalInputValue, formatMoney } from "../../decimal";
import type { Simulation } from "../../api/generated/models";
import type { EditorPrice } from "./useEditorPrice";
import { HardwarePanel } from "./HardwarePanel";
import type { HardwareResolution } from "./hardwareContracts";
import { SectionView } from "./SectionView";
import { SectionPreviewSvg } from "./SectionPreviewSvg";
import {
  frontBounds,
  frontLayout,
  frontModuleBox,
  OpeningGlyph,
  ProductFrontContent,
} from "./ProductFrontSvg";

import { useAssemblyCalculation } from "./useAssemblyCalculation";
import type { IntentNode, Opening, SlidingLayout, SplitType } from "./intentEditing";
import { declareSlidingTravel, slidingTravel } from "./intentEditing";
import {
  findNode,
  intentBays,
  isSlidingOpening,
  resolvedSlidingLayout,
  topIntent,
  updateBay,
  SLIDING_PRESETS,
} from "./intentEditing";
import {
  canRemoveModuleDivision,
  moduleGlassSku,
  moduleGlassThicknessMm,
  moduleOpening,
  modulePanelSku,
  modulePrimaryBay,
  contourTopCorners,
  setModuleTree,
  isProductModel,
  type CouplingJson,
  type FramelessEdge,
  type FramelessFittingJson,
  type FramelessSpecJson,
  type FramelessSupportJson,
  type ProductJson,
  type ProductModuleJson,
} from "./productEditing";
import { OPENING_OPTIONS } from "./openings";
import { OpeningPalette } from "./OpeningPalette";
import {
  openingChoices,
  physicalNodeLabel,
  visualOpening,
  type OpeningLeafFact,
} from "./physicalOpenings";
import { GlassSelector } from "../glass/GlassSelector";
import { asGlassProduct } from "../glass/glassModel";
import { glassContext, useGlassChecks } from "../glass/useGlassPreview";
import { ExtrasInspector } from "../projects/ExtrasInspector";
import { MountingInspector } from "../projects/MountingInspector";
import { MountingDimensions } from "../projects/MountingDimensions";

/** §16 3D view: three.js + the scene builder stay out of the editing path —
 * the bundle only loads when the user opens the panel (lazy chunk), and
 * frameloop="demand" keeps it idle between interactions. */
const Model3DView = lazy(() => import("./Model3DView"));

const ISSUE_KEYS: Record<string, TranslationKey> = {
  couplings_count_mismatch: "assembly.issue.couplingsCountMismatch",
  assembly_folds_back: "assembly.issue.assemblyFoldsBack",
  plan_self_intersection: "assembly.issue.planSelfIntersection",
  module_geometry_failed: "assembly.issue.moduleGeometryFailed",
  coupler_profile_missing: "assembly.issue.couplerProfileMissing",
  coupler_profile_unknown: "assembly.issue.couplerProfileUnknown",
  coupler_height_mismatch: "assembly.issue.couplerHeightMismatch",
  coupler_reinforcement_nonpositive: "assembly.issue.couplerReinforcementNonpositive",
  contour_invalid: "assembly.issue.contourInvalid",
  contour_splits_unsupported: "assembly.issue.contourSplits",
  contour_opening_unsupported: "assembly.issue.contourOpening",
  contour_panel_unsupported: "assembly.issue.contourPanel",
  contour_coupling_unsupported: "assembly.issue.contourCoupling",
  member_bending_required: "assembly.issue.memberBending",
  coupler_width_mismatch: "assembly.issue.couplerWidthMismatch",
  coupler_module_unknown: "assembly.issue.couplerModuleUnknown",
  coupler_edge_invalid: "assembly.issue.couplerEdgeInvalid",
  coupler_edge_conflict: "assembly.issue.couplerEdgeConflict",
  connection_type_unsupported: "assembly.issue.connectionTypeUnsupported",
  assembly_disconnected: "assembly.issue.assemblyDisconnected",
  stacked_cycle: "assembly.issue.stackedCycle",
  inline_not_adjacent: "assembly.issue.inlineNotAdjacent",
  sliding_layout_invalid: "assembly.issue.slidingLayoutInvalid",
  sliding_tracks_unsupported: "assembly.issue.slidingTracksUnsupported",
  frameless_contour_unsupported: "assembly.issue.framelessContour",
  frameless_splits_unsupported: "assembly.issue.framelessSplits",
  frameless_opening_unsupported: "assembly.issue.framelessOpening",
  frameless_panel_unsupported: "assembly.issue.framelessPanel",
  frameless_article_unknown: "assembly.issue.framelessArticleUnknown",
  member_exceeds_stock: "assembly.issue.memberExceedsStock",
  hardware_kit_incompatible: "assembly.issue.hardwareKitIncompatible",
  hardware_kit_overweight: "assembly.issue.hardwareKitOverweight",
  hardware_undecidable: "assembly.issue.hardwareUndecidable",
};

/** Engine failure reasons arrive as `str(error)` — member ids and field
 * names never reach the user; each known cause maps to a readable phrase
 * and anything unrecognized degrades to a generic sentence. */
export const REASON_KEYS: [RegExp, TranslationKey][] = [
  [/requires glass_thickness_mm and glass_spec/i, "assembly.reason.glassRequired"],
  [/requires opening_type/i, "assembly.reason.openingRequired"],
  [/requires panel_article_sku/i, "assembly.reason.panelRequired"],
  [/requires split offset and mullion sku/i, "assembly.reason.splitMullionRequired"],
  [/requires at least two modules/i, "assembly.reason.bowTwoModules"],
  [/requires at least one module/i, "assembly.reason.oneModule"],
  [/requires a top-level bay/i, "assembly.reason.doorNeedsBay"],
  [/requires an opening type/i, "assembly.reason.openingRequired"],
  [/zero-length segment/i, "assembly.reason.contourDegenerate"],
  [/sagitta exceeds/i, "assembly.reason.contourSagitta"],
  [/self-intersect/i, "assembly.reason.contourSelfIntersect"],
  [/requires a sliding_layout/i, "assembly.reason.slidingLayoutRequired"],
  [/not a sliding opening/i, "assembly.reason.slidingLayoutRequired"],
  [/duplicate panel slot/i, "assembly.reason.slidingDuplicateSlot"],
  [/undeclared track/i, "assembly.reason.slidingBadTrack"],
  [/cannot occupy a track/i, "assembly.reason.slidingFixedTrack"],
  [/adjacent fixed panels/i, "assembly.reason.slidingFixedAdjacent"],
  [/cannot share a track/i, "assembly.reason.slidingSameTrack"],
  [/at least one moving panel/i, "assembly.reason.slidingNoMoving"],
  [/frame inset collapsed the glass pocket/i, "assembly.reason.glassPocketCollapsed"],
  [/handle height requires explicit/i, "assembly.reason.handleHeightMigration"],
  [/polishing authority/i, "assembly.reason.polishingAuthority"],
  [/requires policy placement/i, "assembly.reason.policyPlacement"],
  [/requires all four bead offsets/i, "assembly.reason.beadOffsets"],
  [/no compatible hardware kit/i, "assembly.reason.noHardwareKit"],
  [/hardware compatibility undecidable|leaf mass unknown/i, "assembly.reason.hardwareUndecidable"],
  [/ambiguous hardware kits/i, "assembly.reason.ambiguousHardware"],
];

export function issueText(
  issue: ProductIssue,
  modules: ProductModuleJson[],
  couplings: CouplingJson[],
): string {
  const key = ISSUE_KEYS[issue.code];
  // Unmapped engine codes still read as sentences — a chip that shows
  // "R02_LEAF_PROPORTION" asks the user to decode our own identifier.
  let text = key
    ? t(key)
    : (issue.params.reason ?? "Revisa la compatibilidad y los datos del catálogo.");
  if (issue.params.source) text += " Fuente: " + issue.params.source;
  for (const [name, value] of Object.entries(issue.params)) {
    if (name === "reason") continue;
    // Engine params arrive as str(Decimal) — "345.00" reads as technical
    // noise in a sentence; trim to the human form.
    const human = name.endsWith("_kg")
      ? formatDecimal(value, 1)
      : name.endsWith("_mm")
        ? fmtMm(value)
        : /^-?\d+\.\d+0*$/.test(value)
          ? value.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "")
          : value;
    text = text.replace(`{${name}}`, human);
  }
  const [kind, id] = issue.target.split(":", 2);
  const ordinal =
    kind === "module"
      ? modules.findIndex((item) => item.id === id)
      : kind === "coupling"
        ? couplings.findIndex((item) => item.id === id)
        : -1;
  const noun =
    kind === "coupling"
      ? `la ${t("assembly.coupling").toLowerCase()}`
      : `el ${t("assembly.module").toLowerCase()}`;
  const target =
    ordinal >= 0
      ? `${noun} ${ordinal + 1}`
      : kind === "assembly"
        ? t("assembly.wholeAssembly")
        : noun;
  text = text.replace("{target}", target);
  const reason = issue.params["reason"];
  if (reason && !text.includes(reason)) {
    const matched = REASON_KEYS.find(([pattern]) => pattern.test(reason));
    text += ` — ${matched ? t(matched[1]) : t("assembly.reason.generic")}`;
  }
  return text;
}

const MAX_MM = 30000;

function normalizeMm(candidate: string): string | null {
  const value = parseLocaleNumber(candidate);
  if (value === null || value <= 0 || value > MAX_MM) return null;
  return value.toFixed(2);
}

function normalizeAngle(candidate: string): string | null {
  const value = parseLocaleNumber(candidate);
  if (value === null || Math.abs(value) >= 90) return null;
  return value.toFixed(1);
}

/** Contour coordinates are signed: zero/negative carry meaning (a vertical
 * side, an inward arc). Bounds keep the corner ordering the engine requires. */
function normalizeRange(candidate: string, min: number, max: number): string | null {
  const value = parseLocaleNumber(candidate);
  if (value === null || value < min || value >= max) return null;
  return value.toFixed(2);
}

/* Pickers label an option the way an estimator reads the catalog — the
 * composition/panel name first, the SKU as the qualifier. A bare SKU
 * ("GLASS-BASE") forces decoding shorthand mid-design. */
function panelLabel(sku: string, choices: PanelChoice[]): string {
  const name = choices.find((item) => item.sku === sku)?.name;
  return name ? `${name} · ${sku}` : sku;
}

type DraftFieldProps = {
  label?: string;
  value: string;
  unit: string;
  disabled: boolean;
  onCommit(value: string): void;
  normalize(candidate: string): string | null;
  /** Constraint shown when Enter rejects the value (e.g. the ±90° band on
   * coupling angles) — a silent revert reads as the field ignoring input. */
  rejectHint?: string;
};

function DraftField({
  label,
  value,
  unit,
  disabled,
  onCommit,
  normalize,
  rejectHint,
}: DraftFieldProps): JSX.Element {
  const inputText = decimalInputValue(value).replace(".", ",");
  const [draft, setDraft] = useState(inputText);
  const [invalid, setInvalid] = useState(false);
  const committed = useRef(false);
  useEffect(() => {
    setDraft(decimalInputValue(value).replace(".", ","));
    setInvalid(false);
  }, [value]);
  useEffect(() => {
    // A refused operation keeps the declared value unchanged. Reset only a
    // submitted draft after that transaction, preserving typing during engine
    // recalculation and unrelated pending evaluations.
    if (!disabled && committed.current) {
      committed.current = false;
      setDraft(decimalInputValue(value).replace(".", ","));
      setInvalid(false);
    }
  }, [disabled, value]);
  return (
    <label className={`assembly-field${invalid ? " is-invalid" : ""}`}>
      {label ? <span>{label}</span> : null}
      <span className="assembly-input-wrap">
        <input
          value={draft}
          disabled={disabled}
          inputMode="decimal"
          aria-label={label}
          aria-invalid={invalid || undefined}
          onFocus={(event) => event.currentTarget.select()}
          onChange={(event) => {
            setDraft(event.target.value);
            setInvalid(false);
          }}
          onBlur={() => {
            if (draft === inputText) return;
            const normalized = normalize(draft);
            if (normalized === null) {
              // Revert to the last valid value but keep the field flagged —
              // a silent snap-back reads as the input being ignored.
              setDraft(inputText);
              setInvalid(true);
            } else {
              if (normalized !== value) {
                committed.current = true;
                onCommit(normalized);
              }
              setInvalid(false);
            }
          }}
          onKeyDown={(event) => {
            // Enter on an unparseable value keeps the field open and flags
            // it — reverting silently reads as the input being ignored.
            if (event.key === "Enter") {
              if (normalize(draft) === null) {
                setInvalid(true);
              } else {
                event.currentTarget.blur();
              }
            }
            if (event.key === "Escape") {
              event.preventDefault();
              event.stopPropagation();
              setInvalid(false);
              setDraft(inputText);
            }
          }}
        />
        <span className="assembly-unit">{unit}</span>
      </span>
      {invalid ? (
        <span className="assembly-field-error" role="alert">
          {rejectHint ?? t("assembly.fieldRejected")}
        </span>
      ) : null}
    </label>
  );
}

function statusKey(status: string | undefined): TranslationKey {
  if (status === "VALID") return "assembly.statusValid";
  if (status === "MANUFACTURING_INCOMPLETE") return "assembly.statusIncomplete";
  return "assembly.statusInvalid";
}

/** Editable semantic fields of a contour outline: the two top-corner
 * offsets for a straight chord, plus one rise per bulged edge. Free-form
 * outlines expose a vertex count until the polygon editor lands. */
function ContourShapeSection({
  module,
  busy,
  commit,
}: {
  module: ProductModuleJson;
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
}): JSX.Element {
  const contour = module.contour!;
  const corners = contourTopCorners(contour);
  const hasBulges = contour.bulges.some((bulge) => bulge !== null && bulge !== undefined);
  const widthMm = Number(module.width_mm);
  const leftBound = corners ? Number(contour.vertices[corners.rightIndex]!.x_mm) : 0;
  const rightBound = corners ? widthMm - Number(contour.vertices[corners.leftIndex]!.x_mm) : 0;
  // Sagitta is signed and bounded by half the chord (minor arcs only);
  // zero straightens the edge back to a line.
  const edgeChordMm = (edgeIndex: number): number => {
    const n = contour.vertices.length;
    const a = contour.vertices[edgeIndex % n]!;
    const b = contour.vertices[(edgeIndex + 1) % n]!;
    return Math.hypot(Number(b.x_mm) - Number(a.x_mm), Number(b.y_mm) - Number(a.y_mm));
  };
  return (
    <details className="inspector-section" open>
      <summary>{t("assembly.shape")}</summary>
      {corners && !hasBulges && (
        <>
          <DraftField
            label={t("assembly.shapeOffsetLeft")}
            value={Number(contour.vertices[corners.leftIndex]!.x_mm).toFixed(2)}
            unit="mm"
            disabled={busy}
            normalize={(candidate) => normalizeRange(candidate, 0, leftBound)}
            onCommit={(value) =>
              commit([
                {
                  op: "set_contour_vertex",
                  module: module.id,
                  index: corners.leftIndex,
                  x_mm: value,
                  y_mm: contour.vertices[corners.leftIndex]!.y_mm,
                },
              ])
            }
          />
          <DraftField
            label={t("assembly.shapeOffsetRight")}
            value={(widthMm - Number(contour.vertices[corners.rightIndex]!.x_mm)).toFixed(2)}
            unit="mm"
            disabled={busy}
            normalize={(candidate) => normalizeRange(candidate, 0, rightBound)}
            onCommit={(value) =>
              commit([
                {
                  op: "set_contour_vertex",
                  module: module.id,
                  index: corners.rightIndex,
                  x_mm: value,
                  y_mm: contour.vertices[corners.rightIndex]!.y_mm,
                  from: "END",
                },
              ])
            }
          />
        </>
      )}
      {contour.bulges.map(
        (bulge, edgeIndex) =>
          bulge !== null &&
          bulge !== undefined && (
            <DraftField
              key={edgeIndex}
              label={t("assembly.shapeRise")}
              value={bulge}
              unit="mm"
              disabled={busy}
              normalize={(candidate) =>
                normalizeRange(
                  candidate,
                  -edgeChordMm(edgeIndex) / 2,
                  edgeChordMm(edgeIndex) / 2 + 0.01,
                )
              }
              onCommit={(value) =>
                commit([
                  { op: "set_contour_bulge", module: module.id, index: edgeIndex, rise_mm: value },
                ])
              }
            />
          ),
      )}
      {!corners && !hasBulges && (
        <p className="inspector-note">
          {t("assembly.shapeVertices").replace("{count}", String(contour.vertices.length))}
        </p>
      )}
    </details>
  );
}

const FRAMELESS_EDGES: [FramelessEdge, TranslationKey][] = [
  ["bottom", "assembly.framelessEdgeBottom"],
  ["top", "assembly.framelessEdgeTop"],
  ["left", "assembly.framelessEdgeLeft"],
  ["right", "assembly.framelessEdgeRight"],
];
const FRAMELESS_FITTING_KINDS: FramelessFittingJson["kind"][] = [
  "PATCH_FITTING",
  "CLAMP",
  "HINGE",
  "LOCK",
  "CONNECTOR",
  "SEAL",
  "SUPPORT",
];

function FramelessSection({
  module,
  couplerSkus,
  busy,
  commit,
}: {
  module: ProductModuleJson;
  couplerSkus: string[];
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
}): JSX.Element {
  const spec = module.frameless;
  const update = (next: FramelessSpecJson | null) =>
    commit([{ op: "set_frameless", module: module.id, spec: next }]);
  if (!spec) {
    return (
      <details className="inspector-section">
        <summary>{t("assembly.frameless")}</summary>
        <p className="inspector-note">{t("assembly.framelessHint")}</p>
        <div className="inspector-actions">
          <button
            type="button"
            className="ghost-button"
            disabled={busy}
            onClick={() => update({ supports: [], fittings: [] })}
          >
            {t("assembly.makeFrameless")}
          </button>
        </div>
      </details>
    );
  }
  const exposed = spec.exposed_edges ?? ["left", "right", "top", "bottom"];
  const setSupport = (index: number, next: Partial<FramelessSupportJson>) =>
    update({
      ...spec,
      supports: spec.supports.map((item, at) => (at === index ? { ...item, ...next } : item)),
    });
  const setFitting = (index: number, next: Partial<FramelessFittingJson>) =>
    update({
      ...spec,
      fittings: spec.fittings.map((item, at) => (at === index ? { ...item, ...next } : item)),
    });
  return (
    <details className="inspector-section" open>
      <summary>{t("assembly.frameless")}</summary>
      <p className="inspector-note">{t("assembly.framelessHint")}</p>
      <h5 className="inspector-subhead">{t("assembly.framelessSupports")}</h5>
      <ul className="frameless-rows">
        {spec.supports.map((support, index) => (
          <li key={index} className="frameless-row">
            <select
              aria-label={t("assembly.framelessEdge")}
              value={support.edge}
              disabled={busy}
              onChange={(event) => setSupport(index, { edge: event.target.value as FramelessEdge })}
            >
              {FRAMELESS_EDGES.map(([edge, key]) => (
                <option key={edge} value={edge}>
                  {t(key)}
                </option>
              ))}
            </select>
            <select
              aria-label={t("assembly.framelessKind")}
              value={support.kind}
              disabled={busy}
              onChange={(event) =>
                setSupport(index, {
                  kind: event.target.value as FramelessSupportJson["kind"],
                })
              }
            >
              <option value="CHANNEL">{t("assembly.framelessKindChannel")}</option>
              <option value="CLAMPS">{t("assembly.framelessKindClamps")}</option>
            </select>
            {support.kind === "CHANNEL" ? (
              <select
                aria-label={t("assembly.framelessSku")}
                value={support.article_sku}
                disabled={busy}
                onChange={(event) => setSupport(index, { article_sku: event.target.value })}
              >
                <option value="">{t("assembly.framelessSku")}…</option>
                {couplerSkus.map((sku) => (
                  <option key={sku} value={sku}>
                    {sku}
                  </option>
                ))}
              </select>
            ) : (
              <input
                aria-label={t("assembly.framelessSku")}
                type="text"
                value={support.article_sku}
                disabled={busy}
                onChange={(event) => setSupport(index, { article_sku: event.target.value })}
              />
            )}
            <input
              aria-label={t("assembly.framelessQty")}
              type="number"
              min={1}
              value={support.qty}
              disabled={busy}
              onChange={(event) =>
                setSupport(index, { qty: Math.max(1, Number(event.target.value) || 1) })
              }
            />
            <button
              type="button"
              className="ghost-button is-danger"
              aria-label={`${t("assembly.framelessRemoveItem")} ${t("assembly.framelessSupports")} ${index + 1}`}
              disabled={busy}
              onClick={() =>
                update({ ...spec, supports: spec.supports.filter((_, at) => at !== index) })
              }
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button"
          disabled={busy}
          onClick={() =>
            update({
              ...spec,
              supports: [
                ...spec.supports,
                { kind: "CHANNEL", edge: "bottom", article_sku: "", qty: 1 },
              ],
            })
          }
        >
          {t("assembly.framelessAddSupport")}
        </button>
      </div>
      <h5 className="inspector-subhead">{t("assembly.framelessFittings")}</h5>
      <ul className="frameless-rows">
        {spec.fittings.map((fitting, index) => (
          <li key={index} className="frameless-row">
            <select
              aria-label={t("assembly.framelessKind")}
              value={fitting.kind}
              disabled={busy}
              onChange={(event) =>
                setFitting(index, {
                  kind: event.target.value as FramelessFittingJson["kind"],
                })
              }
            >
              {FRAMELESS_FITTING_KINDS.map((kind) => (
                <option key={kind} value={kind}>
                  {t(`assembly.fittingKind.${kind}` as TranslationKey)}
                </option>
              ))}
            </select>
            <input
              aria-label={t("assembly.framelessSku")}
              type="text"
              value={fitting.sku}
              disabled={busy}
              onChange={(event) => setFitting(index, { sku: event.target.value })}
            />
            <input
              aria-label={t("assembly.framelessQty")}
              type="number"
              min={1}
              value={fitting.qty}
              disabled={busy}
              onChange={(event) =>
                setFitting(index, { qty: Math.max(1, Number(event.target.value) || 1) })
              }
            />
            <button
              type="button"
              className="ghost-button is-danger"
              aria-label={`${t("assembly.framelessRemoveItem")} ${t("assembly.framelessFittings")} ${index + 1}`}
              disabled={busy}
              onClick={() =>
                update({ ...spec, fittings: spec.fittings.filter((_, at) => at !== index) })
              }
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button"
          disabled={busy}
          onClick={() =>
            update({
              ...spec,
              fittings: [...spec.fittings, { kind: "PATCH_FITTING", sku: "", qty: 1 }],
            })
          }
        >
          {t("assembly.framelessAddFitting")}
        </button>
      </div>
      <h5 className="inspector-subhead">{t("assembly.framelessExposedEdges")}</h5>
      <div
        className="frameless-edges"
        role="group"
        aria-label={t("assembly.framelessExposedEdges")}
      >
        {FRAMELESS_EDGES.map(([edge, key]) => (
          <label key={edge} className="assembly-field assembly-field--inline">
            <input
              type="checkbox"
              checked={exposed.includes(edge)}
              disabled={busy}
              onChange={(event) => {
                const next = event.target.checked
                  ? [...exposed, edge]
                  : exposed.filter((item) => item !== edge);
                update({
                  ...spec,
                  exposed_edges:
                    next.length === 4
                      ? undefined
                      : FRAMELESS_EDGES.map(([candidate]) => candidate).filter((candidate) =>
                          next.includes(candidate),
                        ),
                });
              }}
            />
            <span>{t(key)}</span>
          </label>
        ))}
      </div>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button is-danger"
          disabled={busy}
          onClick={() => update(null)}
        >
          {t("assembly.framelessRemove")}
        </button>
      </div>
    </details>
  );
}

/** Detail levels on the right rail — the same selection shows progressively
 * more: identity & facts (overview), editable design intent (design), or the
 * engine's manufacturing output (technical). */
type DetailLevel = "overview" | "design" | "technical";

const DETAIL_LEVELS: { level: DetailLevel; labelKey: TranslationKey }[] = [
  { level: "overview", labelKey: "assembly.levelOverview" },
  { level: "design", labelKey: "assembly.levelDesign" },
  { level: "technical", labelKey: "assembly.levelTechnical" },
];

/** Sliding panel topology editor — shared by the module inspector (primary
 * bay) and the bay inspector (the leaf the layout actually lives on). */
function SlidingPanelsEditor({
  instanceId,
  layout,
  busy,
  onChange: commit,
}: {
  instanceId: string;
  layout: SlidingLayout;
  busy: boolean;
  onChange(next: SlidingLayout): void;
}): JSX.Element {
  const onChange = (next: SlidingLayout) => commit(declareSlidingTravel(next));
  return (
    <details className="inspector-section" open>
      <summary>{t("assembly.slidingLayout")}</summary>
      {layout.panels.some((panel) => panel.kind === "MOVING" && panel.travel == null) && (
        <p className="sliding-inferred" role="status">
          Dirección inferida · revisa el recorrido de cada hoja.
        </p>
      )}
      <div className="inspector-field">
        <label htmlFor={`tracks-${instanceId}`}>{t("assembly.slidingTracks")}</label>
        <select
          id={`tracks-${instanceId}`}
          value={layout.tracks}
          disabled={busy}
          onChange={(event) => {
            const tracks = Number(event.target.value);
            onChange({
              tracks,
              panels: layout.panels.map((panel, index) =>
                panel.kind === "MOVING" ? { ...panel, track: index % tracks } : panel,
              ),
            });
          }}
        >
          {[1, 2, 3, 4]
            .filter(
              (count) =>
                count === layout.tracks ||
                count >=
                  (layout.panels.filter((panel) => panel.kind === "MOVING").length > 1 ? 2 : 1),
            )
            .map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
        </select>
      </div>
      <ul className="sliding-panels" aria-label={t("assembly.slidingLayout")}>
        {layout.panels.map((panel, index) => (
          <li key={panel.slot} className="sliding-panel">
            <span className="sliding-panel__slot">
              {t("assembly.slidingPanel").replace("{index}", String(index + 1))}
            </span>
            <select
              aria-label={`${t("assembly.slidingPanel").replace("{index}", String(index + 1))} ${t("intent.opening")}`}
              value={panel.kind}
              disabled={busy}
              onChange={(event) => {
                const kind = event.target.value as "MOVING" | "FIXED";
                const panels = layout.panels.map((item, at) =>
                  at === index
                    ? {
                        ...item,
                        kind,
                        travel:
                          kind === "FIXED"
                            ? null
                            : (item.travel ??
                              (index * 2 < layout.panels.length ? "RIGHT" : "LEFT")),
                        track:
                          kind === "MOVING"
                            ? (item.track ?? index % Math.max(layout.tracks, 1))
                            : null,
                      }
                    : item,
                );
                onChange({ ...layout, panels });
              }}
            >
              <option value="MOVING">{t("assembly.panelMoving")}</option>
              <option value="FIXED">{t("assembly.panelFixed")}</option>
            </select>
            {panel.kind === "MOVING" && (
              <>
                <select
                  aria-label={`${t("assembly.slidingPanel").replace("{index}", String(index + 1))} ${t("assembly.panelTrack")}`}
                  value={panel.track ?? 0}
                  disabled={busy}
                  onChange={(event) => {
                    const track = Number(event.target.value);
                    const panels = layout.panels.map((item, at) =>
                      at === index ? { ...item, track } : item,
                    );
                    onChange({ ...layout, panels });
                  }}
                >
                  {Array.from({ length: layout.tracks }, (_, track) => (
                    <option key={track} value={track}>
                      {t("assembly.panelTrack")} {track + 1}
                    </option>
                  ))}
                </select>
                <select
                  aria-label={`Hoja ${index + 1} recorrido`}
                  disabled={busy}
                  value={slidingTravel(panel, index, layout.panels.length) ?? "RIGHT"}
                  onChange={(event) =>
                    onChange({
                      ...layout,
                      panels: layout.panels.map((item, at) =>
                        at === index
                          ? { ...item, travel: event.target.value as "LEFT" | "RIGHT" }
                          : item,
                      ),
                    })
                  }
                >
                  <option value="LEFT" disabled={index === 0}>
                    Hacia la izquierda
                  </option>
                  <option value="RIGHT" disabled={index === layout.panels.length - 1}>
                    Hacia la derecha
                  </option>
                </select>
              </>
            )}
          </li>
        ))}
      </ul>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button"
          disabled={busy || layout.panels.length >= 8}
          onClick={() =>
            onChange({
              ...layout,
              panels: [
                ...layout.panels,
                {
                  slot: `S${layout.panels.length + 1}`,
                  kind: "MOVING",
                  track: layout.panels.length % Math.max(layout.tracks, 1),
                },
              ],
            })
          }
        >
          {t("assembly.addPanel")}
        </button>
        <button
          type="button"
          className="ghost-button"
          disabled={busy || layout.panels.length <= 1}
          onClick={() =>
            onChange({
              ...layout,
              panels: layout.panels.slice(0, -1),
            })
          }
        >
          {t("assembly.removePanel")}
        </button>
      </div>
    </details>
  );
}

function LeafFacts({
  module,
  bay,
  evaluation,
  options,
  busy,
  onHandleHeight,
}: {
  module: ProductModuleJson;
  bay: IntentNode;
  evaluation: EngineAssemblyCalculateResponse | null;
  options?: DesignOptions;
  busy: boolean;
  onHandleHeight(value: string): void;
}) {
  const result = evaluation?.modules.find((item) => item.module_id === module.id)?.result;
  const facts = (result?.opening_leaves ?? []) as OpeningLeafFact[];
  const leaf = facts.find((item) => item.bay_id === bay.id);
  const hardware = result?.hardware_items.find((item) => item.bay_id === bay.id);
  const kit = options?.hardware_kits.find((item) => item.sku === hardware?.kit_sku);
  const resolved = hardware?.resolution as HardwareResolution | null | undefined;
  const glass = options?.glass_specs.find((item) => item.sku === bay.glass_article_sku);
  const handleHeight = bay.handle_height_mm ?? resolved?.handle_height_mm;
  return (
    <>
      {handleHeight != null && (
        <DraftField
          label="Altura de manilla"
          value={handleHeight}
          unit="mm"
          disabled={busy || resolved?.handle_minimum_mm === resolved?.handle_maximum_mm}
          normalize={normalizeMm}
          onCommit={onHandleHeight}
        />
      )}
      <dl className="editor-leaf-facts">
        <div>
          <dt>Composición</dt>
          <dd>{glass?.spec ?? bay.glass_spec ?? "Sin dato · elige vidrio"}</dd>
        </div>
        <div>
          <dt>Espesor</dt>
          <dd>
            {bay.glass_thickness_mm
              ? `${fmtMm(bay.glass_thickness_mm)} mm`
              : "Sin dato · elige vidrio"}
          </dd>
        </div>
        <div>
          <dt>Hoja · ancho</dt>
          <dd>
            {leaf || resolved
              ? `${fmtMm(leaf?.width_mm ?? resolved?.width_mm)} mm`
              : visualOpening(bay) === "FIXED"
                ? "No requiere · paño fijo"
                : "Sin dato · calcula el marco"}
          </dd>
        </div>
        <div>
          <dt>Hoja · alto</dt>
          <dd>
            {leaf || resolved
              ? `${fmtMm(leaf?.height_mm ?? resolved?.height_mm)} mm`
              : visualOpening(bay) === "FIXED"
                ? "No requiere · paño fijo"
                : "Sin dato · calcula el marco"}
          </dd>
        </div>
        <div>
          <dt>Kit derivado</dt>
          <dd>
            {kit?.name ??
              (visualOpening(bay) === "FIXED"
                ? "No requiere · paño fijo"
                : "Sin dato · revisa herrajes")}
          </dd>
        </div>
        <div>
          <dt>Manilla · lado</dt>
          <dd>
            {leaf?.handle
              ? leaf.handle.side === "LEFT"
                ? "Izquierda"
                : leaf.handle.side === "RIGHT"
                  ? "Derecha"
                  : "Cierre superior/inferior"
              : visualOpening(bay) === "FIXED"
                ? "No requiere · paño fijo"
                : "Sin dato · revisa apertura"}
          </dd>
        </div>
        <div>
          <dt>Fuente</dt>
          <dd>
            <details className="editor-leaf-facts__source">
              <summary>¿De dónde sale?</summary>
              <p>
                {leaf?.source ??
                  resolved?.source ??
                  "Evaluación del motor sobre la apertura declarada; composición y kit del catálogo de la serie."}
              </p>
            </details>
          </dd>
        </div>
      </dl>
    </>
  );
}

/** A bay (paño) is the leaf granularity the workshop thinks in — opening,
 * glazing and handle placement edit on this leaf alone, through the same
 * normalized request-tree every other canvas edit uses. */
function BayInspector({
  options,
  evaluation,
  module,
  bay,
  product,
  glassSpecs,
  panelSkus,
  panelChoices,
  organizationId,
  color,
  busy,
  commit,
  onOpeningPreview,
  onAskAssistant,
}: {
  options?: DesignOptions;
  evaluation: EngineAssemblyCalculateResponse | null;
  module: ProductModuleJson;
  bay: IntentNode;
  product: ProductJson;
  glassSpecs: GlassSpecChoice[];
  panelSkus: string[];
  panelChoices: PanelChoice[];
  organizationId: string;
  color: string;
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
  onOpeningPreview(next: ProductJson | null): void;
  onAskAssistant?(): void;
}): JSX.Element {
  const opening = visualOpening(bay);
  const isDoor = opening === "DOOR_ENTRY" || opening === "DOOR_DOUBLE";
  const physicalLeaves = (evaluation?.modules?.find((item) => item.module_id === module.id)?.result
    ?.opening_leaves ?? []) as OpeningLeafFact[];
  const activeLeaf = physicalLeaves.find((leaf) => leaf.bay_id === bay.id && leaf.handle);
  const physicalHandle = activeLeaf?.handle;
  const slidingLayout = resolvedSlidingLayout(bay);
  const bays = intentBays(module.tree);
  const bayOrdinal = bays.findIndex((node) => node.id === bay.id) + 1;
  const moduleOrdinal = product.assembly.modules.findIndex((item) => item.id === module.id) + 1;
  const isTopBay = topIntent(module.tree).id === bay.id;

  function patchBay(patch: Partial<IntentNode>): void {
    commit(bayOperations(module.id, bay.id, patch));
  }

  function pickOpening(next: Opening): void {
    if (next === "DOOR_ENTRY" && !isTopBay) return;
    patchBay({
      opening_type: next,
      opening: null,
      opening_use: null,
      hinged_layout: null,
      sliding_layout: next === "SLIDING" ? declareSlidingTravel(SLIDING_PRESETS.SLIDING_2L!) : null,
      panel_article_sku: next === "DOOR_ENTRY" ? (bay.panel_article_sku ?? null) : null,
      door_handedness: next === "DOOR_ENTRY" ? bay.door_handedness : null,
    });
  }

  const operable = opening !== "FIXED";
  const classHardware = options?.hardware_kits.some((kit) => kit.class_authority != null) ?? false;

  return (
    <section className="assembly-inspector" aria-label={t("assembly.bay")}>
      <header className="assembly-inspector__header">
        <h4>
          {t("assembly.bay")} {bayOrdinal} · {t("assembly.module")} {moduleOrdinal}
        </h4>
      </header>
      <div className="editor-basic-dimensions">
        <DraftField
          label="Ancho del marco"
          value={module.width_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) =>
            commit([{ op: "set_module_width", module: module.id, width_mm: value }])
          }
        />
        <DraftField
          label={module.contour?.bulges.some(Boolean) ? "Alto hasta arranque" : "Alto del marco"}
          value={module.height_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) => commit([{ op: "set_height", height_mm: value }])}
        />
      </div>
      <details className="inspector-section" open>
        <summary>{t("assembly.opening")}</summary>
        {options?.opening_capabilities?.length ? (
          <OpeningPalette
            compact
            options={options}
            bay={bay}
            disabled={busy}
            onPick={(patch) =>
              patchBay({
                ...patch,
                is_sidelight:
                  patch.opening_use === "DOOR" && patch.opening?.movement === "FIXED" && !isTopBay,
              })
            }
            onPreview={(patch) =>
              onOpeningPreview(
                patch
                  ? setModuleTree(product, module.id, updateBay(module.tree, bay.id, patch))
                  : null,
              )
            }
          />
        ) : (
          <>
            {" "}
            <div className="opening-grid" role="group" aria-label={t("assembly.opening")}>
              {OPENING_OPTIONS.filter(
                ([value]) => !options?.system_family || options.compatible_openings.includes(value),
              ).map(([value, labelKey]) => {
                const doorBlocked = value === "DOOR_ENTRY" && !isTopBay;
                return (
                  <button
                    key={value}
                    type="button"
                    className={`opening-choice${opening === value ? " is-active" : ""}`}
                    title={doorBlocked ? t("assembly.doorTopOnly") : t(labelKey)}
                    aria-label={t(labelKey)}
                    aria-pressed={opening === value}
                    disabled={busy || doorBlocked}
                    onClick={() => pickOpening(value)}
                  >
                    <svg viewBox="0 0 100 100" aria-hidden="true">
                      <rect className="opening-choice__frame" x={4} y={4} width={92} height={92} />
                      <OpeningGlyph opening={value} x={4} y={4} w={92} h={92} />
                    </svg>
                  </button>
                );
              })}
            </div>
          </>
        )}
        {isDoor && !bay.opening && (
          <label className="assembly-field">
            <span>{t("assembly.hingeSide")}</span>
            <select
              aria-label={t("assembly.hingeSide")}
              disabled={busy}
              value={bay.door_handedness ?? "LEFT"}
              onChange={(event) =>
                patchBay({ door_handedness: event.target.value as "LEFT" | "RIGHT" })
              }
            >
              <option value="LEFT">{t("assembly.hingeLeft")}</option>
              <option value="RIGHT">{t("assembly.hingeRight")}</option>
            </select>
          </label>
        )}
        {isDoor && !bay.opening && !isTopBay && (
          <p className="assembly-hint">{t("assembly.doorTopOnly")}</p>
        )}
      </details>
      {slidingLayout && (
        <SlidingPanelsEditor
          instanceId={bay.id}
          layout={slidingLayout}
          busy={busy}
          onChange={(next) => commit([slidingOperation(module.id, bay.id, next)])}
        />
      )}
      <details className="inspector-section" open>
        <summary>{t("inspector.glazing")}</summary>
        <GlassSelector
          compact
          options={options}
          choices={glassSpecs}
          node={bay}
          context={glassContext(bay, module.id, evaluation)}
          busy={busy}
          onPatch={patchBay}
        />
        {isDoor && (
          <label className="assembly-field">
            <span>{t("assembly.panel")}</span>
            <select
              aria-label={t("assembly.panel")}
              disabled={busy}
              value={bay.panel_article_sku ?? ""}
              onChange={(event) => patchBay({ panel_article_sku: event.target.value || null })}
            >
              <option value="">{t("assembly.noPanel")}</option>
              {panelSkus.map((sku) => (
                <option key={sku} value={sku}>
                  {panelLabel(sku, panelChoices)}
                </option>
              ))}
            </select>
          </label>
        )}
        {!classHardware && (!bay.opening || physicalHandle) && (
          <DraftField
            label={t("assembly.handleHeight")}
            value={bay.handle_height_mm ?? physicalHandle?.height_from_bottom_mm ?? ""}
            unit="mm"
            disabled={
              busy ||
              Boolean(
                physicalHandle &&
                physicalHandle.minimum_height_from_bottom_mm ===
                  physicalHandle.maximum_height_from_bottom_mm,
              )
            }
            normalize={normalizeMm}
            onCommit={(value) => patchBay({ handle_height_mm: value })}
          />
        )}
        {!classHardware && physicalHandle && (
          <p className="assembly-hint">
            Desde el borde inferior de la hoja ·{" "}
            {fmtMm(physicalHandle.minimum_height_from_bottom_mm)}–
            {fmtMm(physicalHandle.maximum_height_from_bottom_mm)} mm. Fuente:{" "}
            {physicalHandle.source}
          </p>
        )}
      </details>
      <LeafFacts
        module={module}
        bay={bay}
        evaluation={evaluation}
        options={options}
        busy={busy}
        onHandleHeight={(value) =>
          commit(bayOperations(module.id, bay.id, { handle_height_mm: value }))
        }
      />
      {operable && (
        <details className="inspector-section">
          <summary>Avanzado · herrajes y manilla</summary>
          <HardwarePanel
            options={options}
            module={module}
            bay={bay}
            organizationId={organizationId}
            color={color}
            busy={busy}
            onPatch={patchBay}
            onTree={(tree) => commit([{ op: "set_module_tree", module: module.id, tree }])}
          />
        </details>
      )}
      <details className="inspector-section editor-advanced">
        <summary>Avanzado · perfiles y procedencia</summary>
        <CatalogLimitNotice options={options} opening={opening} />
        <ProvenanceStrip
          items={[
            { label: t("assembly.opening"), state: "DECLARED" },
            // A panelled door leaf is complete without glass — name the panel,
            // not a "Sin definir Vidrio" chip for a leaf that has none.
            isDoor && bay.panel_article_sku
              ? { label: t("assembly.panel"), state: "VERIFIED" as const }
              : {
                  label: t("assembly.glass"),
                  state: bay.glass_article_sku
                    ? ("VERIFIED" as const)
                    : opening === "FIXED" || isDoor
                      ? ("UNKNOWN" as const)
                      : ("BLOCKED" as const),
                },
            {
              label: t("assembly.glassThickness"),
              state: bay.glass_thickness_mm ? "DECLARED" : "UNKNOWN",
            },
            {
              label: t("assembly.handleHeight"),
              state: bay.handle_height_mm ? "DECLARED" : "UNKNOWN",
            },
          ]}
        />
      </details>
      {onAskAssistant && (
        <div className="inspector-actions">
          <button type="button" className="ghost-button" disabled={busy} onClick={onAskAssistant}>
            {t("assistant.modifyWith")}
          </button>
        </div>
      )}
    </section>
  );
}

/** §04-D technical provenance: which declared values are catalog-backed
 * (VERIFIED), which are user intent (DECLARED), which are missing
 * (UNKNOWN) and which block the design (BLOCKED). Rendered as a compact
 * strip at the top of every inspector so the states are always obvious. */
type FieldState = "VERIFIED" | "DECLARED" | "UNKNOWN" | "BLOCKED";

function ProvenanceStrip({
  items,
}: {
  items: { label: string; state: FieldState }[];
}): JSX.Element {
  return (
    <ul className="prov-strip" aria-label={t("prov.title")}>
      {items.map((item, index) => (
        <li
          key={`${item.label}-${index}`}
          className={`prov-chip prov-chip--${item.state.toLowerCase()}`}
          title={t(`prov.${item.state.toLowerCase()}` as TranslationKey)}
        >
          <span className="prov-chip__state">
            {t(`prov.${item.state.toLowerCase()}` as TranslationKey)}
          </span>
          {item.label}
        </li>
      ))}
    </ul>
  );
}

/** Mullion/transom inspector — a division is a real object: its offset is
 * editable, its profile is catalog authority, its bays are one click away,
 * and merging it back is an explicit domain op (never index surgery). */
function DivisionInspector({
  module,
  division,
  product,
  busy,
  commit,
  onSelect,
  onAskAssistant,
}: {
  module: ProductModuleJson;
  division: IntentNode;
  product: ProductJson;
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
  onSelect(id: string): void;
  onAskAssistant?(): void;
}): JSX.Element {
  const vertical = division.type === "SPLIT_V";
  const children = division.children ?? [];
  const removable = canRemoveModuleDivision(product, module.id, division.id);
  const bays = intentBays(module.tree);
  const childLabel = (child: IntentNode): string =>
    child.type === "BAY"
      ? `${t("assembly.bay")} ${bays.findIndex((node) => node.id === child.id) + 1}`
      : child.type === "SPLIT_V"
        ? t("assembly.mullionV")
        : child.type === "SPLIT_H"
          ? t("assembly.transomH")
          : child.id;
  return (
    <section className="assembly-inspector" aria-label={t("assembly.division")}>
      <header className="assembly-inspector__header">
        <h4>{vertical ? t("assembly.mullionV") : t("assembly.transomH")}</h4>
      </header>
      <ProvenanceStrip
        items={[
          { label: t("inspector.divisionType"), state: "DECLARED" },
          { label: t("assembly.splitOffset"), state: "DECLARED" },
          {
            label: t("assembly.mullionProfile"),
            state: division.mullion_profile_sku ? "VERIFIED" : "UNKNOWN",
          },
        ]}
      />
      <details className="inspector-section" open>
        <summary>{t("inspector.dimensions")}</summary>
        <DraftField
          label={t("assembly.splitOffset")}
          value={division.split_offset_mm ?? ""}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) =>
            commit([
              { op: "move_divider", module: module.id, divider: division.id, offset_mm: value },
            ])
          }
        />
        <div className="inspector-field">
          <span className="inspector-field__label">{t("assembly.mullionProfile")}</span>
          <code className="inspector-field__value">
            {division.mullion_profile_sku ?? t("prov.unknown")}
          </code>
        </div>
      </details>
      <details className="inspector-section" open>
        <summary>{t("assembly.divisionBays")}</summary>
        <ul className="division-children">
          {children.map((child) => (
            <li key={child.id}>
              <button
                type="button"
                className="link-button"
                onClick={() => onSelect(`${module.id}/${child.id}`)}
              >
                {childLabel(child)}
              </button>
            </li>
          ))}
        </ul>
      </details>
      <div className="inspector-actions">
        <button
          type="button"
          className="ghost-button ghost-button--danger"
          disabled={busy || !removable}
          onClick={() => {
            const kept = children[0]?.id;
            commit([{ op: "remove_divider", module: module.id, divider: division.id }]);
            onSelect(kept ? `${module.id}/${kept}` : module.id);
          }}
        >
          {t("assembly.removeSplit")}
        </button>
        {!removable && <p className="assembly-hint">{t("assembly.removeSplitNested")}</p>}
        {removable && <p className="assembly-hint">{t("assembly.removeSplitKeeps")}</p>}
        {onAskAssistant && (
          <button type="button" className="ghost-button" disabled={busy} onClick={onAskAssistant}>
            {t("assistant.modifyWith")}
          </button>
        )}
      </div>
    </section>
  );
}

/** Overview level: what this element IS, not how to change it. */
function ElementSummary({ title, rows }: { title: string; rows: [string, string][] }): JSX.Element {
  return (
    <section className="assembly-inspector inspector-summary">
      <h4 className="inspector-summary__title">{title}</h4>
      <dl className="inspector-summary__list">
        {rows.map(([label, value]) => (
          <div key={label} className="inspector-summary__row">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** Technical level: the engine's manufacturing output for the selection —
 * the module's cuts/glass/hardware, or just the pieces tagged to one bay. */
function TechnicalPanel({
  evaluation,
  options,
  moduleId,
  bayId,
  moduleIndex,
  members,
  bayNode,
  widthMm,
}: {
  evaluation: EngineAssemblyCalculateResponse | null;
  options?: DesignOptions;
  moduleId?: string;
  bayId?: string | null;
  moduleIndex?: (moduleId: string) => number;
  /** The declared member sections + bay the §05 section view cuts through
   * — same product model as the canvas, never a separate drawing. */
  members?: MemberGeometry;
  bayNode?: IntentNode | null;
  widthMm?: number;
}): JSX.Element {
  const entries = (evaluation?.modules ?? []).filter(
    (entry) => !moduleId || entry.module_id === moduleId,
  );
  const names = new Map([
    ...(options?.profiles ?? []).map((article) => [article.sku, article.name] as const),
    ...(options?.glazing_beads ?? []).map(
      (article) => [article.sku, `Junquillo para ${fmtMm(article.glass_thickness_mm)} mm`] as const,
    ),
    ...(options?.glass_specs ?? []).map(
      (article) =>
        [
          article.sku,
          asGlassProduct(article.product)?.name ??
            article.spec ??
            "Sin dato: falta el nombre del vidrio",
        ] as const,
    ),
    ...(options?.panel_choices ?? []).map((article) => [article.sku, article.name] as const),
    ...(options?.hardware_kits ?? []).map((article) => [article.sku, article.name] as const),
  ]);
  if (entries.length === 0) {
    return (
      <section className="assembly-inspector">
        <p className="assembly-hint">{t("assembly.techPending")}</p>
      </section>
    );
  }
  return (
    <div className="tech-panel">
      <p className="inspector-note">
        Fuente: cálculo del motor con la versión elegida del catálogo.
      </p>
      {members && widthMm !== undefined && widthMm > 0 && (
        <details className="inspector-section" open>
          <summary>{t("assembly.sectionView")}</summary>
          <SectionView bay={bayNode ?? null} members={members} widthMm={widthMm} />
        </details>
      )}
      {entries.map((entry) => {
        const result = entry.result;
        const ordinal = moduleIndex ? moduleIndex(entry.module_id) : 0;
        const heading = `${t("assembly.module")} ${ordinal}`;
        if (!result) {
          return (
            <section key={entry.module_id} className="assembly-inspector">
              <h4 className="inspector-summary__title">{heading}</h4>
              <p className="assembly-hint">{t("assembly.techUnavailable")}</p>
            </section>
          );
        }
        const cuts = result.profile_cuts.filter((cut) => !bayId || cut.bay_id === bayId);
        const glasses = result.glasses.filter((glass) => !bayId || glass.bay_id === bayId);
        const panels = result.panels.filter((panel) => !bayId || panel.bay_id === bayId);
        const fittings = result.fittings.filter((fit) => !bayId || fit.bay_id === bayId);
        const empty =
          cuts.length === 0 && glasses.length === 0 && panels.length === 0 && fittings.length === 0;
        return (
          <section key={entry.module_id} className="assembly-inspector">
            <h4 className="inspector-summary__title">{heading}</h4>
            {empty && <p className="assembly-hint">{t("assembly.techEmpty")}</p>}
            {cuts.length > 0 && (
              <details className="inspector-section" open>
                <summary>{t("assembly.techCuts")}</summary>
                <table className="tech-table">
                  <thead>
                    <tr>
                      <th>Perfil</th>
                      <th>{t("assembly.techLength")}</th>
                      <th>{t("assembly.techQty")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cuts.map((cut, index) => (
                      <tr key={`${cut.sku}-${index}`}>
                        <td title={cut.sku}>
                          {names.get(cut.sku) ?? "Sin dato: falta el nombre del perfil"}
                        </td>
                        <td>{fmtMm(cut.length_mm)}</td>
                        <td>{cut.qty}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            )}
            {glasses.length > 0 && (
              <details className="inspector-section" open>
                <summary>{t("assembly.techGlasses")}</summary>
                <table className="tech-table">
                  <thead>
                    <tr>
                      <th>{t("assembly.glass")}</th>
                      <th>{t("projects.dims")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {glasses.map((glass, index) => (
                      <tr key={`${glass.bay_id}-${index}`}>
                        <td title={glass.article_sku ?? undefined}>
                          {names.get(glass.article_sku ?? "") ??
                            "Sin dato: falta el nombre del vidrio"}
                        </td>
                        <td>
                          {fmtMm(glass.width_mm)} × {fmtMm(glass.height_mm)} mm
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            )}
            {panels.length > 0 && (
              <details className="inspector-section" open>
                <summary>{t("assembly.techPanels")}</summary>
                <table className="tech-table">
                  <thead>
                    <tr>
                      <th>{t("assembly.panel")}</th>
                      <th>{t("projects.dims")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {panels.map((panel, index) => (
                      <tr key={`${panel.bay_id}-${index}`}>
                        <td title={panel.sku}>
                          {names.get(panel.sku) ?? "Sin dato: falta el nombre del panel"}
                        </td>
                        <td>
                          {fmtMm(panel.width_mm)} × {fmtMm(panel.height_mm)} mm
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            )}
            {fittings.length > 0 && (
              <details className="inspector-section" open>
                <summary>{t("assembly.techFittings")}</summary>
                <table className="tech-table">
                  <thead>
                    <tr>
                      <th>Herraje</th>
                      <th>{t("assembly.techQty")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fittings.map((fit, index) => (
                      <tr key={`${fit.sku}-${index}`}>
                        <td title={fit.sku}>{names.get(fit.sku) ?? domainLabel(fit.kind)}</td>
                        <td>{fit.qty}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            )}
          </section>
        );
      })}
    </div>
  );
}

function ModuleInspector({
  options,
  organizationId,
  color,
  evaluation,
  module,
  product,
  members,
  glassSpecs,
  panelSkus,
  panelChoices,
  couplerSkus,
  busy,
  commit,
  onOpeningPreview,
  onAskAssistant,
  onMountingChanged,
}: {
  options?: DesignOptions;
  organizationId: string;
  color: string;
  evaluation: EngineAssemblyCalculateResponse | null;
  module: ProductJson["assembly"]["modules"][number];
  product: ProductJson;
  members: MemberGeometry;
  glassSpecs: GlassSpecChoice[];
  panelSkus: string[];
  panelChoices: PanelChoice[];
  mullionSkus: Partial<Record<SplitType, string>>;
  couplerSkus: string[];
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
  onOpeningPreview(next: ProductJson | null): void;
  onAskAssistant?(): void;
  onMountingChanged(): void;
}): JSX.Element {
  const opening = moduleOpening(module);
  const isDoor = opening === "DOOR_ENTRY" && !modulePrimaryBay(module)?.opening;
  const slidingBay = isSlidingOpening(opening) ? modulePrimaryBay(module) : null;
  const slidingLayout = slidingBay ? resolvedSlidingLayout(slidingBay) : null;
  const ordinal = product.assembly.modules.findIndex((item) => item.id === module.id) + 1;
  const commitSlidingLayout = (layout: SlidingLayout) => {
    if (slidingBay) {
      commit([slidingOperation(module.id, slidingBay.id, layout)]);
    }
  };
  return (
    <section className="assembly-inspector" aria-label={t("assembly.module")}>
      <header className="assembly-inspector__header">
        <h4>
          {t("assembly.module")} {ordinal}
        </h4>
        {product.assembly.modules.length > 1 && (
          <button
            type="button"
            className="ghost-button is-danger"
            disabled={busy || product.assembly.modules.length <= 1}
            title={t("assembly.removeUnit")}
            aria-label={t("assembly.removeUnit")}
            onClick={() => commit([{ op: "remove_unit", module: module.id }])}
          >
            ×
          </button>
        )}
      </header>
      <details className="inspector-section" open>
        <summary>{t("inspector.dimensions")}</summary>
        <DraftField
          label={t("assembly.width")}
          value={module.width_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) =>
            commit([{ op: "set_module_width", module: module.id, width_mm: value }])
          }
        />
        <DraftField
          label={
            module.contour?.bulges.some(Boolean) ? "Alto hasta arranque" : t("assembly.height")
          }
          value={module.height_mm}
          unit="mm"
          disabled={busy}
          normalize={normalizeMm}
          onCommit={(value) => commit([{ op: "set_height", height_mm: value }])}
        />
      </details>
      <details className="inspector-section" open>
        <summary>{t("assembly.opening")}</summary>
        {options?.opening_capabilities?.length && modulePrimaryBay(module) ? (
          <OpeningPalette
            compact
            options={options}
            bay={modulePrimaryBay(module)!}
            disabled={busy}
            onPick={(patch) =>
              commit(bayOperations(module.id, modulePrimaryBay(module)!.id, patch))
            }
            onPreview={(patch) =>
              onOpeningPreview(
                patch
                  ? setModuleTree(
                      product,
                      module.id,
                      updateBay(module.tree, modulePrimaryBay(module)!.id, patch),
                    )
                  : null,
              )
            }
          />
        ) : (
          <>
            {" "}
            <div className="opening-grid" role="group" aria-label={t("assembly.opening")}>
              {OPENING_OPTIONS.filter(
                ([value]) => !options?.system_family || options.compatible_openings.includes(value),
              ).map(([value, labelKey]) => (
                <button
                  key={value}
                  type="button"
                  className={`opening-choice${opening === value ? " is-active" : ""}`}
                  title={t(labelKey)}
                  aria-label={t(labelKey)}
                  aria-pressed={opening === value}
                  disabled={busy}
                  onClick={() => commit([{ op: "set_opening", module: module.id, opening: value }])}
                >
                  <svg viewBox="0 0 100 100" aria-hidden="true">
                    <rect className="opening-choice__frame" x={4} y={4} width={92} height={92} />
                    <OpeningGlyph opening={value} x={4} y={4} w={92} h={92} />
                  </svg>
                </button>
              ))}
            </div>
          </>
        )}
      </details>
      {slidingLayout && slidingBay && (
        <SlidingPanelsEditor
          instanceId={slidingBay.id}
          layout={slidingLayout}
          busy={busy}
          onChange={commitSlidingLayout}
        />
      )}
      <details className="inspector-section" open>
        <summary>{t("inspector.glazing")}</summary>
        <GlassSelector
          compact
          options={options}
          choices={glassSpecs}
          node={modulePrimaryBay(module)!}
          context={glassContext(modulePrimaryBay(module)!, module.id, evaluation)}
          busy={busy}
          onPatch={(patch) =>
            commit(
              intentBays(module.tree).flatMap((bay) => bayOperations(module.id, bay.id, patch)),
            )
          }
        />
        {isDoor && (
          <label className="assembly-field">
            <span>{t("assembly.panel")}</span>
            <select
              aria-label={t("assembly.panel")}
              disabled={busy}
              value={modulePanelSku(module) ?? ""}
              onChange={(event) =>
                commit([{ op: "set_panel", module: module.id, sku: event.target.value || null }])
              }
            >
              <option value="">{t("assembly.noPanel")}</option>
              {panelSkus.map((sku) => (
                <option key={sku} value={sku}>
                  {panelLabel(sku, panelChoices)}
                </option>
              ))}
            </select>
          </label>
        )}
      </details>
      <LeafFacts
        module={module}
        bay={modulePrimaryBay(module)!}
        evaluation={evaluation}
        options={options}
        busy={busy}
        onHandleHeight={(value) =>
          commit(
            bayOperations(module.id, modulePrimaryBay(module)!.id, { handle_height_mm: value }),
          )
        }
      />
      {moduleOpening(module) !== "FIXED" && (
        <details className="inspector-section">
          <summary>Avanzado · herrajes y manilla</summary>
          <HardwarePanel
            options={options}
            module={module}
            bay={modulePrimaryBay(module)!}
            organizationId={organizationId}
            color={color}
            busy={busy}
            onPatch={(patch) =>
              commit(bayOperations(module.id, modulePrimaryBay(module)!.id, patch))
            }
            onTree={(tree) => commit([{ op: "set_module_tree", module: module.id, tree }])}
          />
        </details>
      )}
      <details className="inspector-section editor-advanced">
        <summary>Avanzado · montaje, extras y perfiles</summary>
        <CatalogLimitNotice options={options} opening={opening} />
        <MountingInspector
          module={module}
          product={product}
          busy={busy}
          onChanged={onMountingChanged}
        />
        <ProvenanceStrip
          items={[
            { label: t("inspector.dimensions"), state: "DECLARED" },
            {
              label: t("assembly.glass"),
              state: moduleGlassSku(module) !== null ? "VERIFIED" : "UNKNOWN",
            },
            {
              label: t("assembly.coupler"),
              state: couplerSkus.length > 0 ? "VERIFIED" : "UNKNOWN",
            },
          ]}
        />
        {!module.frameless && (
          <details className="inspector-section">
            <summary>{t("assembly.sectionTitle")}</summary>
            <div className="section-preview-list">
              <div>
                <p className="inspector-note">{members.frame.sku ?? t("assembly.frame")}</p>
                <SectionPreviewSvg
                  section={members.frame.section}
                  faceWidthMm={members.frame.faceWidthMm}
                  material={members.frame.material}
                />
              </div>
              <div>
                <p className="inspector-note">{members.sash.sku ?? t("assembly.sash")}</p>
                <SectionPreviewSvg
                  section={members.sash.section}
                  faceWidthMm={members.sash.faceWidthMm}
                  material={members.sash.material}
                />
              </div>
            </div>
          </details>
        )}
        {module.contour && <ContourShapeSection module={module} busy={busy} commit={commit} />}
        <FramelessSection module={module} couplerSkus={couplerSkus} busy={busy} commit={commit} />
        <ExtrasInspector
          options={options}
          module={module}
          evaluation={evaluation}
          busy={busy}
          commit={commit}
        />
      </details>
      {onAskAssistant && (
        <div className="inspector-actions">
          <button type="button" className="ghost-button" disabled={busy} onClick={onAskAssistant}>
            {t("assistant.modifyWith")}
          </button>
        </div>
      )}
    </section>
  );
}

function CouplingInspector({
  coupling,
  ordinal,
  couplerSkus,
  busy,
  commit,
  onAskAssistant,
}: {
  coupling: CouplingJson;
  ordinal: number;
  couplerSkus: string[];
  busy: boolean;
  commit(ops: DesignOperationRequest[]): void;
  onAskAssistant?(): void;
}): JSX.Element {
  return (
    <section className="assembly-inspector" aria-label={t("assembly.coupling")}>
      <header className="assembly-inspector__header">
        <h4>
          {t("assembly.coupling")} {ordinal}
        </h4>
      </header>
      <ProvenanceStrip
        items={[
          { label: t("assembly.angle"), state: "DECLARED" },
          { label: t("inspector.couplingType"), state: "DECLARED" },
          {
            label: t("assembly.coupler"),
            state: coupling.coupler_profile_sku ? "VERIFIED" : "UNKNOWN",
          },
        ]}
      />
      <DraftField
        label={t("assembly.angle")}
        value={coupling.angle_deg}
        unit="°"
        disabled={busy}
        normalize={normalizeAngle}
        rejectHint={t("assembly.fieldAngleRange")}
        onCommit={(value) =>
          commit([{ op: "set_coupling_angle", coupling: coupling.id, angle_deg: value }])
        }
      />
      <label className="assembly-field">
        <span>{t("assembly.coupler")}</span>
        <select
          aria-label={t("assembly.coupler")}
          disabled={busy}
          value={coupling.coupler_profile_sku ?? ""}
          onChange={(event) =>
            commit([
              { op: "set_coupler_sku", coupling: coupling.id, sku: event.target.value || null },
            ])
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
          title={
            Number(coupling.angle_deg) === 0
              ? t("assembly.straightenDisabled")
              : t("assembly.straightenHint")
          }
          onClick={() =>
            commit([{ op: "set_coupling_angle", coupling: coupling.id, angle_deg: "0" }])
          }
        >
          {t("assembly.straighten")}
        </button>
        {onAskAssistant && (
          <button type="button" className="ghost-button" disabled={busy} onClick={onAskAssistant}>
            {t("assistant.modifyWith")}
          </button>
        )}
      </div>
    </section>
  );
}

function ToolIcon({ name }: { name: string }): JSX.Element {
  const strokes: Record<string, JSX.Element> = {
    select: <path d="M4 2l10 5.5-4.2 1.2L12 13l-2 1.4-2.2-4.3-3.8 2.9z" />,
    split_v: <path d="M3 3h10v10H3z M8 3v10" />,
    split_h: <path d="M3 3h10v10H3z M3 8h10" />,
    couple_left: <path d="M6 3h7v10H6z M5.5 8H1 M2.5 5.5L1 8l1.5 2.5" />,
    couple_right: <path d="M3 3h7v10H3z M10.5 8H15 M13.5 5.5L15 8l-1.5 2.5" />,
    equalize: <path d="M3 5h10 M8 2.5L10.5 5 8 7.5 M3 11h10 M8 8.5L10.5 11 8 13.5" />,
    opening: <path d="M3 3h10v10H3z M3 3l10 5-10 5" />,
    glass: <path d="M3 3h10v10H3z M5 4l-1 2 M12 10l-2 2" />,
    measure: <path d="M2 4v9h12 M4 8v2 M7 8v2 M10 8v2" />,
    library: <path d="M3 2v12 M6 2v12 M9 2l4 11" />,
    inspector: <path d="M2 3h12 M2 8h12 M2 13h12 M6 2v2 M10 7v2 M6 12v2" />,
    help: <path d="M5 5a3 3 0 1 1 4 3c-1 .5-1 1-1 2 M8 12v1" />,
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
  positionId,
  positionPanel,
  contentEpoch = 0,
  optionsReady = options !== undefined,
  quantity = 1,
  libraryOpen = false,
  onLibraryToggle,
  library,
  issuesOpen = false,
  onCloseIssues,
  onOpenIssues,
  saveBlockReason,
  onChooseSystem,
}: {
  organizationId: string;
  couplerSkus: string[];
  glassSkus: string[];
  panelSkus: string[];
  options: DesignOptions | undefined;
  disabled: boolean;
  onChanged(): void;
  onEvaluationChange(
    evaluation: EngineAssemblyCalculateResponse | null,
    state?: { pending: boolean; error: string | null },
  ): void;
  positionId: string | null;
  positionPanel?: JSX.Element;
  quantity?: number;
  libraryOpen?: boolean;
  onLibraryToggle?(): void;
  library?: JSX.Element;
  issuesOpen?: boolean;
  onCloseIssues?(): void;
  onOpenIssues?(): void;
  saveBlockReason?: string | null;
  onChooseSystem?(): void;
  /** Bumped when the product is replaced wholesale (starter pick) so the
   * canvas viewport re-fits even after the user took manual pan/zoom control. */
  contentEpoch?: number;
  /** The system's design options have hydrated (or errored) — paid AI
   * generation must not start on an empty catalog signature. Defaults to
   * the options value's presence for callers without a loading state. */
  optionsReady?: boolean;
}): JSX.Element | null {
  const inputs = useCanvasStore((state) => state.inputs);
  const commitInputs = useCanvasStore((state) => state.commitInputs);
  const selection = useCanvasStore((state) => state.selection);
  const select = useCanvasStore((state) => state.select);
  const undoHistory = useCanvasStore((state) => state.undo);
  const redoHistory = useCanvasStore((state) => state.redo);
  const canUndo = useCanvasStore((state) => state.past.length > 0);
  const canRedo = useCanvasStore((state) => state.future.length > 0);
  const specClipboard = useCanvasStore((state) => state.specClipboard);
  const lastMutation = useCanvasStore((state) => state.lastMutation);
  const product = inputs.product;
  const [openingPreviewProduct, setOpeningPreviewProduct] = useState<ProductJson | null>(null);
  const previewInputs = { ...inputs, product: openingPreviewProduct };
  const openingPreview = useAssemblyCalculation(organizationId, previewInputs, false);
  const previewReady =
    openingPreviewProduct !== null && openingPreview.evaluation?.status === "VALID";
  const { evaluation, currentEvaluation, isPending, errorCode, retry } = useAssemblyCalculation(
    organizationId,
    inputs,
  );
  const drawingEvaluation = previewReady ? openingPreview.evaluation : evaluation;
  const issues = evaluation?.issues ?? [];
  const glassChecks = useGlassChecks(organizationId, product, options, evaluation);
  const [viewFace, setViewFace] = useState<"interior" | "exterior">("interior");
  const members = useMemo(
    () => resolveMembers(options, inputs.color, viewFace),
    [options, inputs.color, viewFace],
  );
  const [tool, setTool] = useState<EditorTool>("select");
  const [treeOpen, setTreeOpen] = useState(false);
  const narrow = useEditorMedia("(max-width: 1279px)");
  const readOnly = useEditorMedia("(max-width: 1023px)");
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const inspectorRef = useRef<HTMLDivElement>(null);
  const [proposal, setProposal] = useState<{
    simulation: Simulation;
    snapshot: typeof inputs;
    quantity: number;
  } | null>(null);
  const liveQuantity = useRef(quantity);
  liveQuantity.current = quantity;
  useFloatingLayer(treeOpen, () => setTreeOpen(false));
  useEffect(() => {
    if (narrow && (treeOpen || helpOpen || libraryOpen || issuesOpen)) setInspectorOpen(false);
  }, [narrow, treeOpen, helpOpen, libraryOpen, issuesOpen]);
  useEffect(() => {
    if (!narrow || !inspectorOpen) return;
    const dismiss = (event: PointerEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      if (!target.closest(".assembly-side, .assembly-tools, .ui-popover")) setInspectorOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [narrow, inspectorOpen]);
  useEffect(() => {
    setProposal(null);
  }, [inputs, quantity]);
  /** Right-rail detail level — overview/design/technical over the same
   * selection; complexity stays hidden until the user asks for it. */
  const [detail, setDetail] = useState<DetailLevel>("design");
  const [planOpen, setPlanOpen] = useState(true);
  const [view3dOpen, setView3dOpen] = useState(false);
  const [operationBusy, setOperationBusy] = useState(false);
  const [operationMessage, setOperationMessage] = useState("");
  /** Queued prompt for the assistant — "" means focus only. Every "…with
   * DEKOPEN" affordance funnels here; the human always confirms. */
  const [assistantDraft, setAssistantDraft] = useState<{
    text: string;
    submit?: boolean;
  } | null>(null);

  const issuesListRef = useRef<HTMLUListElement>(null);
  /** Canvas context menu — cursor position, closed on action/outside/Escape. */
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  useFloatingLayer(contextMenu !== null, () => setContextMenu(null));
  const contextMenuRef = useRef<HTMLDivElement | null>(null);
  /** Measured on-screen position — null until the first layout pass, so the
   * menu can flip away from viewport edges instead of overflowing them. */
  const [contextMenuPos, setContextMenuPos] = useState<{ left: number; top: number } | null>(null);

  useLayoutEffect(() => {
    if (!contextMenu) {
      setContextMenuPos(null);
      return;
    }
    const menu = contextMenuRef.current;
    if (!menu) return;
    const rect = menu.getBoundingClientRect();
    setContextMenuPos({
      left: Math.max(0, Math.min(contextMenu.x, window.innerWidth - rect.width)),
      top: Math.max(0, Math.min(contextMenu.y, window.innerHeight - rect.height)),
    });
    menu.querySelector<HTMLElement>('[role="menuitem"]')?.focus();
  }, [contextMenu]);

  useEffect(() => {
    // Only the current request can authorize a save. Undo can restore the same
    // cached result while a previous request is pending: publish it again for
    // that input identity instead of leaving the parent's result cleared.
    onEvaluationChange(operationBusy ? null : currentEvaluation, {
      pending: isPending || operationBusy,
      error: errorCode,
    });
  }, [currentEvaluation, inputs, operationBusy, isPending, errorCode, onEvaluationChange]);

  /** Every "…with DEKOPEN" affordance: scroll the assistant into view and
   * hand it a prompt draft — "" focuses the field untouched. */
  function askAssistant(prompt: string, submit = false): void {
    setAssistantOpen(true);
    setInspectorOpen(true);
    setAssistantDraft({ text: prompt, submit });
  }

  useEffect(() => {
    if (!contextMenu) return;
    function dismiss(): void {
      setContextMenu(null);
    }
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") dismiss();
    }
    window.addEventListener("mousedown", dismiss);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("mousedown", dismiss);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [contextMenu]);

  function commit(next: ProductJson): void {
    if (next === product || disabled || readOnly) return;
    // Any product edit ends modal tool state — an armed divide must not
    // survive an unrelated edit and surprise the next module click.
    setTool("select");
    commitInputs({ ...useCanvasStore.getState().inputs, product: next });
    onChanged();
  }

  const bridgeProduct = useMemo(
    () =>
      product
        ? {
            ...product,
            design_context: {
              system_id: inputs.systemId,
              color: inputs.color,
            },
          }
        : null,
    [product, inputs.systemId, inputs.color],
  );

  function applyRegisteredOps(ops: DesignOperation[]): void {
    if (!product || disabled || readOnly) return;
    const next = applyOperationEffects(product, ops);
    const attributes = ops.reduce<Record<string, string>>(
      (current, op) => ({
        ...current,
        ...(op.context_effect && typeof op.context_effect === "object"
          ? (op.context_effect as Record<string, string>)
          : {}),
      }),
      {},
    );
    setTool("select");
    commitInputs({
      ...useCanvasStore.getState().inputs,
      product: next,
      ...(attributes.system_id ? { systemId: attributes.system_id } : {}),
      ...(attributes.color ? { color: attributes.color } : {}),
    });
    onChanged();
  }

  function simulateCommand(
    ops: DesignOperationRequest[],
    spec?: CommandSpec,
    args: CommandArgs = {},
  ): void {
    const snapshot = useCanvasStore.getState().inputs;
    if (!snapshot.product || !snapshot.systemId || disabled || readOnly || operationBusy) return;
    setOperationBusy(true);
    setOperationMessage("");
    void designOperationsSimulate(
      {
        product: snapshot.product,
        system_id: snapshot.systemId,
        color: snapshot.color,
        ops,
        quantity,
      },
      { headers: { "X-Organization-ID": organizationId } },
    )
      .then((response) => {
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        if (useCanvasStore.getState().inputs !== snapshot) throw Error("stale");
        if (!response.data.valid) throw Error("invalid");
        applyRegisteredOps(response.data.ops.map((op) => ({ ...op })));
        if (spec) {
          useCanvasStore.getState().recordMutation(spec.id, args);
          spec.postCommit?.(
            commandCtx!,
            snapshot.product!,
            response.data.product as ProductJson,
            args,
          );
        }
      })
      .catch((error: unknown) => {
        const detail =
          error instanceof ApiError && error.payload && typeof error.payload === "object"
            ? (error.payload as { error?: { detail?: string } }).error?.detail
            : null;
        setOperationMessage(
          detail ||
            "No se aplicó el cambio. Revisa la geometría y vuelve a intentar con el diseño actual.",
        );
      })
      .finally(() => setOperationBusy(false));
  }

  function proposeCommand(ops: DesignOperationRequest[]): void {
    const snapshot = useCanvasStore.getState().inputs;
    const snapshotQuantity = quantity;
    if (!snapshot.product || !snapshot.systemId || disabled || readOnly || operationBusy) return;
    setProposal(null);
    setOperationBusy(true);
    setOperationMessage("");
    void designOperationsSimulate(
      {
        product: snapshot.product,
        system_id: snapshot.systemId,
        color: snapshot.color,
        ops,
        quantity,
      },
      { headers: { "X-Organization-ID": organizationId } },
    )
      .then((response) => {
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        if (
          useCanvasStore.getState().inputs !== snapshot ||
          liveQuantity.current !== snapshotQuantity
        )
          return;
        setProposal({ simulation: response.data, snapshot, quantity: snapshotQuantity });
      })
      .catch(() =>
        setOperationMessage(
          "No se pudo simular la propuesta. Revisa la serie y los datos del diseño y vuelve a ejecutar el comando.",
        ),
      )
      .finally(() => setOperationBusy(false));
  }

  function showInspector(field?: string): void {
    dismissFloatingLayers();
    setInspectorOpen(true);
    setDetail("design");
    const current = useCanvasStore.getState();
    if (!current.selection) current.select(current.inputs.product?.assembly.modules[0]?.id ?? null);
    requestAnimationFrame(() => {
      const target =
        field === "opening"
          ? inspectorRef.current?.querySelector<HTMLButtonElement>(".editor-opening-trigger")
          : field === "glass"
            ? inspectorRef.current?.querySelector<HTMLSelectElement>('select[aria-label="Vidrio"]')
            : inspectorRef.current?.querySelector<HTMLElement>("input, button");
      target?.focus();
      if (field === "opening") target?.click();
    });
  }

  // Editor-only gestures never run while a text field is being edited.
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (
        event.target instanceof Element &&
        event.target.closest("input, textarea, select, [contenteditable='true'], [role='dialog']")
      )
        return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.key === "?") {
        event.preventDefault();
        setHelpOpen((open) => !open);
      }
      if (event.key === "Escape") {
        setInspectorOpen(false);
        setHelpOpen(false);
        setTreeOpen(false);
        setProposal(null);
      }
      if (disabled || readOnly || operationBusy || !event.key.startsWith("Arrow")) return;
      const current = useCanvasStore.getState();
      const [moduleId, nodeId] = current.selection?.split("/") ?? [];
      const module = current.inputs.product?.assembly.modules.find((item) => item.id === moduleId);
      const division = module && nodeId ? findNode(module.tree, nodeId) : null;
      if (!division?.split_offset_mm) return;
      const horizontal = division.type === "SPLIT_H";
      if (
        horizontal
          ? !["ArrowUp", "ArrowDown"].includes(event.key)
          : !["ArrowLeft", "ArrowRight"].includes(event.key)
      )
        return;
      event.preventDefault();
      // Exact adjustment of declared intent, no geometry is derived here.
      event.stopPropagation();
      const step =
        (event.shiftKey ? 10 : 1) * (["ArrowUp", "ArrowLeft"].includes(event.key) ? -1 : 1);
      const offset = dividerNudge(division.split_offset_mm, step);
      if (offset === null) return;
      simulateCommand([
        { op: "move_divider", module: moduleId!, divider: nodeId!, offset_mm: offset },
      ]);
    };
    window.addEventListener("keydown", key, true);
    return () => window.removeEventListener("keydown", key, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- gestures dispatch against the live store
  }, [disabled, readOnly, operationBusy]);

  // The agent dock's ops bridge: publishes the live product plus an apply
  // channel that commits through the same registry path as a human click.
  // The hook forwards calls to the latest closure, so capturing `product` and
  // `commit` always lands on the current product — and the published product
  // re-registers on every commit so a stale-product apply is refused.
  useRegisterDesignOpsBridge(
    product && !disabled && !readOnly
      ? (bridgeProduct as unknown as { [key: string]: unknown })
      : null,
    product && !disabled && !readOnly
      ? (ops: DesignOperation[]) => {
          applyRegisteredOps(ops);
        }
      : null,
  );

  // Hooks before the empty branch — a starter pick flips product
  // null→object on the SAME mounted instance, so any early return placed
  // ahead of a hook crashes with "Rendered more hooks".
  const busy = disabled || readOnly || operationBusy;
  const mullionSkus: Partial<Record<SplitType, string>> = useMemo(
    () => ({
      SPLIT_V: options?.profiles.find((profile) => profile.role === "MULLION_V")?.sku,
      SPLIT_H: options?.profiles.find((profile) => profile.role === "MULLION_H")?.sku,
    }),
    [options],
  );

  // One layout pass per product commit — bounds/selection boxes derive from
  // the memo instead of recomputing the elevation four times per render.
  const front = useMemo(() => (product ? frontLayout(product) : null), [product]);
  const frontBox = useMemo(() => {
    if (!front) return null;
    const box = frontBounds(
      front,
      Object.fromEntries(
        (drawingEvaluation?.modules ?? []).map((item) => [item.module_id, item.drawing ?? null]),
      ),
      detail === "technical",
      Object.fromEntries(
        (drawingEvaluation?.modules ?? []).map((item) => [
          item.module_id,
          (item.result?.opening_leaves ?? []) as unknown as OpeningLeafFact[],
        ]),
      ),
    );
    return inputs.mounting?.length
      ? { ...box, y: box.y - 180, h: box.h + 180, x: box.x - 60, w: box.w + 120 }
      : box;
  }, [front, inputs.mounting, drawingEvaluation, detail]);
  const selectionBox = useMemo(
    () => (front ? frontModuleBox(front, selection) : null),
    [front, selection],
  );

  // The shared command registry: palette, keyboard and AI all dispatch the
  // same typed commands; `commit` inside is the single undoable transaction.
  const commandCtx = useMemo<CommandContext | null>(() => {
    if (!product) return null;
    return {
      product,
      selection,
      catalog: {
        openingChoices: openingChoices(options),
        compatibleOpenings: options?.compatible_openings,
        glassThicknesses: options?.glazing_thicknesses ?? [],
        glassSkus,
        glassSpecs: options?.glass_specs,
        couplerSkus,
        panelSkus,
        mullionSkus,
      },
      disabled: busy,
      commit,
      simulate: simulateCommand,
      propose: proposeCommand,
      select,
      setTool,
      focusAssistant: () => askAssistant(""),
      undo: () => {
        if (useCanvasStore.getState().past.length === 0) return;
        undoHistory();
        onChanged();
      },
      redo: () => {
        if (useCanvasStore.getState().future.length === 0) return;
        redoHistory();
        onChanged();
      },
      canUndo,
      canRedo,
      specClipboard,
      writeSpecClipboard: useCanvasStore.getState().setSpecClipboard,
      lastMutation,
      recordMutation: useCanvasStore.getState().recordMutation,
    };
    // `commit` is re-declared per render and always sees current inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    product,
    selection,
    options,
    glassSkus,
    couplerSkus,
    panelSkus,
    mullionSkus,
    busy,
    select,
    undoHistory,
    redoHistory,
    canUndo,
    canRedo,
    specClipboard,
    lastMutation,
    quantity,
  ]);
  const surface = useMemo(
    () =>
      commandCtx ? { commands: resolveCommands(commandCtx, assemblyCommands(commandCtx)) } : null,
    [commandCtx],
  );
  // Every chord the surface advertises (menus, palette) is reserved while the
  // editor is mounted — a filtered-out command's shortcut must not leak to
  // the browser (Ctrl+D opened the bookmark dialog).
  const reservedShortcuts = useMemo(() => {
    if (!commandCtx) return [];
    const specs = assemblyCommands(commandCtx);
    return specs.flatMap((spec) => {
      const s = spec.shortcut;
      return s === undefined ? [] : Array.isArray(s) ? [...s] : [s];
    });
  }, [commandCtx]);
  useRegisterCommands(surface);
  useCommandShortcuts(surface, reservedShortcuts);
  const objectTree = useMemo(
    () => (product ? buildObjectTree(product, members, issues, t, options) : null),
    [product, members, issues, options],
  );

  if (!product || !front || !frontBox || !commandCtx || !surface || !objectTree) {
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

  const modules = product.assembly.modules;
  const couplings = product.assembly.couplings;
  const selectedModule =
    modules.find((module) => module.id === selection) ??
    (selection === null ? modules[0] : undefined);
  const selectedCoupling = couplings.find((coupling) => coupling.id === selection);
  // Leaf granularity: canvas bay clicks and tree leaf rows select the
  // composite "moduleId/bayId" — resolved back into (module, bay node) here.
  const treeSelection = selection?.includes("/") ? selection.split("/") : null;
  const selectedTreeModule = treeSelection
    ? modules.find((module) => module.id === treeSelection[0])
    : undefined;
  const selectedNode = (() => {
    if (!treeSelection || !selectedTreeModule || treeSelection[1] === undefined) return null;
    return findNode(selectedTreeModule.tree, treeSelection[1]);
  })();
  const selectedBayModule = selectedNode?.type === "BAY" ? selectedTreeModule : undefined;
  const selectedBayNode = selectedNode?.type === "BAY" ? selectedNode : null;
  const selectedDivisionModule =
    selectedNode && (selectedNode.type === "SPLIT_V" || selectedNode.type === "SPLIT_H")
      ? selectedTreeModule
      : undefined;
  const selectedDivisionNode = selectedDivisionModule ? selectedNode : null;
  // isPending also holds while the query is disabled (no system/product yet).
  // Evaluation is non-blocking: an in-flight recalc keeps the canvas live —
  // react-query keys on the product so stale results never land on newer
  // state, and save still requires the fresh engine verdict upstream.
  const evaluating = isPending && inputs.systemId !== null;
  const planBox = couplings.length > 0 && evaluation?.plan ? planBounds(evaluation.plan) : null;
  const statusText = drawingEvaluation?.elevation
    ? `${fmtMm(drawingEvaluation.elevation.width_mm)} × ${fmtMm(drawingEvaluation.elevation.height_mm)} mm`
    : `${fmtMm(front.totalW)} × ${fmtMm(front.height)} mm${front.lift > 0 ? " hasta arranque" : ""}`;
  // Labels derive from actual product membership — selection ids are
  // arbitrary strings, so a coupling legitimately named "coupling-x" must
  // still resolve (prefix sniffing would hide it).
  const bayOrdinal =
    selectedBayModule && selectedBayNode
      ? intentBays(selectedBayModule.tree).findIndex((node) => node.id === selectedBayNode.id) + 1
      : 0;
  const selectedLabel = selectedModule
    ? `${t("assembly.module")} ${modules.findIndex((item) => item.id === selectedModule.id) + 1}`
    : selectedBayModule && selectedBayNode
      ? `${t("assembly.bay")} ${bayOrdinal} · ${t("assembly.module")} ${modules.findIndex((item) => item.id === selectedBayModule.id) + 1}`
      : selectedDivisionModule && selectedDivisionNode
        ? `${selectedDivisionNode.type === "SPLIT_V" ? t("assembly.mullionV") : t("assembly.transomH")} · ${t("assembly.module")} ${modules.findIndex((item) => item.id === selectedDivisionModule.id) + 1}`
        : selectedCoupling
          ? `${t("assembly.coupling")} ${couplings.findIndex((item) => item.id === selection) + 1}`
          : null;

  const divideToolType = tool === "split_v" ? "SPLIT_V" : tool === "split_h" ? "SPLIT_H" : null;

  // Divide tool: a canvas click splits the module at the cursor offset
  // (direct manipulation), a tree click splits it at the center.
  function pickModule(id: string): void {
    const sku =
      divideToolType === "SPLIT_V"
        ? mullionSkus.SPLIT_V
        : divideToolType === "SPLIT_H"
          ? mullionSkus.SPLIT_H
          : undefined;
    if (divideToolType !== null && sku !== undefined) {
      simulateCommand([
        {
          op: "split_bay",
          module: id,
          bay: "b1",
          axis: divideToolType === "SPLIT_V" ? "V" : "H",
          from: "CENTER",
        },
      ]);
      setTool("select");
    }
    select(id);
  }

  function divideModule(id: string, bayId: string | null, offsetMm?: string): void {
    const sku =
      divideToolType === "SPLIT_V"
        ? mullionSkus.SPLIT_V
        : divideToolType === "SPLIT_H"
          ? mullionSkus.SPLIT_H
          : undefined;
    if (divideToolType === null || sku === undefined) {
      select(id);
      return;
    }
    simulateCommand([
      {
        op: "split_bay",
        module: id,
        bay: bayId ?? "b1",
        axis: divideToolType === "SPLIT_V" ? "V" : "H",
        from: offsetMm === undefined ? "CENTER" : "START",
        ...(offsetMm === undefined ? {} : { offset_mm: offsetMm }),
      },
    ]);
    setTool("select");
    select(id);
  }

  function coupleUnit(side: "left" | "right"): void {
    simulateCommand([{ op: "add_unit", side }]);
  }

  const splitReady = { SPLIT_V: mullionSkus.SPLIT_V, SPLIT_H: mullionSkus.SPLIT_H };
  return (
    <div
      className={`assembly-editor${treeOpen ? "" : " assembly-editor--tree-closed"}`}
      aria-label={t("assembly.frontView")}
    >
      {operationBusy && (
        <output className="editor-operation-message" role="status">
          Calculando el cambio con el motor…
        </output>
      )}
      {operationMessage && (
        <output className="editor-operation-message" role="alert">
          {operationMessage}
        </output>
      )}
      <div className="assembly-tools" role="toolbar" aria-label={t("assembly.tools")}>
        {[
          {
            name: "select",
            label: "Seleccionar",
            key: "V",
            action: () => setTool("select"),
            active: tool === "select",
          },
          {
            name: "split_v",
            label: "Dividir vertical",
            key: "|",
            action: () => setTool(tool === "split_v" ? "select" : "split_v"),
            active: tool === "split_v",
            unavailable: busy || splitReady.SPLIT_V === undefined,
          },
          {
            name: "split_h",
            label: "Dividir horizontal",
            key: "–",
            action: () => setTool(tool === "split_h" ? "select" : "split_h"),
            active: tool === "split_h",
            unavailable: busy || splitReady.SPLIT_H === undefined,
          },
          {
            name: "opening",
            label: "Apertura",
            key: "",
            action: () => showInspector("opening"),
            unavailable: busy,
          },
          {
            name: "glass",
            label: "Vidrio",
            key: "",
            action: () => showInspector("glass"),
            unavailable: busy,
          },
          {
            name: "couple_right",
            label: "Acoplar",
            key: "",
            action: () => coupleUnit("right"),
            unavailable: busy || couplerSkus.length === 0,
          },
          {
            name: "measure",
            label: "Medir",
            key: "",
            action: () => {
              setDetail("technical");
              setInspectorOpen(true);
            },
          },
        ].map((item) => (
          <button
            key={item.name}
            type="button"
            className={`tool-button${item.active ? " is-active" : ""}`}
            title={`${item.label}${item.key ? ` · ${item.key}` : ""}`}
            aria-label={item.label}
            aria-pressed={item.active}
            disabled={item.unavailable}
            onClick={item.action}
          >
            <ToolIcon name={item.name} />
            <span>{item.label}</span>
            {item.key && <kbd>{item.key}</kbd>}
          </button>
        ))}
        <span className="assembly-tools__divider" aria-hidden="true" />
        {onLibraryToggle && (
          <button
            type="button"
            className="tool-button"
            aria-label="Biblioteca de tipologías"
            title="Biblioteca de tipologías"
            aria-expanded={libraryOpen}
            onClick={onLibraryToggle}
          >
            <ToolIcon name="library" />
            <span>Tipologías</span>
          </button>
        )}
        {narrow && (
          <button
            type="button"
            className="tool-button"
            aria-label="Inspector"
            title="Inspector"
            aria-expanded={inspectorOpen}
            onClick={() => {
              if (!inspectorOpen) dismissFloatingLayers();
              setInspectorOpen((open) => !open);
            }}
          >
            <ToolIcon name="inspector" />
            <span>Inspector</span>
          </button>
        )}
        <span className="assembly-tools__spacer" aria-hidden="true" />
        <button
          type="button"
          className="tool-button"
          aria-label="Árbol del conjunto"
          title="Árbol del conjunto"
          aria-expanded={treeOpen}
          onClick={() => setTreeOpen((open) => !open)}
        >
          <ToolIcon name="tree" />
          <span>Conjunto</span>
        </button>
        <button
          type="button"
          className="tool-button"
          aria-label="Atajos del editor"
          title="Atajos del editor · ?"
          onClick={() => setHelpOpen((open) => !open)}
        >
          <ToolIcon name="help" />
          <span>Atajos</span>
          <kbd>?</kbd>
        </button>
      </div>
      {libraryOpen && library && (
        <EditorFlyout
          title="Biblioteca de tipologías"
          onClose={() => onLibraryToggle?.()}
          className="editor-library"
        >
          {library}
        </EditorFlyout>
      )}
      {helpOpen && (
        <EditorFlyout title="Atajos del editor" onClose={() => setHelpOpen(false)}>
          <dl className="editor-shortcuts">
            {[
              ["V", "Seleccionar"],
              ["| / M", "Dividir vertical"],
              ["– / T", "Dividir horizontal"],
              ["F / Mayús+1", "Centrar"],
              ["Mayús+2", "Ajustar a selección"],
              ["Rueda", "Zoom al cursor"],
              ["Espacio + arrastrar / botón medio", "Desplazar dibujo"],
              ["Flechas / Mayús+flechas", "Divisor: 1 mm / 10 mm"],
              ["Ctrl+Z / Ctrl+Y", "Deshacer / rehacer"],
              ["Supr", "Eliminar selección"],
              ["Enter / Esc", "Confirmar / cancelar cota"],
              ["Ctrl+K", "Buscar o ejecutar comando"],
              ["Ctrl+S", "Guardar"],
            ].map(([key, action]) => (
              <div key={key}>
                <dt>
                  <kbd>{key}</kbd>
                </dt>
                <dd>{action}</dd>
              </div>
            ))}
          </dl>
        </EditorFlyout>
      )}
      {issuesOpen && (
        <EditorFlyout
          id="editor-missing"
          title="Qué falta"
          onClose={() => onCloseIssues?.()}
          className="editor-missing"
        >
          {!inputs.systemId && (
            <p>
              Elige una serie con autoridad para calcular el diseño.{" "}
              <button type="button" onClick={onChooseSystem}>
                Elegir serie
              </button>
            </p>
          )}
          {saveBlockReason && (
            <p>
              {saveBlockReason}
              <button
                type="button"
                onClick={() => {
                  onCloseIssues?.();
                  showInspector(saveBlockReason.includes("vidrio") ? "glass" : undefined);
                }}
              >
                Completar en el inspector
              </button>
            </p>
          )}
          {errorCode && (
            <p role="alert">
              No se pudo evaluar el diseño. Revisa la conexión y el catálogo.{" "}
              <button type="button" onClick={() => void retry()}>
                Reintentar cálculo
              </button>
            </p>
          )}
          {issues.length ? (
            <ul className="assembly-issues" ref={issuesListRef}>
              {issues.map((issue, index) => (
                <li key={index}>
                  <p>{issueText(issue, modules, couplings)}</p>
                  <button
                    type="button"
                    onClick={() => {
                      const target = issue.target;
                      if (target.startsWith("module:") || target.startsWith("coupling:"))
                        select(target.slice(target.indexOf(":") + 1));
                      onCloseIssues?.();
                      showInspector();
                    }}
                  >
                    Revisar {issue.target.startsWith("coupling:") ? "unión" : "marco"}
                  </button>
                </li>
              ))}
            </ul>
          ) : saveBlockReason === null && inputs.systemId ? (
            <p>
              {evaluating
                ? "El motor está calculando el diseño actual."
                : errorCode
                  ? "No se pudo evaluar. Revisa los datos del catálogo y vuelve a intentar."
                  : "El diseño está listo para guardar."}
            </p>
          ) : null}
        </EditorFlyout>
      )}
      {treeOpen && (
        <div className="assembly-tree">
          <ObjectTree
            root={objectTree}
            selection={selection}
            onSelect={(id) => {
              if (id !== null && modules.some((module) => module.id === id)) pickModule(id);
              else select(id);
            }}
            onContextMenu={(id, pos) => {
              // The tree is an editing surface too — right-click selects the
              // object and opens the same command menu the canvas offers.
              if (modules.some((module) => module.id === id)) pickModule(id);
              else select(id);
              setContextMenu(pos);
            }}
            title={t("tree.title")}
          />
        </div>
      )}
      <div
        className="assembly-canvas"
        onDoubleClick={(event) => {
          if ((event.target as Element).closest("[role='button'][aria-label^='Paño']"))
            showInspector("opening");
        }}
        onContextMenu={(event) => {
          event.preventDefault();
          setContextMenu({ x: event.clientX, y: event.clientY });
        }}
        onKeyDown={(event) => {
          // Keyboard context-menu trigger — Shift+F10 or the dedicated
          // ContextMenu key opens the same menu, centered on the canvas.
          if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
            event.preventDefault();
            const rect = event.currentTarget.getBoundingClientRect();
            setContextMenu({
              x: rect.left + rect.width / 2,
              y: rect.top + rect.height / 2,
            });
          }
        }}
      >
        <div className="assembly-view-choices" role="group" aria-label="Cara visible del dibujo">
          <button
            type="button"
            aria-pressed={viewFace === "interior"}
            className="assembly-face"
            onClick={() => setViewFace("interior")}
          >
            Vista interior
          </button>
          <button
            type="button"
            aria-pressed={viewFace === "exterior"}
            className="assembly-face"
            onClick={() => setViewFace("exterior")}
          >
            Vista exterior
          </button>
        </div>
        <details className="assembly-symbol-legend">
          <summary>Simbología</summary>
          <p>
            Vértice hacia la manilla. Continuo: abre hacia usted. Discontinuo: se aleja. Flecha:
            recorrido de la corredera.
          </p>
          <p>
            Carril 1 al exterior, numeración hacia el interior · convención de dibujo; contraste la
            sección del fabricante.
          </p>
        </details>
        {openingPreviewProduct && (
          <span className="opening-preview-label" role="status">
            {openingPreview.isPending
              ? "Calculando vista previa…"
              : previewReady
                ? "Vista previa · elige para aplicar"
                : "Esta composición requiere ajustar sus medidas o datos del catálogo"}
          </span>
        )}
        <CanvasViewport
          contentBox={frontBox}
          visibleBox={{
            x: -front.leftOver,
            y: -front.lift,
            w: front.totalW + front.leftOver + front.rightOver,
            h: front.height + front.lift + front.dip,
          }}
          selectionBox={selectionBox}
          status={statusText}
          contentEpoch={contentEpoch}
        >
          <ProductFrontContent
            elevation={drawingEvaluation?.elevation}
            drawingFacts={Object.fromEntries(
              (drawingEvaluation?.modules ?? []).map((item) => [
                item.module_id,
                item.drawing ?? null,
              ]),
            )}
            hideOverallWidth={(inputs.mounting?.length ?? 0) > 0}
            openingFacts={Object.fromEntries(
              (drawingEvaluation?.modules ?? []).map((item) => [
                item.module_id,
                (item.result?.opening_leaves ?? []) as unknown as OpeningLeafFact[],
              ]),
            )}
            product={previewReady ? openingPreviewProduct! : product}
            members={members}
            selectedId={selectedModule?.id ?? null}
            issues={issues}
            glassNotices={Object.fromEntries(
              Object.entries(glassChecks.data ?? {})
                .filter(([, check]) =>
                  check.findings.some((finding) => finding.code !== "tempered_exact"),
                )
                .map(([key, check]) => {
                  const alternative = options?.glass_specs.find((choice) =>
                    check.alternative_skus.includes(choice.sku),
                  );
                  return [
                    key,
                    {
                      message: check.findings
                        .filter((finding) => finding.code !== "tempered_exact")
                        .map((finding) => finding.message)
                        .join(" · "),
                      alternativeSku: alternative?.sku,
                      alternativeName: asGlassProduct(alternative?.product)?.name,
                    },
                  ];
                }),
            )}
            onGlassNotice={(moduleId, bayId, alternativeSku) => {
              select(`${moduleId}/${bayId}`);
              const choice = options?.glass_specs.find((item) => item.sku === alternativeSku);
              const module = product.assembly.modules.find((item) => item.id === moduleId);
              if (choice && module)
                simulateCommand([
                  { op: "set_glass", module: moduleId, bay: bayId, sku: choice.sku },
                ]);
            }}
            disabled={busy || viewFace === "exterior"}
            divideTool={divideToolType}
            dimLevel={detail}
            onSelectModule={pickModule}
            onSelectBay={(moduleId, bayId) => select(`${moduleId}/${bayId}`)}
            onSelectDivision={(moduleId, divisionId) => select(`${moduleId}/${divisionId}`)}
            onSelectCoupling={(couplingId) => select(couplingId)}
            selectedBayId={selectedBayModule && selectedBayNode ? selectedBayNode.id : null}
            selectedDivisionId={
              selectedDivisionModule && selectedDivisionNode ? selectedDivisionNode.id : null
            }
            onContextMenuModule={(moduleId, pos) => {
              select(moduleId);
              setContextMenu(pos);
            }}
            onAddUnit={coupleUnit}
            onCommitModuleWidth={(moduleId, widthMm) =>
              simulateCommand([{ op: "set_module_width", module: moduleId, width_mm: widthMm }])
            }
            onCommitTotalWidth={(totalMm) =>
              simulateCommand([{ op: "set_total_width", width_mm: totalMm }])
            }
            onCommitHeight={(heightMm) =>
              simulateCommand([{ op: "set_height", height_mm: heightMm }])
            }
            onCommitDivide={divideModule}
            onMoveDivision={(moduleId, divisionId, offsetMm) =>
              simulateCommand([
                { op: "move_divider", module: moduleId, divider: divisionId, offset_mm: offsetMm },
              ])
            }
            onResizeSeam={(index, deltaMm) => {
              const left = modules[index],
                right = modules[index + 1];
              if (left && right)
                simulateCommand([
                  {
                    op: "resize_seam",
                    left: left.id,
                    right: right.id,
                    delta_mm: deltaMm.toFixed(2),
                  },
                ]);
            }}
          />
          {proposal &&
            proposal.snapshot === inputs &&
            isProductModel(proposal.simulation.product) && (
              <g
                className="command-ghost"
                aria-label="Propuesta del motor en fantasma"
                pointerEvents="none"
              >
                <ProductFrontContent
                  product={proposal.simulation.product}
                  members={members}
                  selectedId={null}
                  issues={[]}
                  disabled
                  dimLevel="overview"
                  openingFacts={Object.fromEntries(
                    (
                      (proposal.simulation.engine as EngineAssemblyCalculateResponse)?.modules ?? []
                    ).map((item) => [
                      item.module_id,
                      (item.result?.opening_leaves ?? []) as OpeningLeafFact[],
                    ]),
                  )}
                  onSelectModule={() => {}}
                  onAddUnit={() => {}}
                  onCommitModuleWidth={() => {}}
                  onCommitTotalWidth={() => {}}
                  onCommitHeight={() => {}}
                />
              </g>
            )}
          {inputs.mounting?.length ? (
            <MountingDimensions product={product} evidence={inputs.mounting} />
          ) : null}
        </CanvasViewport>
        {proposal && proposal.snapshot === inputs && (
          <section className="editor-proposal" aria-label="Propuesta por revisar">
            <h3>Tres paños · centro fijo</h3>
            <p>
              Laterales abatibles hacia el centro · simulación del motor
              {options?.is_demo ? " · DEMO" : ""}
            </p>
            <p className="editor-proposal-price">
              Δ neto de línea ·{" "}
              {(proposal.simulation.price as EditorPrice).delta_net == null
                ? "Sin dato"
                : formatMoney(
                    (proposal.simulation.price as EditorPrice).delta_net,
                    (proposal.simulation.price as EditorPrice).currency,
                  )}
            </p>
            <details>
              <summary>¿De dónde sale?</summary>
              <p>
                {(proposal.simulation.price as EditorPrice).reason ??
                  (proposal.simulation.price as EditorPrice).source}
              </p>
              <p>
                Operaciones del registro sobre el diseño actual; diferencia exacta de ventas
                calculada por el motor. Se conserva la cantidad de la posición.
              </p>
            </details>
            {!proposal.simulation.valid && (
              <p role="alert">
                El motor bloquea la propuesta. Revisa las medidas y la autoridad de la serie antes
                de aplicar.
              </p>
            )}
            <button
              type="button"
              className="primary-action"
              disabled={busy || !proposal.simulation.valid}
              onClick={() => {
                if (proposal.snapshot !== useCanvasStore.getState().inputs) return;
                applyRegisteredOps(proposal.simulation.ops.map((op) => ({ ...op })));
                setProposal(null);
              }}
            >
              Aplicar propuesta
            </button>
            <button type="button" onClick={() => setProposal(null)}>
              Descartar
            </button>
          </section>
        )}
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
              role="img"
              aria-label={t("assembly.planView")}
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
                onContextMenuElement={(elementId, pos) => {
                  select(elementId);
                  setContextMenu(pos);
                }}
                onCommitAngle={(couplingId, angleDeg) =>
                  simulateCommand([
                    { op: "set_coupling_angle", coupling: couplingId, angle_deg: angleDeg },
                  ])
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
        {view3dOpen ? (
          <div className="model3d-inset" role="complementary" aria-label={t("assembly.view3d")}>
            <div className="plan-inset__header">
              <span>{t("assembly.view3d")}</span>
              <button
                type="button"
                aria-label={t("assembly.hide3d")}
                onClick={() => setView3dOpen(false)}
              >
                ×
              </button>
            </div>
            <Suspense
              fallback={
                <div className="model3d-loading" role="status">
                  <span className="model3d-loading__bar" aria-hidden="true" />
                  {t("assembly.loading3d")}
                </div>
              }
            >
              <Model3DView
                product={product}
                members={members}
                plan={evaluation?.plan ?? null}
                selection={selection}
                onSelectModule={pickModule}
                onSelectBay={(moduleId, bayId) => select(`${moduleId}/${bayId}`)}
                onSelectCoupling={select}
              />
            </Suspense>
          </div>
        ) : (
          <button type="button" className="model3d-toggle" onClick={() => setView3dOpen(true)}>
            {t("assembly.view3d")}
          </button>
        )}
      </div>
      {contextMenu && (
        <div
          ref={contextMenuRef}
          className="context-menu"
          role="menu"
          style={{
            left: contextMenuPos?.left ?? contextMenu.x,
            top: contextMenuPos?.top ?? contextMenu.y,
            visibility: contextMenuPos ? "visible" : "hidden",
          }}
          onMouseDown={(event) => event.stopPropagation()}
          onContextMenu={(event) => event.preventDefault()}
          onKeyDown={(event) => {
            // APG menu contract — arrows cycle, Home/End jump, Esc closes.
            if (
              event.key !== "ArrowDown" &&
              event.key !== "ArrowUp" &&
              event.key !== "Home" &&
              event.key !== "End"
            ) {
              return;
            }
            const items = Array.from(
              event.currentTarget.querySelectorAll<HTMLElement>('[role="menuitem"]'),
            );
            if (!items.length) return;
            event.preventDefault();
            const index = items.indexOf(document.activeElement as HTMLElement);
            const next =
              event.key === "Home"
                ? items[0]
                : event.key === "End"
                  ? items[items.length - 1]
                  : items[
                      (index + (event.key === "ArrowDown" ? 1 : items.length - 1)) % items.length
                    ];
            next?.focus();
          }}
        >
          {surface.commands
            .filter((command) => !command.params?.length)
            .map((command) => (
              <button
                key={command.id}
                type="button"
                role="menuitem"
                className="context-menu__item"
                onClick={() => {
                  command.run({});
                  setContextMenu(null);
                }}
              >
                <span className="context-menu__label">{command.title}</span>
                {command.shortcut && (
                  <kbd className="context-menu__hint">{formatShortcut(command.shortcut)}</kbd>
                )}
              </button>
            ))}
          {selectedLabel && (
            <button
              type="button"
              role="menuitem"
              className="context-menu__item context-menu__item--assistant"
              onClick={() => {
                askAssistant(t("assistant.modifyPrompt").replace("{target}", selectedLabel));
                setContextMenu(null);
              }}
            >
              {t("assistant.modifyWith")}
            </button>
          )}
        </div>
      )}
      <div
        className={`assembly-side${inspectorOpen ? " is-open" : ""}`}
        ref={inspectorRef}
        aria-label="Inspector contextual"
      >
        <header className="editor-inspector-header">
          <h3>Inspector</h3>
          <button
            type="button"
            aria-label="Cerrar inspector"
            onClick={() => setInspectorOpen(false)}
          >
            ×
          </button>
        </header>
        {isPending && (
          <p className="editor-calculation-note" role="status">
            Calculando las medidas de hoja y el kit. El dibujo conserva la última evaluación.
          </p>
        )}
        <div className="detail-levels" role="group" aria-label={t("assembly.detailLevels")}>
          {DETAIL_LEVELS.map(({ level, labelKey }) => (
            <button
              key={level}
              type="button"
              className={`detail-levels__btn${detail === level ? " is-active" : ""}`}
              aria-pressed={detail === level}
              onClick={() => setDetail(level)}
            >
              {t(labelKey)}
            </button>
          ))}
        </div>
        {detail === "technical" ? (
          <TechnicalPanel
            evaluation={currentEvaluation}
            options={options}
            moduleId={selectedBayModule?.id ?? selectedModule?.id}
            bayId={selectedBayNode && selectedBayModule ? selectedBayNode.id : null}
            moduleIndex={(moduleId) => modules.findIndex((module) => module.id === moduleId) + 1}
            members={members}
            bayNode={selectedBayNode}
            widthMm={Number((selectedBayModule ?? selectedModule)?.width_mm) || undefined}
          />
        ) : detail === "overview" ? (
          selectedModule ? (
            <ElementSummary
              title={selectedLabel ?? t("assembly.module")}
              rows={[
                [
                  t("inspector.dimensions"),
                  `${Number(selectedModule.width_mm).toFixed(0)} × ${Number(selectedModule.height_mm).toFixed(0)} mm`,
                ],
                [
                  t("assembly.opening"),
                  physicalNodeLabel(modulePrimaryBay(selectedModule)!) ??
                    t(
                      OPENING_OPTIONS.find(
                        ([value]) => value === moduleOpening(selectedModule),
                      )?.[1] ?? "intent.fixed",
                    ),
                ],
                [t("assembly.bayCount"), String(intentBays(selectedModule.tree).length)],
                [
                  t("assembly.glass"),
                  [moduleGlassThicknessMm(selectedModule), moduleGlassSku(selectedModule)]
                    .filter((value): value is string => value !== null && value !== "")
                    .join(" · ") || "—",
                ],
              ]}
            />
          ) : selectedBayModule && selectedBayNode ? (
            <ElementSummary
              title={selectedLabel ?? t("assembly.bay")}
              rows={[
                [
                  t("assembly.opening"),
                  physicalNodeLabel(selectedBayNode) ??
                    t(
                      OPENING_OPTIONS.find(
                        ([value]) => value === (selectedBayNode.opening_type ?? "FIXED"),
                      )?.[1] ?? "intent.fixed",
                    ),
                ],
                [
                  t("assembly.glass"),
                  [selectedBayNode.glass_thickness_mm, selectedBayNode.glass_article_sku]
                    .filter((value): value is string => value != null && value !== "")
                    .join(" · ") || "—",
                ],
                [
                  t("quotation.handleHeight"),
                  selectedBayNode.handle_height_mm
                    ? `${fmtMm(selectedBayNode.handle_height_mm)} mm`
                    : "—",
                ],
                ...(selectedBayNode.opening_type === "DOOR_ENTRY"
                  ? [
                      [t("assembly.panel"), selectedBayNode.panel_article_sku ?? "—"] as [
                        string,
                        string,
                      ],
                      [
                        t("assembly.hingeSide"),
                        selectedBayNode.door_handedness === "RIGHT"
                          ? t("assembly.hingeRight")
                          : t("assembly.hingeLeft"),
                      ] as [string, string],
                    ]
                  : []),
              ]}
            />
          ) : selectedCoupling ? (
            <ElementSummary
              title={selectedLabel ?? t("assembly.coupling")}
              rows={[
                [t("assembly.angle"), `${selectedCoupling.angle_deg}°`],
                [t("assembly.coupler"), selectedCoupling.coupler_profile_sku ?? "—"],
              ]}
            />
          ) : (
            (positionPanel ?? (
              <section className="assembly-inspector">
                <p className="assembly-hint">{t("assembly.elementHint")}</p>
              </section>
            ))
          )
        ) : selectedModule ? (
          <ModuleInspector
            organizationId={organizationId}
            color={inputs.color}
            onMountingChanged={onChanged}
            onOpeningPreview={setOpeningPreviewProduct}
            options={options}
            evaluation={currentEvaluation}
            module={selectedModule}
            product={product}
            members={members}
            glassSpecs={options?.glass_specs ?? []}
            panelSkus={panelSkus}
            panelChoices={options?.panel_choices ?? []}
            mullionSkus={mullionSkus}
            couplerSkus={couplerSkus}
            busy={busy}
            commit={simulateCommand}
            onAskAssistant={
              selectedLabel
                ? () => askAssistant(t("assistant.modifyPrompt").replace("{target}", selectedLabel))
                : undefined
            }
          />
        ) : selectedBayModule && selectedBayNode ? (
          <BayInspector
            onOpeningPreview={setOpeningPreviewProduct}
            options={options}
            evaluation={currentEvaluation}
            module={selectedBayModule}
            bay={selectedBayNode}
            product={product}
            organizationId={organizationId}
            color={inputs.color}
            glassSpecs={options?.glass_specs ?? []}
            panelSkus={panelSkus}
            panelChoices={options?.panel_choices ?? []}
            busy={busy}
            commit={simulateCommand}
            onAskAssistant={
              selectedLabel
                ? () => askAssistant(t("assistant.modifyPrompt").replace("{target}", selectedLabel))
                : undefined
            }
          />
        ) : selectedDivisionModule && selectedDivisionNode ? (
          <DivisionInspector
            module={selectedDivisionModule}
            division={selectedDivisionNode}
            product={product}
            busy={busy}
            commit={simulateCommand}
            onSelect={(id) => select(id)}
            onAskAssistant={
              selectedLabel
                ? () => askAssistant(t("assistant.modifyPrompt").replace("{target}", selectedLabel))
                : undefined
            }
          />
        ) : selectedCoupling ? (
          <CouplingInspector
            coupling={selectedCoupling}
            ordinal={couplings.findIndex((item) => item.id === selectedCoupling.id) + 1}
            couplerSkus={couplerSkus}
            busy={busy}
            commit={simulateCommand}
            onAskAssistant={
              selectedLabel
                ? () => askAssistant(t("assistant.modifyPrompt").replace("{target}", selectedLabel))
                : undefined
            }
          />
        ) : (
          <section className="assembly-inspector">
            <p className="assembly-hint">{t("assembly.elementHint")}</p>
          </section>
        )}
        {product && (
          <details
            open={assistantOpen}
            onToggle={(event) => setAssistantOpen(event.currentTarget.open)}
            className="editor-assistant"
          >
            <summary>Asistente y alternativas</summary>
            <AssistantPanel
              organizationId={organizationId}
              positionId={positionId}
              systemId={inputs.systemId}
              color={inputs.color}
              product={product}
              disabled={disabled}
              draft={assistantDraft}
              onDraftHandled={() => setAssistantDraft(null)}
              onApply={applyRegisteredOps}
            />
            <AlternativesPanel
              organizationId={organizationId}
              positionId={positionId}
              systemId={inputs.systemId}
              product={product}
              members={members}
              disabled={disabled}
              onUse={(next) => commit(next)}
              catalogReady={optionsReady}
              catalogKey={[
                ...(options?.glass_skus ?? []),
                ...(options?.panel_skus ?? []),
                ...(options?.coupler_skus ?? []),
                ...(options?.glazing_thicknesses ?? []),
                // Recipes are catalog authority too — a composition edit
                // makes old cards stale and new generations a new request.
                ...(options?.glass_specs ?? []).map((item) => `${item.sku}=${item.spec}`),
              ]
                .sort()
                .join("|")}
            />
          </details>
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
              onOpenIssues?.();
              const first = issues[0];
              if (
                first &&
                (first.target.startsWith("module:") || first.target.startsWith("coupling:"))
              ) {
                select(first.target.slice(first.target.indexOf(":") + 1));
              }
              // The list sits at the top of the inspector column — surface
              // it so the click visibly resolves to the issues, not silence.
              issuesListRef.current?.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
              });
            }}
          >
            {t("assembly.issueCount").replace("{count}", String(issues.length))}
          </button>
        )}
      </footer>
    </div>
  );
}

function CatalogLimitNotice({
  options,
  opening,
}: {
  options?: DesignOptions;
  opening: string;
}): JSX.Element | null {
  if (!options?.system_family) return null;
  const rule = options.dimensional_limits.find((item) => item.opening_type === opening);
  return (
    <details className="inspector-section">
      <summary>Límites del sistema y fuente</summary>
      {rule ? (
        <>
          <p>
            Ancho de hoja: {fmtMm(rule.min_leaf_width_mm)}–{fmtMm(rule.max_leaf_width_mm)} mm. Alto:{" "}
            {fmtMm(rule.min_leaf_height_mm)}–{fmtMm(rule.max_leaf_height_mm)} mm.
          </p>
          <p>
            Peso máximo:{" "}
            {rule.max_leaf_weight_kg == null ? "Sin dato" : fmtMm(rule.max_leaf_weight_kg) + " kg"}.
            Relación alto/ancho: {fmtMm(rule.min_aspect_ratio)}–{fmtMm(rule.max_aspect_ratio)}.
          </p>
          <p>Fuente: {rule.source}</p>
        </>
      ) : (
        <p>Sin dato: declara los límites de esta apertura en Catálogo antes de calcular.</p>
      )}
    </details>
  );
}

import { useEffect, useState } from "react";

import "./canvas.css";

import type { EngineAssemblyCalculateResponse, ProductIssue } from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { useCanvasStore, type CanvasDesignInputs } from "./canvasStore";
import { BowPlanSvg } from "./BowPlanSvg";
import { useAssemblyCalculation } from "./useAssemblyCalculation";
import {
  equalizeCouplingAngles,
  equalizeModuleWidths,
  isProductModel,
  makeBowProduct,
  moduleOpening,
  setAllModuleHeights,
  setCouplerSku,
  setCouplerSkuAll,
  setCouplingAngle,
  setModuleCount,
  setModuleOpening,
  setModuleWidth,
  totalModuleWidth,
  type ProductJson,
} from "./productEditing";

const OPENING_OPTIONS = [
  ["FIXED", "intent.fixed"],
  ["TURN_LEFT", "intent.turnLeft"],
  ["TURN_RIGHT", "intent.turnRight"],
  ["TILT_TURN_LEFT", "intent.tiltLeft"],
  ["TILT_TURN_RIGHT", "intent.tiltRight"],
  ["AWNING", "intent.awning"],
  ["DOOR_ENTRY", "intent.door"],
] as const;

const MODULE_COUNTS = [2, 3, 4, 5, 6];

const ISSUE_KEYS: Record<string, TranslationKey> = {
  couplings_count_mismatch: "assembly.issue.couplingsCountMismatch",
  assembly_folds_back: "assembly.issue.assemblyFoldsBack",
  plan_self_intersection: "assembly.issue.planSelfIntersection",
  module_geometry_failed: "assembly.issue.moduleGeometryFailed",
  coupler_profile_missing: "assembly.issue.couplerProfileMissing",
  coupler_profile_unknown: "assembly.issue.couplerProfileUnknown",
  coupler_height_mismatch: "assembly.issue.couplerHeightMismatch",
};

function issueText(issue: ProductIssue): string {
  const key = ISSUE_KEYS[issue.code];
  let text = key ? t(key) : issue.code;
  for (const [name, value] of Object.entries(issue.params)) {
    text = text.replace(`{${name}}`, value);
  }
  return text.replace("{target}", issue.target.replace("coupling:", "").replace("module:", ""));
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
): ProductJson {
  return makeBowProduct({
    moduleCount: 3,
    widthMm: Math.max(Number(inputs.nominalWidthMm) || 2100, 600),
    heightMm: Math.max(Number(inputs.nominalHeightMm) || 1400, 400),
    angleDeg: 15,
    glassThicknessMm,
    glassSpec,
  });
}

export function AssemblyEditor({
  organizationId,
  couplerSkus,
  disabled,
  onChanged,
  onEvaluationChange,
}: {
  organizationId: string;
  couplerSkus: string[];
  disabled: boolean;
  onChanged(): void;
  onEvaluationChange(evaluation: EngineAssemblyCalculateResponse | null): void;
}): JSX.Element | null {
  const inputs = useCanvasStore((state) => state.inputs);
  const selection = useCanvasStore((state) => state.selection);
  const commitInputs = useCanvasStore((state) => state.commitInputs);
  const selectBay = useCanvasStore((state) => state.selectBay);
  const product = isProductModel(inputs.product) ? inputs.product : null;
  const { evaluation, isPending, errorCode } = useAssemblyCalculation(organizationId, inputs);

  useEffect(() => {
    onEvaluationChange(evaluation);
  }, [evaluation, onEvaluationChange]);

  if (product === null) return null;
  const { modules, couplings } = product.assembly;
  const selected = modules.some((m) => m.id === selection) ? selection : (modules[0]?.id ?? "");

  function commit(next: ProductJson): void {
    commitInputs({ ...inputs, product: next });
    onChanged();
  }

  const statusKey =
    evaluation === null
      ? null
      : evaluation.status === "VALID"
        ? "assembly.statusValid"
        : evaluation.status === "MANUFACTURING_INCOMPLETE"
          ? "assembly.statusIncomplete"
          : "assembly.statusInvalid";

  return (
    <div className="assembly-editor" data-testid="assembly-editor">
      <div className="assembly-toolbar">
        <DraftField
          label={t("assembly.totalWidth")}
          value={totalModuleWidth(product).toFixed(2)}
          unit="mm"
          disabled={disabled}
          normalize={normalizeMm}
          onCommit={(value) => {
            const factor = Number(value) / totalModuleWidth(product);
            if (!Number.isFinite(factor) || factor <= 0) return;
            commit({
              ...product,
              assembly: {
                ...product.assembly,
                modules: modules.map((module) => ({
                  ...module,
                  width_mm: (Number(module.width_mm) * factor).toFixed(2),
                })),
              },
            });
          }}
        />
        <DraftField
          label={t("assembly.height")}
          value={modules[0]?.height_mm ?? ""}
          unit="mm"
          disabled={disabled}
          normalize={normalizeMm}
          onCommit={(value) => commit(setAllModuleHeights(product, value))}
        />
        <label className="assembly-field">
          <span>{t("assembly.modules")}</span>
          <select
            value={modules.length}
            disabled={disabled}
            onChange={(event) => commit(setModuleCount(product, Number(event.target.value)))}
          >
            {MODULE_COUNTS.map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={disabled}
          onClick={() => commit(equalizeModuleWidths(product))}
        >
          {t("assembly.equalizeModules")}
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => commit(equalizeCouplingAngles(product))}
        >
          {t("assembly.equalizeAngles")}
        </button>
      </div>

      <div className="assembly-workspace">
        <div className="assembly-canvas">
          <div className="design-caption">{t("assembly.planView")}</div>
          {evaluation?.plan ? (
            <BowPlanSvg
              plan={evaluation.plan}
              selectedModuleId={selected}
              onSelectModule={selectBay}
            />
          ) : (
            <p role="status">{isPending ? t("assembly.calculating") : t("assembly.noPlan")}</p>
          )}
          {errorCode && <p role="alert">{t("assembly.calculateError")}</p>}
          <div className="design-caption">{t("assembly.frontView")}</div>
          <div className="assembly-strip">
            {modules.map((module) => (
              <button
                key={module.id}
                type="button"
                className={
                  module.id === selected
                    ? "assembly-strip-module is-selected"
                    : "assembly-strip-module"
                }
                style={{ flexGrow: Number(module.width_mm) }}
                onClick={() => selectBay(module.id)}
              >
                <span className="assembly-strip-id">{module.id}</span>
                <span className="assembly-strip-opening">
                  {t(
                    OPENING_OPTIONS.find(([value]) => value === moduleOpening(module))?.[1] ??
                      "intent.fixed",
                  )}
                </span>
                <span className="assembly-strip-dims">
                  {Math.round(Number(module.width_mm))} × {Math.round(Number(module.height_mm))}
                </span>
              </button>
            ))}
          </div>
          <div
            className={`assembly-status assembly-status--${
              evaluation?.status.toLowerCase() ?? "idle"
            }`}
            role="status"
          >
            {statusKey ? t(statusKey) : isPending ? t("assembly.calculating") : ""}
          </div>
          {evaluation && evaluation.issues.length > 0 && (
            <ul className="assembly-issues">
              {evaluation.issues.map((issue, index) => (
                <li key={`${issue.code}-${index}`} className={`issue-${issue.severity}`}>
                  {issueText(issue)}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="assembly-controls">
          <div className="design-caption">{t("assembly.modules")}</div>
          <table className="assembly-table">
            <thead>
              <tr>
                <th />
                <th>{t("assembly.width")}</th>
                <th>{t("assembly.opening")}</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => (
                <tr
                  key={module.id}
                  className={module.id === selected ? "is-selected" : ""}
                  onClick={() => selectBay(module.id)}
                >
                  <th scope="row">{module.id}</th>
                  <td onClick={(event) => event.stopPropagation()}>
                    <DraftField
                      value={module.width_mm}
                      unit="mm"
                      disabled={disabled}
                      normalize={normalizeMm}
                      onCommit={(value) => commit(setModuleWidth(product, module.id, value))}
                    />
                  </td>
                  <td>
                    <select
                      value={moduleOpening(module)}
                      disabled={disabled}
                      onClick={(event) => event.stopPropagation()}
                      onChange={(event) =>
                        commit(
                          setModuleOpening(
                            product,
                            module.id,
                            event.target.value as (typeof OPENING_OPTIONS)[number][0],
                          ),
                        )
                      }
                    >
                      {OPENING_OPTIONS.map(([value, key]) => (
                        <option key={value} value={value}>
                          {t(key)}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="design-caption">{t("assembly.couplings")}</div>
          <table className="assembly-table">
            <thead>
              <tr>
                <th />
                <th>{t("assembly.angle")}</th>
                <th>{t("assembly.coupler")}</th>
              </tr>
            </thead>
            <tbody>
              {couplings.map((coupling) => (
                <tr key={coupling.id}>
                  <th scope="row">{coupling.id}</th>
                  <td>
                    <DraftField
                      value={coupling.angle_deg}
                      unit="°"
                      disabled={disabled}
                      normalize={normalizeAngle}
                      onCommit={(value) => commit(setCouplingAngle(product, coupling.id, value))}
                    />
                  </td>
                  <td>
                    <select
                      value={coupling.coupler_profile_sku ?? ""}
                      disabled={disabled}
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {couplerSkus.length > 0 && (
            <button
              type="button"
              disabled={disabled}
              onClick={() => commit(setCouplerSkuAll(product, couplerSkus[0] ?? null))}
            >
              {t("assembly.couplerAll").replace("{sku}", couplerSkus[0] ?? "")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

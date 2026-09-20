import { useEffect, useRef, useState } from "react";
import { engineCalculate } from "../../api/generated/dekopen";
import type { EngineCalculateResponse } from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import { type CanvasDesignInputs, useCanvasStore } from "./canvasStore";
import {
  changeOpening,
  exactMm,
  intentBays,
  moveDivision,
  walkIntent,
  OPENINGS,
  requestTree,
  singleBayTemplate,
  splitBay,
  topIntent,
  type Opening,
  type SplitType,
} from "./intentEditing";
import { requestFromInputs } from "./useEngineCalculation";

import { useEngineLayout } from "./useEngineLayout";
import "./canvas.css";

const openingLabels: Record<Opening, TranslationKey> = {
  FIXED: "intent.fixed",
  TURN_LEFT: "intent.turnLeft",
  TURN_RIGHT: "intent.turnRight",
  TILT_TURN_LEFT: "intent.tiltLeft",
  TILT_TURN_RIGHT: "intent.tiltRight",
  SLIDING_2L: "intent.sliding",
  AWNING: "intent.awning",
  DOOR_ENTRY: "intent.door",
};

type Props = {
  organizationId: string;
  onValidationChange(validating: boolean): void;
  onDraftChange?(): void;
  disabled?: boolean;
  mullions: Partial<Record<SplitType, { sku: string; name: string }>>;
  onCalculated(inputs: CanvasDesignInputs, response: EngineCalculateResponse): void;
};

export function IntentEditor({
  organizationId,
  onValidationChange,
  onDraftChange,
  disabled = false,
  mullions,
  onCalculated,
}: Props): JSX.Element {
  const inputs = useCanvasStore((state) => state.inputs);

  const layout = useEngineLayout(inputs, organizationId);
  const selection = useCanvasStore((state) => state.selection);
  const selectBay = useCanvasStore((state) => state.selectBay);

  const bays = intentBays(inputs.parametricTree);
  const selected = bays.find((bay) => bay.id === selection);
  const [width, setWidth] = useState(inputs.nominalWidthMm);
  const [height, setHeight] = useState(inputs.nominalHeightMm);
  const [offset, setOffset] = useState("");
  const [divisionId, setDivisionId] = useState("");
  const [divisionOffset, setDivisionOffset] = useState("");
  const [template, setTemplate] = useState<Opening>("FIXED");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<TranslationKey | null>(null);
  const [draftOpening, setDraftOpening] = useState<Opening>(selected?.opening_type ?? "FIXED");

  const locked = useRef(false);
  const divisions = walkIntent(inputs.parametricTree).filter(
    (node) => node.type === "SPLIT_V" || node.type === "SPLIT_H",
  );
  const epoch = useRef(0);

  useEffect(() => {
    setWidth(inputs.nominalWidthMm);
    setHeight(inputs.nominalHeightMm);
  }, [inputs]);

  useEffect(() => {
    setOffset("");
    setDraftOpening(selected?.opening_type ?? "FIXED");
  }, [inputs, selection, selected?.opening_type]);

  useEffect(
    () => () => {
      epoch.current += 1;
    },
    [],
  );

  async function apply(build: (base: CanvasDesignInputs) => CanvasDesignInputs): Promise<void> {
    if (disabled || locked.current || !selected || !organizationId) return;
    locked.current = true;
    setBusy(true);
    setError(null);
    onValidationChange(true);

    const base = useCanvasStore.getState().inputs;
    const generation = epoch.current;
    let candidate: CanvasDesignInputs;

    try {
      candidate = build(base);
    } catch {
      setError("intent.invalid");
      setDraftOpening(selected?.opening_type ?? "FIXED");
      locked.current = false;
      setBusy(false);
      onValidationChange(false);
      return;
    }

    let response: EngineCalculateResponse;

    try {
      const calculation = await engineCalculate(requestFromInputs(candidate), {
        headers: { "X-Organization-ID": organizationId },
      });
      if (calculation.status !== 200) throw new Error("calculation_failed");
      response = calculation.data;
    } catch {
      if (generation === epoch.current) {
        setError("intent.rejected");
        setDraftOpening(selected?.opening_type ?? "FIXED");
        locked.current = false;
        setBusy(false);
        onValidationChange(false);
      }
      return;
    }

    if (generation !== epoch.current) return;

    const accepted = useCanvasStore.getState().acceptIntent(base, candidate, selected.id);

    locked.current = false;
    setBusy(false);

    if (!accepted) {
      setError("intent.stale");
      onValidationChange(false);
      return;
    }

    onCalculated(candidate, response);
    onValidationChange(false);
  }

  function applyOpening(opening: Opening): void {
    if (!selected) return;
    setDraftOpening(opening);
    void apply((base) => ({
      ...base,
      parametricTree: changeOpening(base.parametricTree, selected.id, opening),
    }));
  }

  function divide(type: SplitType): void {
    const article = mullions[type];
    if (!selected || !article) return;

    void apply((base) => ({
      ...base,
      parametricTree: splitBay(
        base.parametricTree,
        selected.id,
        { type, offsetMm: offset, mullionSku: article.sku },
        {
          split: crypto.randomUUID(),
          secondBay: crypto.randomUUID(),
        },
      ),
    }));
  }

  const availableOpenings = OPENINGS.filter(
    (opening) => opening !== "DOOR_ENTRY" || topIntent(inputs.parametricTree).id === selected?.id,
  );
  const canSplit = selected && selected.opening_type !== "DOOR_ENTRY";
  const dimensionsPending = width !== inputs.nominalWidthMm || height !== inputs.nominalHeightMm;

  return (
    <section className="intent-editor" aria-label={t("intent.title")}>
      <fieldset disabled={disabled || busy}>
        <legend>{t("intent.title")}</legend>

        <label>
          {t("intent.selectedBay")}
          <select
            value={selected?.id ?? ""}
            disabled={dimensionsPending || !!offset}
            onChange={(event) => {
              selectBay(event.target.value);
              setError(null);
            }}
          >
            <option value="" disabled>
              {t("intent.chooseBay")}
            </option>
            {bays.map((bay, index) => (
              <option key={bay.id} value={bay.id}>
                {t("intent.bay")} {index + 1}
              </option>
            ))}
          </select>
        </label>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void apply((base) => ({
              ...base,
              nominalWidthMm: exactMm(width),
              nominalHeightMm: exactMm(height),
              parametricTree: requestTree(base.parametricTree),
            }));
          }}
        >
          <label>
            {t("intent.width")}
            <input
              inputMode="decimal"
              value={width}
              onChange={(event) => {
                setWidth(event.target.value);
                onDraftChange?.();
              }}
              required
            />
          </label>
          <label>
            {t("intent.height")}
            <input
              inputMode="decimal"
              value={height}
              onChange={(event) => {
                setHeight(event.target.value);
                onDraftChange?.();
              }}
              required
            />
          </label>
          <button type="submit" disabled={!selected}>
            {t("intent.applyDimensions")}
          </button>
        </form>

        {selected ? (
          <>
            <label>
              {t("intent.opening")}
              <select
                value={draftOpening}
                disabled={dimensionsPending || !!offset}
                onChange={(event) => {
                  const opening = OPENINGS.find((value) => value === event.target.value);
                  if (!opening) return;
                  applyOpening(opening);
                }}
              >
                {availableOpenings.map((opening) => (
                  <option key={opening} value={opening}>
                    {t(openingLabels[opening])}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              disabled={dimensionsPending || !!offset}
              onClick={() => applyOpening(draftOpening)}
            >
              {t("intent.applyOpening")}
            </button>

            {(() => {
              const reversible: Opening | null =
                selected.opening_type === "TURN_LEFT"
                  ? "TURN_RIGHT"
                  : selected.opening_type === "TURN_RIGHT"
                    ? "TURN_LEFT"
                    : selected.opening_type === "TILT_TURN_LEFT"
                      ? "TILT_TURN_RIGHT"
                      : selected.opening_type === "TILT_TURN_RIGHT"
                        ? "TILT_TURN_LEFT"
                        : null;
              if (!reversible) return null;
              return (
                <button
                  type="button"
                  disabled={dimensionsPending || !!offset}
                  onClick={() => applyOpening(reversible)}
                >
                  Invertir apertura ({t(openingLabels[reversible])})
                </button>
              );
            })()}

            {canSplit && (mullions.SPLIT_V || mullions.SPLIT_H) ? (
              <div>
                <label>
                  {t("intent.offset")}
                  <input
                    inputMode="decimal"
                    value={offset}
                    onChange={(event) => {
                      setOffset(event.target.value);
                      onDraftChange?.();
                    }}
                  />
                </label>

                {(["SPLIT_V", "SPLIT_H"] as const)
                  .filter((axis) => mullions[axis])
                  .map((axis) => (
                    <div key={axis}>
                      {(["half", "one_third", "two_thirds"] as const).map((ratio) => {
                        const candidate = layout.find((node) => node.node_id === selected.id)?.[
                          axis === "SPLIT_V" ? "vertical" : "horizontal"
                        ][ratio];

                        return (
                          <button
                            key={ratio}
                            type="button"
                            disabled={dimensionsPending || !candidate}

                            onClick={() =>
                              void apply((base) => ({
                                ...base,
                                parametricTree: splitBay(
                                  base.parametricTree,
                                  selected.id,

                                  {
                                    type: axis,
                                    offsetMm: candidate!,
                                    mullionSku: mullions[axis]!.sku,
                                  },

                                  { split: crypto.randomUUID(), secondBay: crypto.randomUUID() },
                                ),
                              }))
                            }
                          >
                            {t(axis === "SPLIT_V" ? "intent.vertical" : "intent.horizontal")} ·{" "}
                            {t(`intent.${ratio}`)}
                          </button>
                        );
                      })}
                    </div>
                  ))}
                <p>{t("intent.offsetHelp")}</p>
                {mullions.SPLIT_V ? (
                  <button
                    type="button"
                    disabled={!offset.trim() || dimensionsPending}
                    onClick={() => divide("SPLIT_V")}
                  >
                    {t("intent.vertical")}
                  </button>
                ) : null}
                {mullions.SPLIT_H ? (
                  <button
                    type="button"
                    disabled={!offset.trim() || dimensionsPending}
                    onClick={() => divide("SPLIT_H")}
                  >
                    {t("intent.horizontal")}
                  </button>
                ) : null}
              </div>
            ) : null}

            {divisions.length > 0 && (
              <fieldset disabled={dimensionsPending || !!offset}>
                <legend>{t("intent.existingDivision")}</legend>
                <label>
                  {t("intent.division")}
                  <select
                    value={divisionId}
                    onChange={(event) => {
                      setDivisionId(event.target.value);
                      setDivisionOffset(
                        divisions.find((node) => node.id === event.target.value)?.split_offset_mm ??
                          "",
                      );
                    }}
                  >
                    <option value="">{t("intent.chooseDivision")}</option>
                    {divisions.map((node, index) => (
                      <option value={node.id} key={node.id}>
                        {index + 1}. {t(node.type === "SPLIT_V" ? "intent.post" : "intent.transom")}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("intent.offset")}
                  <input
                    inputMode="decimal"
                    value={divisionOffset}
                    disabled={!divisionId}
                    onChange={(event) => {
                      setDivisionOffset(event.target.value);
                      onDraftChange?.();
                    }}
                  />
                </label>

                <div>
                  {(["half", "one_third", "two_thirds"] as const).map((ratio) => {
                    const division = divisions.find((node) => node.id === divisionId);

                    const candidate = layout.find((node) => node.node_id === divisionId)?.[
                      division?.type === "SPLIT_V" ? "vertical" : "horizontal"
                    ][ratio];

                    return (
                      <button
                        key={ratio}
                        type="button"
                        disabled={!candidate}

                        onClick={() => {
                          setDivisionOffset(candidate!);
                          onDraftChange?.();
                        }}
                      >
                        {t(`intent.${ratio}`)}
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  disabled={!divisionId || !divisionOffset.trim()}
                  onClick={() =>
                    void apply((base) => ({
                      ...base,
                      parametricTree: moveDivision(base.parametricTree, divisionId, divisionOffset),
                    }))
                  }
                >
                  {t("intent.moveDivision")}
                </button>
              </fieldset>
            )}

            <label>
              {t("intent.template")}
              <select
                value={template}
                onChange={(event) => {
                  const opening = OPENINGS.find((value) => value === event.target.value);
                  if (opening) setTemplate(opening);
                }}
              >
                {OPENINGS.map((opening) => (
                  <option key={opening} value={opening}>
                    {t(openingLabels[opening])}
                  </option>
                ))}
              </select>
            </label>
            <p>{t("intent.templateHelp")}</p>
            <button
              type="button"
              disabled={dimensionsPending || !!offset}
              onClick={() => {
                void apply((base) => ({
                  ...base,
                  parametricTree: singleBayTemplate(base.parametricTree, selected.id, template),
                }));
              }}
            >
              {t("intent.applyTemplate")}
            </button>
          </>
        ) : null}
      </fieldset>

      {busy ? <p role="status">{t("canvas.calculating")}</p> : null}
      {error ? (
        <div role="alert">
          <p>{t(error)}</p>
          <button type="button" onClick={() => setError(null)}>
            {t("intent.review")}
          </button>
        </div>
      ) : null}
    </section>
  );
}

import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError } from "../../api/apiMutator";
import {
  documentaryArtifactAccess,
  documentaryFreezeRevisionA,
  documentaryGenerateArtifact,
  documentaryPrepareInputs,
  documentarySaveInputs,
  projectsStartSuccessor,
  projectsResetPricing,
} from "../../api/generated/dekopen";
import type {
  AccessoryLine,
  AccessorySchedule,
  CoverageEnum,
  DocumentaryPolicyOption,
  DocumentaryPreparationPosition,
  DocumentaryPreparationResponse,
  DocumentaryStructuralInput,
  HandleIntent,
  HandleRequirement,
  ObligationKindEnum,
  OrderTypeEnum,
  ProjectResponse,
  WorkshopAnnotation,
} from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import {
  addDecimal,
  compareDecimal,
  formatDecimal,
  parseDecimal,
  subtractDecimal,
} from "./decimal";

function requirementsFor(position: DocumentaryPreparationPosition): HandleRequirement[] {
  const group = position.handle_requirements.find(
    (entry) => entry.policy_id === position.handle_requirement_policy_id,
  );
  return group?.requirements ?? [];
}

function intentFor(
  position: DocumentaryPreparationPosition,
  requirement: HandleRequirement,
): HandleIntent | undefined {
  return position.handle_intents.find(
    (intent) =>
      intent.bay_id === requirement.bay_id &&
      (intent.leaf_id ?? null) === requirement.leaf_id &&
      intent.handle_domain_slot === requirement.handle_domain_slot,
  );
}

function intentKey(requirement: HandleRequirement): string {
  return `${requirement.bay_id}|${requirement.leaf_id ?? ""}|${requirement.handle_domain_slot}`;
}

const REFERENCE_KEYS = {
  OUTER_TOP: "quotation.refOuterTop",
  OUTER_BOTTOM: "quotation.refOuterBottom",
  LEAF_TOP: "quotation.refLeafTop",
  LEAF_BOTTOM: "quotation.refLeafBottom",
} as const;

const EDGE_KEYS = {
  top: "quotation.edgeTop",
  right: "quotation.edgeRight",
  bottom: "quotation.edgeBottom",
  left: "quotation.edgeLeft",
} as const;

const OBLIGATION_KINDS = [
  "SEALING",
  "FASTENING",
  "INSTALLATION_ACCESSORY",
  "OTHER_DECLARED",
] as const;

const OBLIGATION_KIND_KEYS: Record<(typeof OBLIGATION_KINDS)[number], TranslationKey> = {
  SEALING: "quotation.kindSealing",
  FASTENING: "quotation.kindFastening",
  INSTALLATION_ACCESSORY: "quotation.kindInstallation",
  OTHER_DECLARED: "quotation.kindOther",
};

const ORDER_TYPES = [
  "SUPPLIER_PROFILE_PO",
  "SUPPLIER_GLASS_PO",
  "SUPPLIER_HARDWARE_PO",
  "SUPPLIER_PANEL_PO",
] as const;

const ORDER_TYPE_KEYS: Record<(typeof ORDER_TYPES)[number], TranslationKey> = {
  SUPPLIER_PROFILE_PO: "quotation.orderProfile",
  SUPPLIER_GLASS_PO: "quotation.orderGlass",
  SUPPLIER_HARDWARE_PO: "quotation.orderHardware",
  SUPPLIER_PANEL_PO: "quotation.orderPanel",
};

function parseMmList(text: string): string[] | null {
  const parts = text
    .split(/[,;]+/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (parts.length === 0) return [];
  if (!parts.every((part) => /^\d+(?:\.\d{1,4})?$/.test(part))) return null;
  return parts;
}

function CsvMmField({
  id,
  label,
  values,
  disabled,
  onCommit,
}: {
  id: string;
  label: string;
  values: string[] | null | undefined;
  disabled: boolean;
  onCommit(value: string[] | null): void;
}): JSX.Element {
  const canonical = values?.join(", ") ?? "";
  const [draft, setDraft] = useState(canonical);
  useEffect(() => setDraft(canonical), [canonical]);
  return (
    <label className="workshop-field">
      <span>{label}</span>
      <input
        id={id}
        value={draft}
        disabled={disabled}
        inputMode="decimal"
        placeholder="300, 600"
        onChange={(event) => setDraft(event.target.value)}
        onBlur={() => {
          const parsed = parseMmList(draft);
          if (parsed === null) {
            setDraft(canonical);
          } else if (parsed.join(",") !== (values ?? []).join(",")) {
            onCommit(parsed.length > 0 ? parsed : null);
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") event.currentTarget.blur();
          if (event.key === "Escape") setDraft(canonical);
        }}
      />
      <span className="workshop-unit">mm</span>
    </label>
  );
}

/** Valid input range for the entered height under its vertical reference.
 * The policy bounds describe the final handle coordinate measured from the
 * leaf's top edge; the engine converts each reference into that coordinate
 * before comparing, so the input's own range depends on the reference.
 * All math stays in exact decimals — binary floats would reject boundary
 * entries the engine accepts. */
function heightBounds(
  position: DocumentaryPreparationPosition,
  requirement: HandleRequirement,
  reference: HandleIntent["vertical_reference"],
): [string, string] | null {
  const rect = requirement.leaf_rects.find(
    (entry) => entry.placement_policy_id === position.manufacturing_placement_policy_id,
  );
  const min = parseDecimal(requirement.mounting_min_from_leaf_top_mm);
  const max = parseDecimal(requirement.mounting_max_from_leaf_top_mm);
  const leafTop = rect ? parseDecimal(rect.leaf_top_from_outer_top_mm) : null;
  const leafHeight = rect ? parseDecimal(rect.leaf_height_mm) : null;
  const outerHeight = parseDecimal(requirement.outer_height_mm);
  if (!min || !max || !leafTop || !leafHeight || !outerHeight) return null;
  switch (reference) {
    case "LEAF_TOP":
      return [formatDecimal(min), formatDecimal(max)];
    case "LEAF_BOTTOM":
      return [
        formatDecimal(subtractDecimal(leafHeight, max)),
        formatDecimal(subtractDecimal(leafHeight, min)),
      ];
    case "OUTER_TOP":
      return [formatDecimal(addDecimal(leafTop, min)), formatDecimal(addDecimal(leafTop, max))];
    case "OUTER_BOTTOM":
      return [
        formatDecimal(subtractDecimal(subtractDecimal(outerHeight, leafTop), max)),
        formatDecimal(subtractDecimal(subtractDecimal(outerHeight, leafTop), min)),
      ];
  }
}

/** Dropping or switching the handle policy must not leave intents whose
 * (bay, leaf, slot) no longer exists — freeze rejects extra intents — and a
 * retained intent's reference must still be permitted by the new rule. */
function reconciledHandlePolicy(
  position: DocumentaryPreparationPosition,
  policyId: string,
): Partial<DocumentaryPreparationPosition> {
  const requirements = position.handle_requirements.find(
    (entry) => entry.policy_id === policyId,
  )?.requirements;
  if (!requirements) return { handle_requirement_policy_id: policyId };
  const byKey = new Map(requirements.map((requirement) => [intentKey(requirement), requirement]));
  const intents = position.handle_intents.flatMap((intent) => {
    const requirement = byKey.get(
      `${intent.bay_id}|${intent.leaf_id ?? ""}|${intent.handle_domain_slot}`,
    );
    if (!requirement) return [];
    if (requirement.permitted_vertical_references.includes(intent.vertical_reference))
      return [intent];
    const [fallback] = requirement.permitted_vertical_references;
    return fallback ? [{ ...intent, vertical_reference: fallback }] : [];
  });
  return { handle_requirement_policy_id: policyId, handle_intents: intents };
}

function selectedPolicy(
  options: DocumentaryPolicyOption[],
  value: string | null,
  onChange: (value: string) => void,
  label: string,
  disabled: boolean,
  id: string,
): JSX.Element {
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        required
        value={value ?? ""}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{t("quotation.choosePolicy")}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label} · v{option.version}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ProjectQuotationPanel({
  project,
  orgId,
  canWrite,
  onChanged,
  onDirtyChange,
}: {
  project: ProjectResponse;
  orgId: string;
  canWrite: boolean;
  onChanged(): Promise<unknown>;
  onDirtyChange?(dirty: boolean): void;
}): JSX.Element {
  const [preparation, setPreparation] = useState<DocumentaryPreparationResponse | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const generation = useRef(0);
  const requestOptions = { headers: { "X-Organization-ID": orgId } };
  useEffect(
    () => () => {
      generation.current += 1;
    },
    [],
  );
  useEffect(() => {
    onDirtyChange?.(dirty);
    return () => onDirtyChange?.(false);
  }, [dirty, onDirtyChange]);

  async function loadPreparation(): Promise<void> {
    const current = ++generation.current;
    setBusy(true);
    setMessage("");
    try {
      const response = await documentaryPrepareInputs(project.id, requestOptions);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (generation.current === current) setPreparation(response.data);
    } catch {
      if (generation.current === current) setMessage(t("quotation.loadError"));
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }

  function updatePosition(index: number, update: Partial<DocumentaryPreparationPosition>): void {
    if (!preparation) return;
    setDirty(true);
    setPreparation({
      ...preparation,
      positions: preparation.positions.map((position, positionIndex) =>
        positionIndex === index ? { ...position, ...update } : position,
      ),
    });
  }

  function updateIntent(
    index: number,
    requirement: HandleRequirement,
    patch: Partial<HandleIntent>,
  ): void {
    if (!preparation) return;
    const position = preparation.positions[index];
    if (!position) return;
    const intents = [...position.handle_intents];
    const existing = intentFor(position, requirement);
    if (existing) {
      intents[intents.indexOf(existing)] = { ...existing, ...patch };
    } else {
      const reference = patch.vertical_reference ?? requirement.permitted_vertical_references[0];
      if (!reference) return;
      intents.push({
        bay_id: requirement.bay_id,
        leaf_id: requirement.leaf_id,
        handle_domain_slot: requirement.handle_domain_slot,
        requested_height_mm: patch.requested_height_mm ?? "",
        vertical_reference: reference,
      });
    }
    updatePosition(index, { handle_intents: intents });
  }

  function updateAnnotation(
    index: number,
    bayId: string,
    leafId: string | null,
    patch: Partial<WorkshopAnnotation>,
  ): void {
    if (!preparation) return;
    const position = preparation.positions[index];
    if (!position) return;
    const annotations = [...position.workshop_annotations];
    const existing = annotations.find(
      (item) => item.bay_id === bayId && (item.leaf_id ?? null) === leafId,
    );
    if (existing) {
      annotations[annotations.indexOf(existing)] = { ...existing, ...patch };
    } else {
      annotations.push({
        bay_id: bayId,
        leaf_id: leafId,
        finish_class: "WHITE",
        ...patch,
      });
    }
    updatePosition(index, { workshop_annotations: annotations });
  }

  function updateStructural(
    index: number,
    targetId: string,
    patch: Partial<DocumentaryStructuralInput>,
  ): void {
    if (!preparation) return;
    const position = preparation.positions[index];
    if (!position) return;
    const inputs = [...position.structural_inputs];
    const existing = inputs.find((item) => item.target_id === targetId);
    if (existing) {
      inputs[inputs.indexOf(existing)] = { ...existing, ...patch };
    } else {
      inputs.push({ target_id: targetId, ...patch });
    }
    updatePosition(index, { structural_inputs: inputs });
  }

  function updatePolishing(
    index: number,
    bayId: string,
    leafId: string | null,
    edge: "top" | "right" | "bottom" | "left",
    polished: boolean,
  ): void {
    if (!preparation) return;
    const position = preparation.positions[index];
    if (!position) return;
    const polishing = [...position.glass_polishing];
    const existing = polishing.find(
      (item) => item.bay_id === bayId && (item.leaf_id ?? null) === leafId,
    );
    if (existing) {
      polishing[polishing.indexOf(existing)] = {
        ...existing,
        edges: { ...existing.edges, [edge]: polished },
      };
    } else {
      polishing.push({
        bay_id: bayId,
        leaf_id: leafId,
        edges: { top: false, right: false, bottom: false, left: false, [edge]: polished },
      });
    }
    updatePosition(index, { glass_polishing: polishing });
  }

  function updateAccessories(
    index: number,
    patch: Partial<AccessorySchedule>,
  ): void {
    if (!preparation) return;
    const position = preparation.positions[index];
    if (!position) return;
    const schedule = position.accessory_schedule ?? {
      coverage: "NONE_REQUIRED" as CoverageEnum,
      items: [] as AccessoryLine[],
    };
    updatePosition(index, { accessory_schedule: { ...schedule, ...patch } });
  }

  function updateAccessoryItem(
    index: number,
    itemIndex: number,
    patch: Partial<AccessoryLine> | null,
  ): void {
    const position = preparation?.positions[index];
    if (!position?.accessory_schedule) return;
    const items = [...position.accessory_schedule.items];
    if (patch === null) {
      items.splice(itemIndex, 1);
    } else {
      items[itemIndex] = { ...items[itemIndex]!, ...patch };
    }
    updateAccessories(index, { items });
  }

  async function emit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (
      !preparation ||
      !confirmed ||
      !project.current_pricing_operation_id ||
      !preparation.quotation_valid_until ||
      preparation.positions.some(
        (position) =>
          !position.location_tag.trim() ||
          !position.manufacturing_placement_policy_id ||
          !position.handle_requirement_policy_id ||
          !position.reinforcement_cut_policy_id,
      )
    )
      return;
    const current = ++generation.current;
    setBusy(true);
    setMessage("");
    try {
      const saved = await documentarySaveInputs(
        project.id,
        {
          payment_terms: preparation.payment_terms,
          quotation_valid_until: preparation.quotation_valid_until,
          positions: preparation.positions.map((position) => ({
            position_id: position.position_id,
            calculation_hash: position.calculation_hash,
            location_tag: position.location_tag,
            manufacturing_placement_policy_id: position.manufacturing_placement_policy_id!,
            handle_requirement_policy_id: position.handle_requirement_policy_id!,
            reinforcement_cut_policy_id: position.reinforcement_cut_policy_id!,
            workshop_annotations: position.workshop_annotations,
            structural_inputs: position.structural_inputs,
            glass_polishing: position.glass_polishing,
            handle_intents: position.handle_intents,
            accessory_schedule: position.accessory_schedule,
            legacy_handle_migration_confirmed: position.legacy_handle_migration_confirmed,
          })),
        },
        requestOptions,
      );
      if (saved.status !== 200) throw new ApiError(saved.status, saved.data);
      const frozen = await documentaryFreezeRevisionA(
        project.id,
        { pricing_operation_id: project.current_pricing_operation_id, confirmed: true },
        requestOptions,
      );
      if (frozen.status !== 200 && frozen.status !== 201)
        throw new ApiError(frozen.status, frozen.data);
      if (generation.current !== current) return;
      setPreparation(null);
      setConfirmed(false);
      setDirty(false);
      setMessage(`${t("quotation.emitted")} ${frozen.data.revision_code}`);
      await onChanged();
    } catch (error) {
      if (generation.current !== current) return;
      setMessage(
        t(
          error instanceof ApiError && error.status === 409
            ? "quotation.conflict"
            : "quotation.error",
        ),
      );
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }

  async function startSuccessor(): Promise<void> {
    if (!window.confirm(t("quotation.successorConfirm"))) return;
    const current = ++generation.current;
    setBusy(true);
    setMessage("");
    try {
      const response = await projectsStartSuccessor(
        project.id,
        { confirmed: true, expected_current_revision: project.current_revision },
        requestOptions,
      );
      if (response.status !== 200 && response.status !== 201) {
        throw new ApiError(response.status, response.data);
      }
      if (generation.current !== current) return;
      setMessage(t("quotation.successorReady"));
      await onChanged();
    } catch {
      if (generation.current === current) setMessage(t("quotation.successorError"));
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }

  async function resetPricing(): Promise<void> {
    const reason = window.prompt(t("quotation.resetReason"));
    if (!reason?.trim() || !project.current_pricing_operation_id) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await projectsResetPricing(
        project.id,
        {
          expected_operation_id: project.current_pricing_operation_id,
          reason,
          confirmed: true,
        },
        requestOptions,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setPreparation(null);
      setDirty(false);
      await onChanged();
    } catch {
      setMessage(t("quotation.conflict"));
    } finally {
      setBusy(false);
    }
  }

  async function openEvidence(versionId: string): Promise<void> {
    const current = ++generation.current;
    setBusy(true);
    setMessage("");
    try {
      const artifact = await documentaryGenerateArtifact(
        {
          document_type: "DOC-01",
          format: "PDF",
          project_version_id: versionId,
          order_id: null,
        },
        requestOptions,
      );
      if (artifact.status !== 200 && artifact.status !== 201) {
        throw new ApiError(artifact.status, artifact.data);
      }
      const access = await documentaryArtifactAccess(artifact.data.id, requestOptions);
      if (access.status !== 200) {
        throw new ApiError(access.status, access.data);
      }
      if (generation.current === current)
        window.open(access.data.signed_url, "_blank", "noopener,noreferrer");
    } catch {
      if (generation.current === current) setMessage(t("quotation.documentError"));
    } finally {
      if (generation.current === current) setBusy(false);
    }
  }

  const canEmit =
    canWrite &&
    project.status === "DRAFT" &&
    project.pricing_current &&
    project.current_pricing_operation_id !== null;
  const canRevise = canWrite && project.status === "QUOTED";

  return (
    <section className="quotation-panel" aria-busy={busy}>
      <header>
        <div>
          <h2>{t("quotation.title")}</h2>
          <p>
            {t("quotation.current")}: <strong>{project.current_revision}</strong>
          </p>
        </div>
        {canEmit && !preparation && (
          <button disabled={busy} onClick={() => void loadPreparation()}>
            {t("quotation.prepare")}
          </button>
        )}
        {canEmit && (
          <button disabled={busy} onClick={() => void resetPricing()}>
            {t("quotation.resetPricing")}
          </button>
        )}
        {canRevise && (
          <button disabled={busy} onClick={() => void startSuccessor()}>
            {t("quotation.editQuoted")}
          </button>
        )}
      </header>
      {message && <p role="status">{message}</p>}
      {canWrite && project.status === "DRAFT" && !project.pricing_current && (
        <p>{t("quotation.priceFirst")}</p>
      )}
      {preparation && (
        <form className="quotation-form" onSubmit={(event) => void emit(event)}>
          <label htmlFor="quotation-payment-terms">{t("quotation.paymentTerms")}</label>
          <textarea
            id="quotation-payment-terms"
            required
            maxLength={2000}
            disabled={busy}
            value={preparation.payment_terms}
            onChange={(event) => {
              setDirty(true);
              setPreparation({ ...preparation, payment_terms: event.target.value });
            }}
          />
          <label htmlFor="quotation-valid-until">{t("quotation.validUntil")}</label>
          <input
            id="quotation-valid-until"
            required
            type="date"
            disabled={busy}
            value={preparation.quotation_valid_until ?? ""}
            onChange={(event) => {
              setDirty(true);
              setPreparation({ ...preparation, quotation_valid_until: event.target.value });
            }}
          />
          {preparation.positions.map((position, index) => (
            <fieldset key={position.position_id} disabled={busy}>
              <legend>
                {t("quotation.position")} {index + 1} · {position.system_name}
              </legend>
              <label htmlFor={`position-location-${position.position_id}`}>
                {t("projects.location")}
              </label>
              <input
                id={`position-location-${position.position_id}`}
                required
                maxLength={100}
                value={position.location_tag}
                onChange={(event) => updatePosition(index, { location_tag: event.target.value })}
              />
              {selectedPolicy(
                position.placement_options,
                position.manufacturing_placement_policy_id,
                (value) => updatePosition(index, { manufacturing_placement_policy_id: value }),
                t("quotation.placementPolicy"),
                busy,
                `placement-policy-${position.position_id}`,
              )}
              {selectedPolicy(
                position.handle_options,
                position.handle_requirement_policy_id,
                (value) => updatePosition(index, reconciledHandlePolicy(position, value)),
                t("quotation.handlePolicy"),
                busy,
                `handle-policy-${position.position_id}`,
              )}
              {selectedPolicy(
                position.reinforcement_options,
                position.reinforcement_cut_policy_id,
                (value) => updatePosition(index, { reinforcement_cut_policy_id: value }),
                t("quotation.reinforcementPolicy"),
                busy,
                `reinforcement-policy-${position.position_id}`,
              )}
              {requirementsFor(position).length > 0 && (
                <div className="handle-inputs">
                  <h4>{t("quotation.handleInputs")}</h4>
                  {requirementsFor(position).map((requirement) => {
                    const intent = intentFor(position, requirement);
                    const reference =
                      intent?.vertical_reference ?? requirement.permitted_vertical_references[0];
                    const bounds = reference
                      ? heightBounds(position, requirement, reference)
                      : null;
                    const height =
                      intent?.requested_height_mm !== undefined && intent.requested_height_mm !== ""
                        ? parseDecimal(intent.requested_height_mm)
                        : null;
                    const boundMin = bounds?.[0] ? parseDecimal(bounds[0]) : null;
                    const boundMax = bounds?.[1] ? parseDecimal(bounds[1]) : null;
                    const outOfBounds =
                      bounds !== null &&
                      height !== null &&
                      boundMin !== null &&
                      boundMax !== null &&
                      (compareDecimal(height, boundMin) < 0 ||
                        compareDecimal(height, boundMax) > 0);
                    return (
                      <div className="handle-row" key={intentKey(requirement)}>
                        <div className="handle-leaf">
                          <strong>{requirement.leaf_label}</strong>
                          <span>
                            {requirement.host_member_side === "LEFT"
                              ? t("quotation.sideLeft")
                              : t("quotation.sideRight")}
                            {requirement.handle_domain_slot !== "PRIMARY" &&
                              ` · ${requirement.handle_domain_slot}`}
                          </span>
                        </div>
                        <div className="handle-field">
                          <label
                            htmlFor={`handle-height-${position.position_id}-${intentKey(requirement)}`}
                          >
                            {t("quotation.handleHeight")}
                          </label>
                          <input
                            id={`handle-height-${position.position_id}-${intentKey(requirement)}`}
                            type="number"
                            inputMode="decimal"
                            min={bounds?.[0]}
                            max={bounds?.[1]}
                            step="any"
                            disabled={busy}
                            aria-invalid={outOfBounds || undefined}
                            placeholder={bounds ? `${bounds[0]}–${bounds[1]}` : undefined}
                            value={intent?.requested_height_mm ?? ""}
                            onChange={(event) =>
                              updateIntent(index, requirement, {
                                requested_height_mm: event.target.value,
                              })
                            }
                          />
                          {bounds && (
                            <span className="handle-bounds">
                              {t("quotation.handleBounds")} {bounds[0]}–{bounds[1]} mm
                            </span>
                          )}
                        </div>
                        <div className="handle-field">
                          <label
                            htmlFor={`handle-ref-${position.position_id}-${intentKey(requirement)}`}
                          >
                            {t("quotation.handleReference")}
                          </label>
                          <select
                            id={`handle-ref-${position.position_id}-${intentKey(requirement)}`}
                            disabled={
                              busy || requirement.permitted_vertical_references.length === 1
                            }
                            value={
                              intent?.vertical_reference ??
                              requirement.permitted_vertical_references[0]
                            }
                            onChange={(event) =>
                              updateIntent(index, requirement, {
                                requested_height_mm: intent?.requested_height_mm ?? "",
                                vertical_reference: event.target
                                  .value as HandleIntent["vertical_reference"],
                              })
                            }
                          >
                            {requirement.permitted_vertical_references.map((reference) => (
                              <option key={reference} value={reference}>
                                {t(REFERENCE_KEYS[reference])}
                              </option>
                            ))}
                          </select>
                        </div>
                        {!intent?.requested_height_mm && (
                          <span className="handle-pending">{t("quotation.handlePending")}</span>
                        )}
                        {outOfBounds && (
                          <span className="handle-pending" role="alert">
                            {t("quotation.handleOutOfBounds")}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              {position.workshop_targets && (
              <details className="workshop-inputs">
                <summary>{t("quotation.workshopData")}</summary>
                {position.workshop_targets.bays.map((bay) => {
                  const annotation = position.workshop_annotations.find(
                    (item) => item.bay_id === bay.bay_id && (item.leaf_id ?? null) === null,
                  );
                  return (
                    <div className="workshop-target" key={bay.bay_id}>
                      <strong>{bay.label}</strong>
                      <div className="workshop-row">
                        <CsvMmField
                          id={`drains-${position.position_id}-${bay.bay_id}`}
                          label={t("quotation.drains")}
                          values={annotation?.bottom_drain_holes_mm}
                          disabled={busy}
                          onCommit={(value) =>
                            updateAnnotation(index, bay.bay_id, null, {
                              bottom_drain_holes_mm: value,
                            })
                          }
                        />
                        <label className="workshop-field">
                          <span>{t("quotation.continuousWidth")}</span>
                          <input
                            type="number"
                            inputMode="decimal"
                            step="any"
                            min="0"
                            disabled={busy}
                            value={annotation?.continuous_width_mm ?? ""}
                            onChange={(event) =>
                              updateAnnotation(index, bay.bay_id, null, {
                                continuous_width_mm: event.target.value || null,
                              })
                            }
                          />
                          <span className="workshop-unit">mm</span>
                        </label>
                        <label className="workshop-check">
                          <input
                            type="checkbox"
                            disabled={busy}
                            checked={annotation?.has_coupler ?? false}
                            onChange={(event) =>
                              updateAnnotation(index, bay.bay_id, null, {
                                has_coupler: event.target.checked,
                              })
                            }
                          />
                          {t("quotation.expansionCoupler")}
                        </label>
                      </div>
                    </div>
                  );
                })}
                {position.workshop_targets.leaves.length > 0 && (
                  <div className="workshop-group">
                    <h5>{t("quotation.closingPoints")}</h5>
                    {position.workshop_targets.leaves.map((leaf) => {
                      const annotation = position.workshop_annotations.find(
                        (item) =>
                          item.bay_id === leaf.bay_id &&
                          (item.leaf_id ?? null) === leaf.leaf_id,
                      );
                      return (
                        <CsvMmField
                          key={`${leaf.bay_id}|${leaf.leaf_id ?? ""}`}
                          id={`closing-${position.position_id}-${leaf.bay_id}-${leaf.leaf_id ?? ""}`}
                          label={leaf.leaf_label}
                          values={annotation?.closing_points_perimeter_mm}
                          disabled={busy}
                          onCommit={(value) =>
                            updateAnnotation(index, leaf.bay_id, leaf.leaf_id ?? null, {
                              closing_points_perimeter_mm: value,
                            })
                          }
                        />
                      );
                    })}
                  </div>
                )}
                {position.workshop_targets.spans.length > 0 && (
                  <div className="workshop-group">
                    <h5>{t("quotation.structuralInputs")}</h5>
                    {position.workshop_targets.spans.map((span) => {
                      const structural = position.structural_inputs.find(
                        (item) => item.target_id === span.target_id,
                      );
                      return (
                        <div className="workshop-target" key={span.target_id}>
                          <strong>
                            {span.label} · {span.span_mm} mm
                          </strong>
                          <div className="workshop-row">
                            <label className="workshop-field">
                              <span>{t("quotation.requiredIx")}</span>
                              <input
                                type="number"
                                inputMode="decimal"
                                step="any"
                                min="0"
                                disabled={busy}
                                value={structural?.required_ix_cm4 ?? ""}
                                onChange={(event) =>
                                  updateStructural(index, span.target_id, {
                                    required_ix_cm4: event.target.value || null,
                                  })
                                }
                              />
                              <span className="workshop-unit">cm⁴</span>
                            </label>
                            <label className="workshop-field workshop-field--wide">
                              <span>{t("quotation.structuralBasis")}</span>
                              <input
                                type="text"
                                maxLength={1000}
                                disabled={busy}
                                value={structural?.structural_basis ?? ""}
                                placeholder={t("quotation.structuralBasisHint")}
                                onChange={(event) =>
                                  updateStructural(index, span.target_id, {
                                    structural_basis: event.target.value || null,
                                  })
                                }
                              />
                            </label>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
                {position.workshop_targets.glass.length > 0 && (
                  <div className="workshop-group">
                    <h5>{t("quotation.glassPolishing")}</h5>
                    {position.workshop_targets.glass.map((target) => {
                      const polishing = position.glass_polishing.find(
                        (item) =>
                          item.bay_id === target.bay_id &&
                          (item.leaf_id ?? null) === target.leaf_id,
                      );
                      return (
                        <div
                          className="workshop-target workshop-target--inline"
                          key={`${target.bay_id}|${target.leaf_id ?? ""}`}
                        >
                          <strong>{target.label}</strong>
                          {(["top", "right", "bottom", "left"] as const).map((edge) => (
                            <label className="workshop-check" key={edge}>
                              <input
                                type="checkbox"
                                disabled={busy}
                                checked={polishing?.edges[edge] ?? false}
                                onChange={(event) =>
                                  updatePolishing(
                                    index,
                                    target.bay_id,
                                    target.leaf_id ?? null,
                                    edge,
                                    event.target.checked,
                                  )
                                }
                              />
                              {t(EDGE_KEYS[edge])}
                            </label>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                )}
                <div className="workshop-group">
                  <h5>{t("quotation.accessories")}</h5>
                  <label className="workshop-field">
                    <span>{t("quotation.coverage")}</span>
                    <select
                      disabled={busy}
                      value={position.accessory_schedule?.coverage ?? ""}
                      onChange={(event) => {
                        const coverage = event.target.value as CoverageEnum | "";
                        if (!coverage) return;
                        updateAccessories(index, {
                          coverage,
                          items: coverage === "DECLARED" ? position.accessory_schedule?.items ?? [] : [],
                        });
                      }}
                    >
                      <option value="">{t("quotation.chooseCoverage")}</option>
                      <option value="NONE_REQUIRED">{t("quotation.coverageNone")}</option>
                      <option value="DECLARED">{t("quotation.coverageDeclared")}</option>
                    </select>
                  </label>
                  {position.accessory_schedule?.coverage === "DECLARED" && (
                    <div className="workshop-accessories">
                      {position.accessory_schedule.items.map((item, itemIndex) => (
                        <div className="workshop-accessory" key={itemIndex}>
                          <input
                            type="text"
                            disabled={busy}
                            maxLength={200}
                            placeholder={t("quotation.obligationId")}
                            value={item.obligation_id}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                obligation_id: event.target.value,
                              })
                            }
                          />
                          <select
                            disabled={busy}
                            value={item.obligation_kind}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                obligation_kind: event.target.value as ObligationKindEnum,
                              })
                            }
                          >
                            {OBLIGATION_KINDS.map((kind) => (
                              <option key={kind} value={kind}>
                                {t(OBLIGATION_KIND_KEYS[kind])}
                              </option>
                            ))}
                          </select>
                          <input
                            type="text"
                            disabled={busy}
                            maxLength={200}
                            placeholder={t("quotation.technicalSku")}
                            value={item.technical_sku}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                technical_sku: event.target.value,
                              })
                            }
                          />
                          <input
                            type="text"
                            disabled={busy}
                            maxLength={200}
                            placeholder={t("quotation.purchasingSku")}
                            value={item.purchasing_sku}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                purchasing_sku: event.target.value,
                              })
                            }
                          />
                          <input
                            type="text"
                            disabled={busy}
                            maxLength={300}
                            placeholder={t("quotation.manufacturer")}
                            value={item.manufacturer_name}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                manufacturer_name: event.target.value,
                              })
                            }
                          />
                          <select
                            disabled={busy}
                            value={item.order_type}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                order_type: event.target.value as OrderTypeEnum,
                              })
                            }
                          >
                            {ORDER_TYPES.map((order) => (
                              <option key={order} value={order}>
                                {t(ORDER_TYPE_KEYS[order])}
                              </option>
                            ))}
                          </select>
                          <input
                            type="number"
                            disabled={busy}
                            min="1"
                            step="1"
                            placeholder={t("quotation.quantityPerUnit")}
                            value={item.quantity_per_position_unit}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                quantity_per_position_unit: Math.max(
                                  1,
                                  Number(event.target.value) || 1,
                                ),
                              })
                            }
                          />
                          <input
                            type="text"
                            disabled={busy}
                            maxLength={1000}
                            placeholder={t("quotation.description")}
                            value={item.description}
                            onChange={(event) =>
                              updateAccessoryItem(index, itemIndex, {
                                description: event.target.value,
                              })
                            }
                          />
                          <button
                            type="button"
                            className="ghost-button is-danger"
                            disabled={busy}
                            aria-label={t("quotation.removeAccessory")}
                            onClick={() => updateAccessoryItem(index, itemIndex, null)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        className="ghost-button"
                        disabled={busy}
                        onClick={() =>
                          updateAccessories(index, {
                            items: [
                              ...position.accessory_schedule!.items,
                              {
                                obligation_id: `acc-${position.accessory_schedule!.items.length + 1}`,
                                obligation_kind: "INSTALLATION_ACCESSORY",
                                technical_sku: "",
                                purchasing_sku: "",
                                manufacturer_name: "",
                                order_type: "SUPPLIER_HARDWARE_PO",
                                unit: "EA",
                                quantity_per_position_unit: 1,
                                description: "",
                              },
                            ],
                          })
                        }
                      >
                        {t("quotation.addAccessory")}
                      </button>
                    </div>
                  )}
                </div>
              </details>
              )}
            </fieldset>
          ))}
          <label className="quotation-confirm">
            <input
              required
              type="checkbox"
              checked={confirmed}
              disabled={busy}
              onChange={(event) => {
                setDirty(true);
                setConfirmed(event.target.checked);
              }}
            />
            {t("quotation.confirm")}
          </label>
          <div className="projects-actions">
            <button disabled={busy || !confirmed}>{t("quotation.emit")}</button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                if (dirty && !window.confirm(t("projects.discard"))) return;
                setPreparation(null);
                setConfirmed(false);
                setDirty(false);
              }}
            >
              {t("projects.cancel")}
            </button>
          </div>
        </form>
      )}
      {(project.versions?.length ?? 0) > 0 && (
        <div className="quotation-history">
          <h3>{t("quotation.history")}</h3>
          <ul>
            {project.versions?.map((version) => (
              <li key={version.id}>
                <strong>{version.revision_code}</strong>
                <time dateTime={version.emitted_at}>
                  {new Date(version.emitted_at).toLocaleString("es-CL")}
                </time>
                <span>
                  {t(
                    version.documentary_complete
                      ? "quotation.completeEvidence"
                      : "quotation.designEvidence",
                  )}
                </span>
                <button disabled={busy} onClick={() => void openEvidence(version.id)}>
                  {t("quotation.openEvidence")}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

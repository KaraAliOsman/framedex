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
  DocumentaryPolicyOption,
  DocumentaryPreparationPosition,
  DocumentaryPreparationResponse,
  HandleIntent,
  HandleRequirement,
  ProjectResponse,
} from "../../api/generated/models";
import { t } from "../../i18n/es-CL";

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

/** Valid input range for the entered height under its vertical reference.
 * The policy bounds describe the final handle coordinate measured from the
 * leaf's top edge; the engine converts each reference into that coordinate
 * before comparing, so the input's own range depends on the reference. */
function heightBounds(
  position: DocumentaryPreparationPosition,
  requirement: HandleRequirement,
  reference: HandleIntent["vertical_reference"],
): [number, number] | null {
  const rect = requirement.leaf_rects.find(
    (entry) => entry.placement_policy_id === position.manufacturing_placement_policy_id,
  );
  if (!rect) return null;
  const min = Number(requirement.mounting_min_from_leaf_top_mm);
  const max = Number(requirement.mounting_max_from_leaf_top_mm);
  const leafTop = Number(rect.leaf_top_from_outer_top_mm);
  const leafHeight = Number(rect.leaf_height_mm);
  const outerHeight = Number(requirement.outer_height_mm);
  switch (reference) {
    case "LEAF_TOP":
      return [min, max];
    case "LEAF_BOTTOM":
      return [leafHeight - max, leafHeight - min];
    case "OUTER_TOP":
      return [leafTop + min, leafTop + max];
    case "OUTER_BOTTOM":
      return [outerHeight - leafTop - max, outerHeight - leafTop - min];
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
                    const height = Number(intent?.requested_height_mm ?? "");
                    const outOfBounds =
                      bounds !== null &&
                      intent !== undefined &&
                      intent.requested_height_mm !== "" &&
                      (height < bounds[0] || height > bounds[1]);
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

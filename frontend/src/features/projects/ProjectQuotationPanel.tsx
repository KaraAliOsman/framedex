import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError } from "../../api/apiMutator";
import {
  documentaryArtifactAccess,
  documentaryFreezeRevisionA,
  documentaryGenerateArtifact,
  documentaryPrepareInputs,
  documentarySaveInputs,
  projectsStartSuccessor,
} from "../../api/generated/dekopen";
import type {
  DocumentaryPolicyOption,
  DocumentaryPreparationPosition,
  DocumentaryPreparationResponse,
  ProjectResponse,
} from "../../api/generated/models";
import { t } from "../../i18n/es-CL";

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
}: {
  project: ProjectResponse;
  orgId: string;
  canWrite: boolean;
  onChanged(): Promise<unknown>;
}): JSX.Element {
  const [preparation, setPreparation] = useState<DocumentaryPreparationResponse | null>(null);
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
    setPreparation({
      ...preparation,
      positions: preparation.positions.map((position, positionIndex) =>
        positionIndex === index ? { ...position, ...update } : position,
      ),
    });
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
        { confirmed: true },
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
            onChange={(event) =>
              setPreparation({ ...preparation, payment_terms: event.target.value })
            }
          />
          <label htmlFor="quotation-valid-until">{t("quotation.validUntil")}</label>
          <input
            id="quotation-valid-until"
            required
            type="date"
            disabled={busy}
            value={preparation.quotation_valid_until ?? ""}
            onChange={(event) =>
              setPreparation({ ...preparation, quotation_valid_until: event.target.value })
            }
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
                (value) => updatePosition(index, { handle_requirement_policy_id: value }),
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
            </fieldset>
          ))}
          <label className="quotation-confirm">
            <input
              required
              type="checkbox"
              checked={confirmed}
              disabled={busy}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            {t("quotation.confirm")}
          </label>
          <div className="projects-actions">
            <button disabled={busy || !confirmed}>{t("quotation.emit")}</button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setPreparation(null);
                setConfirmed(false);
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

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { interfacePreferences, interfacePreferencesSave } from "../../api/generated/dekopen";
import type {
  AiAgentStep,
  InterfacePreferencesResponse,
  PatchedInterfacePreferencesRequest,
} from "../../api/generated/models";
import { interfaceQueryKey } from "../../app/interfacePreferences";
import { Icon } from "../../ui/Icon";
import { actionErrorDetail } from "../errors";
import "./operations.css";

const TAB: Record<string, string> = {
  positions: "ventanas y puertas",
  quote: "cotización",
  production: "producción",
  activity: "actividad",
};

/** Human summary of a presentation change; it only ever reaches this person. */
export function describeInterface(changes: PatchedInterfacePreferencesRequest): string[] {
  const lines: string[] = [];
  if (changes.density)
    lines.push(changes.density === "workshop" ? "Densidad de taller" : "Densidad de oficina");
  if (changes.text_size)
    lines.push(changes.text_size === "large" ? "Texto grande" : "Texto normal");
  if (changes.reduce_motion !== undefined)
    lines.push(changes.reduce_motion ? "Menos movimiento" : "Movimiento normal");
  if (changes.project_tab)
    lines.push(`Las obras se abren en ${TAB[changes.project_tab] ?? changes.project_tab}`);
  if (changes.rail_collapsed !== undefined)
    lines.push(changes.rail_collapsed ? "Barra lateral plegada" : "Barra lateral abierta");
  return lines;
}

/** The assistant changed (or proposes) how the interface looks for the
 * person; the receipt applies or undoes it with the same save «Tu interfaz»
 * uses. */
export function InterfaceStep({
  step,
  organizationId,
  declined = false,
  onSettled,
}: {
  step: AiAgentStep;
  organizationId: string;
  declined?: boolean;
  onSettled(action: "applied" | "declined" | "apply_failed" | "undone"): void;
}): JSX.Element {
  const queryClient = useQueryClient();
  const applied = step.applied as { previous?: InterfacePreferencesResponse } | undefined;
  const [state, setState] = useState<"proposed" | "applied" | "undone" | "declined">(
    applied ? "applied" : declined ? "declined" : "proposed",
  );
  const [previous, setPrevious] = useState<InterfacePreferencesResponse | undefined>(
    applied?.previous,
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(step.apply_error ?? "");
  const changes = (step.preferences ?? {}) as PatchedInterfacePreferencesRequest;
  const headers = { headers: { "X-Organization-ID": organizationId } };

  async function save(value: PatchedInterfacePreferencesRequest): Promise<void> {
    const saved = await interfacePreferencesSave(value, headers);
    if (saved.status !== 200) throw new Error("save");
    queryClient.setQueryData(interfaceQueryKey(organizationId), saved.data);
  }

  async function apply(): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const current = await interfacePreferences(headers);
      if (current.status !== 200) throw new Error("read");
      await save(changes);
      setPrevious(current.data);
      setState("applied");
      onSettled("applied");
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se pudo cambiar tu interfaz. Vuelve a intentar."));
      onSettled("apply_failed");
    } finally {
      setBusy(false);
    }
  }

  async function undo(): Promise<void> {
    if (!previous) return;
    setBusy(true);
    setMessage("");
    try {
      await save(previous);
      setState("undone");
      onSettled("undone");
    } catch (error) {
      setMessage(actionErrorDetail(error, "No se pudo deshacer. Vuelve a intentar."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="ask-dock__ops operation-project"
      data-state={state}
      aria-label={state === "applied" ? "Interfaz cambiada" : "Propuesta para tu interfaz"}
    >
      <p className="operation-project__label">
        {state === "applied" ? <Icon name="check" size={16} /> : <Icon name="sidebar" size={16} />}
        {step.label}
      </p>
      <ul className="operation-project__changes">
        {describeInterface(changes).map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {message ? <p role="alert">{message}</p> : null}
      <div className="ask-dock__ops-actions">
        {state === "proposed" ? (
          <>
            <button
              type="button"
              className="ask-dock__action ask-dock__action--primary"
              disabled={busy}
              onClick={() => void apply()}
            >
              Aplicar
            </button>
            <button
              type="button"
              className="ask-dock__action ask-dock__action--ghost"
              disabled={busy}
              onClick={() => {
                setState("declined");
                onSettled("declined");
              }}
            >
              Descartar
            </button>
          </>
        ) : null}
        {state === "applied" && previous ? (
          <button
            type="button"
            className="ask-dock__action ask-dock__action--ghost"
            disabled={busy}
            onClick={() => void undo()}
          >
            Deshacer
          </button>
        ) : null}
      </div>
      {state === "applied" ? (
        <p>Solo cambia para ti. También está en Ajustes · Tu interfaz.</p>
      ) : null}
      {state === "undone" ? <p>Cambio deshecho. Tu interfaz volvió a como estaba.</p> : null}
      {state === "declined" ? <p>Propuesta descartada.</p> : null}
    </section>
  );
}

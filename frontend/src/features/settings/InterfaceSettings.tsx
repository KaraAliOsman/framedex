import { useState } from "react";

import type {
  InterfacePreferencesResponse,
  PatchedInterfacePreferencesRequest,
} from "../../api/generated/models";
import { useInterfacePreferences } from "../../app/interfacePreferences";

type Choice<K extends keyof InterfacePreferencesResponse> = {
  value: InterfacePreferencesResponse[K];
  title: string;
  body: string;
};

const DENSITY: Choice<"density">[] = [
  { value: "office", title: "Oficina", body: "Filas compactas para mouse y teclado." },
  { value: "workshop", title: "Taller", body: "Botones y filas grandes para tablet o guantes." },
];
const TEXT: Choice<"text_size">[] = [
  { value: "normal", title: "Normal", body: "El tamaño de lectura de siempre." },
  { value: "large", title: "Grande", body: "Todo el texto un paso más grande." },
];
const TAB: { value: InterfacePreferencesResponse["project_tab"]; label: string }[] = [
  { value: "positions", label: "Ventanas y puertas" },
  { value: "quote", label: "Cotización" },
  { value: "production", label: "Producción" },
  { value: "activity", label: "Actividad" },
];

/** «Tu interfaz»: only for the signed-in person; the assistant changes the
 * same preferences when asked, with undo. */
export function InterfaceSettings({ orgId }: { orgId: string }): JSX.Element {
  const look = useInterfacePreferences(orgId);
  const [message, setMessage] = useState("");
  const value = look.preferences;

  async function change(changes: PatchedInterfacePreferencesRequest): Promise<void> {
    setMessage("");
    const saved = await look.save(changes);
    setMessage(saved ? "Guardado. Solo cambia para ti." : "No se pudo guardar. Vuelve a intentar.");
  }

  return (
    <section className="settings-card interface-settings" aria-labelledby="interface-title">
      <h2 id="interface-title">Tu interfaz</h2>
      <p>
        Solo cambia cómo ves DEKOPEN tú, en este taller y en todos tus equipos. También puedes
        pedírselo al asistente: «pon el texto más grande».
      </p>
      <fieldset className="site-measurement" disabled={!look.loaded}>
        <legend>Densidad</legend>
        {DENSITY.map((option) => (
          <label key={option.value} className="site-measurement__option">
            <input
              type="radio"
              name="interface-density"
              checked={value.density === option.value}
              onChange={() => void change({ density: option.value })}
            />
            <span>
              <strong>{option.title}</strong>
              <span>{option.body}</span>
            </span>
          </label>
        ))}
      </fieldset>
      <fieldset className="site-measurement" disabled={!look.loaded}>
        <legend>Tamaño del texto</legend>
        {TEXT.map((option) => (
          <label key={option.value} className="site-measurement__option">
            <input
              type="radio"
              name="interface-text"
              checked={value.text_size === option.value}
              onChange={() => void change({ text_size: option.value })}
            />
            <span>
              <strong>{option.title}</strong>
              <span>{option.body}</span>
            </span>
          </label>
        ))}
      </fieldset>
      <div className="interface-settings__rows">
        <label className="settings-inline">
          Una obra se abre en
          <select
            value={value.project_tab}
            disabled={!look.loaded}
            onChange={(event) =>
              void change({
                project_tab: event.target.value as InterfacePreferencesResponse["project_tab"],
              })
            }
          >
            {TAB.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <input
            type="checkbox"
            checked={value.reduce_motion}
            disabled={!look.loaded}
            onChange={(event) => void change({ reduce_motion: event.target.checked })}
          />
          Menos movimiento
        </label>
        <label>
          <input
            type="checkbox"
            checked={value.rail_collapsed}
            disabled={!look.loaded}
            onChange={(event) => void change({ rail_collapsed: event.target.checked })}
          />
          Barra lateral plegada
        </label>
      </div>
      {message && <p role="status">{message}</p>}
    </section>
  );
}

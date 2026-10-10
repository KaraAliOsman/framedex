import { useCallback, useEffect, useState } from "react";
import { organizationBrandingGet, organizationBrandingSave } from "../../api/generated/dekopen";
import type { DocumentPreferences } from "../../api/generated/models";
import { ValidatedForm } from "../../ui/FormValidation";
import { DimLoader } from "../../ui";
import { CommercialTermsEditor, validCommercialTerms } from "./CommercialTermsEditor";
import "./document-settings.css";

export function DocumentSettings({
  orgId,
  canEdit,
}: {
  orgId: string;
  canEdit: boolean;
}): JSX.Element {
  const [value, setValue] = useState<DocumentPreferences | null>(null);
  const [status, setStatus] = useState("Cargando preferencias de documentos…");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const load = useCallback(async (): Promise<void> => {
    setStatus("Cargando preferencias de documentos…");
    setError(false);
    try {
      const response = await organizationBrandingGet({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new Error("read");
      setValue(response.data.document_preferences);
      setStatus("");
    } catch {
      setStatus("No se pudieron cargar las preferencias. Revisa tu conexión y vuelve a intentar.");
      setError(true);
    }
  }, [orgId]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <section className="settings-card document-settings" aria-label="Documentos">
      <h3>Documentos</h3>
      <p>
        Estas preferencias se guardan en cada nueva revisión. El logo y los datos del emisor se
        configuran en Identidad.
      </p>
      {!canEdit && (
        <p>
          El dueño o un estimador pueden configurar documentos. Pídeles que guarden las preferencias
          de la empresa.
        </p>
      )}
      {!value && !error && <DimLoader label="Cargando preferencias de documentos" />}
      {status && <p role={error ? "alert" : "status"}>{status}</p>}
      {!value && error && (
        <button type="button" className="secondary-action" onClick={() => void load()}>
          Reintentar
        </button>
      )}
      {value && (
        <ValidatedForm
          onSubmit={async (event) => {
            event.preventDefault();
            if (!validCommercialTerms(value.commercial_terms)) {
              setStatus(
                "Revisa el calendario: cada hito debe tener nombre y los porcentajes deben sumar 100 %.",
              );
              setError(true);
              return;
            }
            if (
              typeof value.quotation_valid_days !== "number" ||
              !Number.isInteger(value.quotation_valid_days) ||
              value.quotation_valid_days < 1 ||
              value.quotation_valid_days > 365
            ) {
              setStatus(
                "La vigencia comercial debe ser de 1 a 365 días. Revisa ese campo antes de guardar.",
              );
              setError(true);
              return;
            }
            if (
              typeof value.quotation_preview_minutes !== "number" ||
              !Number.isInteger(value.quotation_preview_minutes) ||
              value.quotation_preview_minutes < 5 ||
              value.quotation_preview_minutes > 60
            ) {
              setStatus(
                "La revisión del PDF debe durar entre 5 y 60 minutos. Revisa ese campo antes de guardar.",
              );
              setError(true);
              return;
            }
            setBusy(true);
            setStatus("");
            setError(false);
            try {
              const response = await organizationBrandingSave(
                { document_preferences: value },
                { headers: { "X-Organization-ID": orgId } },
              );
              if (response.status !== 200) {
                setStatus(
                  response.status === 403
                    ? "Tu rol no puede guardar documentos. Pide al dueño o a un estimador que configure estas preferencias."
                    : "No se pudieron guardar las preferencias. Revisa los campos y vuelve a intentar.",
                );
                setError(true);
                return;
              }
              setValue(response.data.document_preferences);
              setStatus("Preferencias guardadas para nuevas emisiones.");
            } catch {
              setStatus(
                "No se pudieron guardar las preferencias. Revisa tu conexión y vuelve a intentar.",
              );
              setError(true);
            } finally {
              setBusy(false);
            }
          }}
        >
          <fieldset disabled={busy || !canEdit}>
            <legend>Formato de impresión</legend>
            <label>
              Papel
              <select
                aria-label="Papel"
                value={value.paper}
                onChange={(event) =>
                  setValue({ ...value, paper: event.target.value as DocumentPreferences["paper"] })
                }
              >
                <option value="LETTER">Carta</option>
                <option value="OFICIO">Oficio</option>
                <option value="A4">A4</option>
              </select>
            </label>
            <label>
              Acento de impresión
              <select
                aria-label="Acento de impresión"
                value={value.accent}
                onChange={(event) =>
                  setValue({
                    ...value,
                    accent: event.target.value as DocumentPreferences["accent"],
                  })
                }
              >
                <option value="TEAL">Verde técnico</option>
                <option value="TEAL_DARK">Verde técnico oscuro</option>
                <option value="GRAPHITE">Grafito</option>
              </select>
            </label>
            <label>
              Texto legal del pie
              <textarea
                maxLength={240}
                value={value.legal_footer}
                onChange={(event) => setValue({ ...value, legal_footer: event.target.value })}
              />
            </label>
            <label>
              Vigencia comercial para cotizaciones nuevas (días)
              <input
                type="number"
                min={1}
                max={365}
                step={1}
                value={value.quotation_valid_days}
                onChange={(event) =>
                  setValue({ ...value, quotation_valid_days: event.target.valueAsNumber })
                }
              />
              <small>
                Se propone desde la fecha local de Chile. Puedes cambiarla antes de emitir; las
                revisiones selladas conservan su fecha.
              </small>
            </label>
            <label>
              Vigencia de la revisión del PDF (minutos)
              <input
                type="number"
                min={5}
                max={60}
                step={1}
                value={value.quotation_preview_minutes}
                onChange={(event) =>
                  setValue({ ...value, quotation_preview_minutes: event.target.valueAsNumber })
                }
              />
              <small>
                Entre 5 y 60 minutos. Al vencer debes preparar y revisar otro PDF; la vigencia
                comercial se declara por cotización.
              </small>
            </label>
          </fieldset>
          <CommercialTermsEditor
            value={value.commercial_terms}
            onChange={(commercial_terms) => setValue({ ...value, commercial_terms })}
            disabled={busy || !canEdit}
          />
          {canEdit && (
            <button type="submit" className="primary-action" disabled={busy}>
              {busy ? "Guardando…" : "Guardar documentos"}
            </button>
          )}
        </ValidatedForm>
      )}
    </section>
  );
}

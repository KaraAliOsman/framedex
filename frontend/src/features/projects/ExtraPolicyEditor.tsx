import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { organizationExtraPolicy, organizationExtraPolicySave } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { actionErrorDetail } from "../errors";
import { ExtraDefinitionEditor, ExtraImport, emptyExtra } from "./ExtraDefinitionEditor";
import { extraDescription, type ExtraPolicy } from "./extraModel";
import "./extras.css";

export function ExtraPolicyEditor({
  orgId,
  canWrite,
}: {
  orgId: string;
  canWrite: boolean;
}): JSX.Element {
  const client = useQueryClient();
  const key = ["extra-policy", orgId];
  const query = useQuery({
    queryKey: key,
    enabled: canWrite,
    queryFn: async () => {
      const result = await organizationExtraPolicy({ headers: { "X-Organization-ID": orgId } });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  const [draft, setDraft] = useState<ExtraPolicy | null>(null);
  const [undo, setUndo] = useState<ExtraPolicy | null>(null);
  const [review, setReview] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const saved = query.data?.policy as ExtraPolicy | undefined;
  const value = draft ?? saved;
  const edit = (next: ExtraPolicy) => {
    setDraft(next);
    setReview(false);
    setError("");
  };
  async function save(next: ExtraPolicy, note = reason) {
    if (!query.data) return;
    setBusy(true);
    setError("");
    try {
      const result = await organizationExtraPolicySave(
        { policy: next, expected_revision: query.data.revision, reason: note },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      setUndo(saved ?? null);
      setDraft(null);
      setReview(false);
      setReason("");
      client.setQueryData(key, result.data);
      await client.invalidateQueries({ queryKey: ["project-services", orgId] });
    } catch (cause) {
      setError(
        actionErrorDetail(cause, "No pudimos guardar la plantilla. Revisa sus reglas y tarifas."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="settings-group" aria-label="Extras y servicios">
      <h2>Extras y servicios</h2>
      {!canWrite ? (
        <p>Solo el dueño puede cambiar las tarifas y plantillas de la organización.</p>
      ) : query.isPending ? (
        <p role="status">Cargando plantilla…</p>
      ) : query.isError ? (
        <p role="alert">
          No pudimos cargar la plantilla.{" "}
          <button type="button" onClick={() => void query.refetch()}>
            Reintentar
          </button>
        </p>
      ) : (
        value && (
          <fieldset disabled={busy} className="extra-policy">
            <p>
              Estas tarifas tienen fuente propia. La plantilla se aplica a posiciones nuevas; las
              revisiones emitidas conservan su autoridad sellada.
            </p>
            <label>
              Precios de extras en la cotización
              <select
                value={value.document_prices}
                onChange={(e) =>
                  edit({
                    ...value,
                    document_prices: e.target.value as ExtraPolicy["document_prices"],
                  })
                }
              >
                <option value="ITEMIZED">Mostrar cada sublínea con precio</option>
                <option value="GROUPED">Agrupar en el precio de la posición</option>
              </select>
            </label>
            <h3>Servicios declarados</h3>
            {!value.services.length && (
              <p>
                Sin servicios. Declara costo, venta y fuente antes de ofrecer instalación, retiro o
                flete.
              </p>
            )}
            {value.services.map((item, index) => (
              <details key={index} className="extra-authority-row">
                <summary>
                  {item.name || "Servicio sin nombre"}
                  {item.synthetic && " · DEMO"}
                </summary>
                <ExtraDefinitionEditor
                  servicesOnly
                  value={item}
                  onChange={(next) =>
                    edit({
                      ...value,
                      services: value.services.map((v, i) => (i === index ? next : v)),
                    })
                  }
                />
                <button
                  type="button"
                  onClick={() =>
                    edit({ ...value, services: value.services.filter((_, i) => i !== index) })
                  }
                >
                  Quitar servicio
                </button>
              </details>
            ))}
            <button
              type="button"
              onClick={() => edit({ ...value, services: [...value.services, emptyExtra()] })}
            >
              Agregar servicio con fuente
            </button>
            <h3>Plantilla para posiciones nuevas</h3>
            <p>
              Elige servicios por posición o importa los códigos de accesorios declarados por tus
              series.
            </p>
            {value.position_defaults.map((item, index) => (
              <div className="extra-authority-fields extra-authority-row" key={index}>
                <label>
                  Extra predeterminado
                  <select
                    value={item.code}
                    onChange={(e) =>
                      edit({
                        ...value,
                        position_defaults: value.position_defaults.map((v, i) =>
                          i === index ? { code: e.target.value } : v,
                        ),
                      })
                    }
                  >
                    <option value="">Elige un servicio por posición</option>
                    {!value.services.some((v) => v.code === item.code) && item.code && (
                      <option value={item.code}>Accesorio de catálogo · {item.code}</option>
                    )}
                    {value.services
                      .filter((v) => v.scope === "POSITION")
                      .map((v) => (
                        <option key={v.code} value={v.code}>
                          {v.name}
                        </option>
                      ))}
                  </select>
                </label>
                <button
                  type="button"
                  onClick={() =>
                    edit({
                      ...value,
                      position_defaults: value.position_defaults.filter((_, i) => i !== index),
                    })
                  }
                >
                  Quitar de la plantilla
                </button>
              </div>
            ))}
            <button
              type="button"
              disabled={!value.services.some((v) => v.scope === "POSITION")}
              onClick={() =>
                edit({ ...value, position_defaults: [...value.position_defaults, { code: "" }] })
              }
            >
              Agregar servicio predeterminado
            </button>
            <ExtraImport
              value={value}
              onChange={edit}
              parse={(input) => {
                const v = input as ExtraPolicy;
                if (
                  v?.schema_version !== 1 ||
                  !Array.isArray(v.services) ||
                  !Array.isArray(v.position_defaults) ||
                  !["ITEMIZED", "GROUPED"].includes(v.document_prices)
                )
                  throw new Error();
                return v;
              }}
            />
            {draft && (
              <>
                <label>
                  Motivo del cambio
                  <input
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Indica la fuente o condición que cambió"
                  />
                </label>
                <button type="button" disabled={!reason.trim()} onClick={() => setReview(true)}>
                  Revisar cambios de plantilla
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setDraft(null);
                    setReview(false);
                  }}
                >
                  Descartar cambios
                </button>
              </>
            )}
            {review && draft && (
              <section aria-label="Revisión de plantilla">
                <h3>Revisión antes de guardar</h3>
                <table className="ui-table">
                  <thead>
                    <tr>
                      <th>Servicio</th>
                      <th>Actual</th>
                      <th>Propuesto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ...new Set([
                        ...(saved?.services.map((v) => v.code) ?? []),
                        ...draft.services.map((v) => v.code),
                      ]),
                    ].map((code) => {
                      const before = saved?.services.find((v) => v.code === code);
                      const after = draft.services.find((v) => v.code === code);
                      const describe = (item: typeof before) =>
                        item ? extraDescription(item) : "No incluido";
                      return (
                        <tr key={code}>
                          <td>{after?.name ?? before?.name ?? "Sin nombre"}</td>
                          <td className="extra-equation">{describe(before)}</td>
                          <td className="extra-equation">{describe(after)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <p>
                  Posiciones predeterminadas: {saved?.position_defaults.length ?? 0} →{" "}
                  {draft.position_defaults.length}. Política:{" "}
                  {draft.document_prices === "ITEMIZED"
                    ? "Sublíneas con precio"
                    : "Precio agrupado"}
                  .
                </p>
                <details>
                  <summary>Detalles técnicos de la propuesta</summary>
                  <pre>{JSON.stringify(draft, null, 2)}</pre>
                </details>
                <button type="button" onClick={() => void save(draft)}>
                  Guardar plantilla revisada
                </button>
              </section>
            )}
            {undo && (
              <button
                type="button"
                onClick={() => void save(undo, "Deshacer último cambio de plantilla revisado")}
              >
                Deshacer último cambio
              </button>
            )}
          </fieldset>
        )
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

import { StatusBadge } from "../../ui/StatusBadge";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { aiSettingsGet, aiSettingsSave, aiConnectionTest } from "../../api/generated/dekopen";
import type { AiRouteStatus, AiSettings } from "../../api/generated/models";
import { formatDecimal, formatDateTime } from "../../format";
import { parseMoneyInput } from "../money";
import {
  Button,
  DeniedState,
  DimLoader,
  ErrorState,
  Skeleton,
  UnknownValue,
  ValidatedForm,
} from "../../ui";
import { AI_CAPABILITIES } from "./providerLabels";
import { AiCost } from "./AiCost";
import "./providerOperations.css";

const PROVIDERS = {
  MIMO: "MiMo (Primalabs)",
  OPENAI: "OpenAI",
  OPENROUTER: "OpenRouter",
  DEEPSEEK: "DeepSeek",
  QWEN: "Qwen",
  MOCK: "Modo de prueba",
};
const STATES = {
  CONNECTED: "Conectado",
  MISSING_CREDENTIAL: "Sin credencial",
  ERROR: "Error",
  UNTESTED: "No probado",
};
function publicDetail(error: unknown, fallback: string): string {
  if (
    !(error instanceof ApiError) ||
    typeof error.payload !== "object" ||
    !error.payload ||
    !("error" in error.payload)
  )
    return fallback;
  const body = error.payload.error;
  return typeof body === "object" && body && "detail" in body && typeof body.detail === "string"
    ? body.detail
    : fallback;
}
type Editable = AiRouteStatus & { inputRate: string; outputRate: string };

export function AiSettingsSection({ orgId }: { orgId: string }): JSX.Element {
  const client = useQueryClient();
  const options = { headers: { "X-Organization-ID": orgId } };
  const [routes, setRoutes] = useState<Editable[]>([]);
  const [budget, setBudget] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState<"save" | "probe" | null>(null);
  const [notice, setNotice] = useState<{ text: string; error?: boolean; credits?: number } | null>(
    null,
  );
  const query = useQuery({
    queryKey: ["ai", "settings", orgId],
    queryFn: async ({ signal }) => {
      const response = await aiSettingsGet({ ...options, signal });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  useEffect(() => {
    if (!query.data || dirty) return;
    setRoutes(
      query.data.routes.map((route) => ({
        ...route,
        inputRate:
          route.input_usd_per_million === null ? "" : formatDecimal(route.input_usd_per_million, 8),
        outputRate:
          route.output_usd_per_million === null
            ? ""
            : formatDecimal(route.output_usd_per_million, 8),
      })),
    );
    setBudget(
      query.data.usage.monthly_budget_credits === null
        ? ""
        : String(query.data.usage.monthly_budget_credits),
    );
  }, [query.data, dirty]);

  function change(index: number, patch: Partial<Editable>): void {
    setDirty(true);
    setNotice(null);
    setRoutes((current) =>
      current.map((route, i) => (i === index ? { ...route, ...patch } : route)),
    );
  }

  async function save(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!query.data) return;
    const limit =
      budget.trim() === ""
        ? null
        : /^\d+$/.test(budget) && Number(budget) <= 2147483647
          ? Number(budget)
          : NaN;
    const normalized = routes.map((route) => ({
      capability: route.capability,
      provider: route.provider,
      provider_model: route.provider_model.trim(),
      timeout_s: route.timeout_s,
      retries: route.retries,
      tools_mode: route.tools_mode,
      input_usd_per_million:
        route.inputRate.trim() === "" ? null : parseMoneyInput(route.inputRate, 8),
      output_usd_per_million:
        route.outputRate.trim() === "" ? null : parseMoneyInput(route.outputRate, 8),
    }));
    if (
      Number.isNaN(limit) ||
      normalized.some(
        (route, i) =>
          !route.provider_model ||
          (route.input_usd_per_million === null) !== (route.output_usd_per_million === null) ||
          (routes[i]!.inputRate.trim() !== "" && route.input_usd_per_million === null) ||
          (routes[i]!.outputRate.trim() !== "" && route.output_usd_per_million === null),
      )
    ) {
      setNotice({
        text: "Revisa el modelo y el presupuesto. Declara ambas tarifas en USD con coma decimal, o deja ambas sin dato.",
        error: true,
      });
      return;
    }
    setBusy("save");
    setNotice(null);
    try {
      const response = await aiSettingsSave(
        {
          expected_revision: query.data.revision,
          monthly_budget_credits: limit,
          routes: normalized,
        },
        options,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setDirty(false);
      client.setQueryData<AiSettings>(["ai", "settings", orgId], response.data);
      await client.invalidateQueries({ queryKey: ["ai", "mode", orgId] });
      setNotice({
        text: "Ajustes de IA guardados.",
      });
    } catch (error) {
      setNotice({
        text: publicDetail(
          error,
          "No se pudieron guardar los ajustes. Revisa la conexión y vuelve a intentar.",
        ),
        error: true,
      });
    } finally {
      setBusy(null);
    }
  }

  async function probe(): Promise<void> {
    setBusy("probe");
    setNotice(null);
    try {
      const response = await aiConnectionTest(
        { operation_key: `connection:${crypto.randomUUID()}` },
        options,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setNotice({
        text: `${response.data.test_mode ? "Modo de prueba: " : "Conexión verificada: "}la propuesta superó el caso mínimo de medidas y la validación del motor.`,
        credits: response.data.credits_debited,
      });
    } catch (error) {
      setNotice({
        text: publicDetail(
          error,
          "No se pudo verificar la conexión. Reintenta y revisa la configuración del proveedor.",
        ),
        error: true,
      });
    } finally {
      await client.invalidateQueries({ queryKey: ["ai", "settings", orgId] });
      setBusy(null);
    }
  }

  return (
    <section
      className="settings-group ai-settings"
      data-density="office"
      aria-labelledby="settings-ai-title"
      id="inteligencia-artificial"
    >
      <h2 className="settings-group__title" id="settings-ai-title">
        Inteligencia artificial
      </h2>
      {query.isPending ? (
        <>
          <Skeleton lines={4} />
          <DimLoader label="Consultando la configuración de IA" />
        </>
      ) : query.error instanceof ApiError && query.error.status === 403 ? (
        <DeniedState reason="Solo el dueño con verificación en dos pasos puede configurar la IA. Pídele que revise estos ajustes." />
      ) : query.isError ? (
        <ErrorState
          title="No se pudieron cargar los ajustes de IA"
          body="Revisa la conexión para consultar el proveedor y el consumo."
          onRetry={() => void query.refetch()}
        />
      ) : query.data ? (
        <>
          <p className="settings-hint">
            La credencial se configura en el servidor. Aquí solo se indica si está disponible.
          </p>
          <ValidatedForm onSubmit={(event) => void save(event)}>
            <div className="ai-routes">
              {routes.map((route, index) => (
                <section
                  className="ai-route"
                  key={route.capability}
                  aria-labelledby={`ai-${route.capability}`}
                >
                  <div className="ai-route-heading">
                    <h3 id={`ai-${route.capability}`}>{AI_CAPABILITIES[route.capability]}</h3>
                    <StatusBadge
                      showIcon={false}
                      className="status-chip"
                      data-status={
                        route.state === "CONNECTED"
                          ? "succeeded"
                          : route.state === "ERROR"
                            ? "failed"
                            : "queued"
                      }
                    >
                      {STATES[route.state]}
                    </StatusBadge>
                    {route.test_mode && (
                      <StatusBadge showIcon={false} className="status-chip">
                        Modo de prueba
                      </StatusBadge>
                    )}
                  </div>
                  <div className="ai-route-fields">
                    <label>
                      Proveedor
                      <select
                        value={route.provider}
                        onChange={(event) =>
                          change(index, {
                            provider: event.target.value as AiRouteStatus["provider"],
                          })
                        }
                      >
                        {Object.entries(PROVIDERS)
                          .filter(([key]) => key !== "MOCK" || query.data!.mock_available)
                          .map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                      </select>
                    </label>
                    <label>
                      Modelo
                      <input
                        value={route.provider_model}
                        maxLength={120}
                        onChange={(event) => change(index, { provider_model: event.target.value })}
                      />
                    </label>
                  </div>
                  <p className="settings-hint">
                    Credencial {route.credential_configured ? "configurada" : "no configurada"} ·{" "}
                    <span className="ai-number">
                      {formatDecimal(route.credits_cost, 0)} créditos
                    </span>{" "}
                    por llamada.
                  </p>
                  {route.state === "MISSING_CREDENTIAL" && (
                    <p className="ai-requires-person">
                      El dueño debe configurar la credencial y la dirección segura de este proveedor
                      en el servidor. Después, prueba la conexión.
                    </p>
                  )}
                  {route.last_cause && (
                    <p role="status" className="ai-requires-person">
                      {route.last_cause}
                    </p>
                  )}
                  {route.checked_at && (
                    <p className="settings-hint">
                      Última respuesta:{" "}
                      <time className="ai-number" dateTime={route.checked_at}>
                        {formatDateTime(route.checked_at)}
                      </time>
                      .
                    </p>
                  )}
                  <details className="ai-advanced">
                    <summary>Tiempo, herramientas y tarifa</summary>
                    <div className="ai-route-fields">
                      <label>
                        Tiempo máximo (s)
                        <input
                          className="ai-number"
                          type="number"
                          min={1}
                          max={180}
                          value={route.timeout_s}
                          onChange={(event) =>
                            change(index, { timeout_s: Number(event.target.value) })
                          }
                        />
                      </label>
                      <label>
                        Reintentos transitorios
                        <select
                          value={route.retries}
                          onChange={(event) =>
                            change(index, { retries: Number(event.target.value) })
                          }
                        >
                          {[0, 1, 2].map((count) => (
                            <option key={count} value={count}>
                              {count}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Herramientas
                        <select
                          value={route.tools_mode}
                          onChange={(event) =>
                            change(index, {
                              tools_mode: event.target.value as AiRouteStatus["tools_mode"],
                            })
                          }
                        >
                          <option value="AUTO">Automático con respaldo validado</option>
                          <option value="NATIVE">Nativas del proveedor</option>
                          <option value="JSON">JSON validado</option>
                        </select>
                      </label>
                      <label>
                        Tarifa de entrada (USD / millón de tokens)
                        <input
                          inputMode="decimal"
                          value={route.inputRate}
                          onChange={(event) => change(index, { inputRate: event.target.value })}
                          placeholder="Sin dato"
                        />
                      </label>
                      <label>
                        Tarifa de salida (USD / millón de tokens)
                        <input
                          inputMode="decimal"
                          value={route.outputRate}
                          onChange={(event) => change(index, { outputRate: event.target.value })}
                          placeholder="Sin dato"
                        />
                      </label>
                    </div>
                    <p className="settings-hint">
                      Copia la tarifa de tu contrato con el proveedor. La estimación usa los tokens
                      que este informó; las tarifas nuevas no cambian llamadas anteriores.
                    </p>
                  </details>
                </section>
              ))}
            </div>
            <section className="ai-month" aria-labelledby="ai-month-title">
              <h3 id="ai-month-title">Consumo del mes</h3>
              <p className="settings-hint">
                Desde{" "}
                <span className="ai-number">{formatDateTime(query.data.usage.month_start)}</span> ·
                horario de Chile.
              </p>
              {query.data.usage.calls === 0 ? (
                <p>
                  No hay llamadas registradas este mes. Prueba la conexión para iniciar el registro.
                </p>
              ) : (
                <dl className="ai-ledger">
                  <div>
                    <dt>Tokens de entrada</dt>
                    <dd className="ai-number">
                      {query.data.usage.tokens_prompt === null ? (
                        <UnknownValue cause="El registro no contiene todos los tokens del mes" />
                      ) : (
                        formatDecimal(query.data.usage.tokens_prompt, 0)
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Tokens de salida</dt>
                    <dd className="ai-number">
                      {query.data.usage.tokens_completion === null ? (
                        <UnknownValue cause="El registro no contiene todos los tokens del mes" />
                      ) : (
                        formatDecimal(query.data.usage.tokens_completion, 0)
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Costo estimado</dt>
                    <dd>
                      <AiCost value={query.data.usage.estimated_cost_usd} />
                    </dd>
                  </div>
                  <div>
                    <dt>Créditos de solicitudes</dt>
                    <dd className="ai-number">
                      {formatDecimal(query.data.usage.capacity_credits, 0)}
                    </dd>
                  </div>
                  <div>
                    <dt>Créditos cobrados</dt>
                    <dd className="ai-number">
                      {formatDecimal(query.data.usage.credits_debited, 0)}
                    </dd>
                  </div>
                </dl>
              )}
              <p className="settings-hint">
                El presupuesto cuenta las solicitudes en curso y las respuestas del proveedor,
                aunque una propuesta falle después. La billetera cobra los intercambios aceptados
                que quedaron auditados.
              </p>
              <details className="ai-advanced">
                <summary>¿De dónde sale? · Consumo mensual</summary>
                <p>
                  Las solicitudes y los tokens provienen del registro de intercambios con el
                  proveedor desde el primer día del mes en Chile. El costo usa la tarifa declarada
                  al iniciar cada llamada. Los créditos cobrados provienen de la auditoría inmutable
                  de la billetera.
                </p>
                <p>
                  Los débitos anteriores a este registro cuentan en el presupuesto, sin duplicar las
                  llamadas nuevas. Si su medición no está completa, los tokens y el costo del mes
                  quedan sin dato.
                </p>
                <Link to="/jobs?capability=all_ai">Revisar las llamadas del mes</Link>
              </details>
              <label className="ai-budget">
                Presupuesto mensual (créditos de solicitudes)
                <input
                  className="ai-number"
                  inputMode="numeric"
                  value={budget}
                  onChange={(event) => {
                    setDirty(true);
                    setBudget(event.target.value);
                  }}
                  placeholder="Sin límite mensual"
                />
              </label>
              <p className="settings-hint">
                Vacío: sin límite mensual adicional. Cero: bloquea nuevas llamadas; las funciones
                manuales siguen disponibles.
              </p>
              {(query.data.usage.budget_blocked || query.data.usage.budget_notice_at) && (
                <p role="alert" className="ai-requires-person">
                  La IA alcanzó el presupuesto o una solicitud lo excedería. Ajusta el límite y
                  guarda para continuar.
                </p>
              )}
              {query.data.usage.users.length > 0 && (
                <details className="ai-advanced">
                  <summary>Consumo por persona</summary>
                  <ul className="ai-person-list">
                    {query.data.usage.users.map((user) => (
                      <li key={user.user_id}>
                        <span>{user.user_label ?? "Usuario sin nombre disponible"}</span>
                        <span className="ai-number">
                          {formatDecimal(user.capacity_credits, 0)} créditos
                        </span>
                        <AiCost value={user.estimated_cost_usd} />
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </section>
            <div className="ai-settings-actions">
              <Button type="submit" disabled={!dirty || busy !== null}>
                Guardar ajustes de IA
              </Button>
              <Button
                variant="primary"
                disabled={dirty || busy !== null}
                onClick={() => void probe()}
              >
                Probar conexión
              </Button>
              <Link to="/jobs?capability=agent">Ver costo y traza de trabajos</Link>
            </div>
            {busy && (
              <DimLoader
                label={
                  busy === "probe"
                    ? "Probando una propuesta con el motor"
                    : "Guardando ajustes de IA"
                }
              />
            )}
            {notice && (
              <p
                role={notice.error ? "alert" : "status"}
                className={notice.error ? "form-error" : "settings-hint"}
              >
                {notice.text}
                {notice.credits !== undefined && (
                  <>
                    {" "}
                    Consumió <span className="ai-number">
                      {formatDecimal(notice.credits, 0)}
                    </span>{" "}
                    créditos.
                  </>
                )}
              </p>
            )}
          </ValidatedForm>
        </>
      ) : null}
    </section>
  );
}

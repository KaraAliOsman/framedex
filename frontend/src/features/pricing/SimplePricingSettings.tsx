import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import {
  pricingSimplePolicy,
  pricingSaveSimplePolicy,
  pricingSimplePolicyExample,
} from "../../api/generated/dekopen";
import type {
  SimplePolicyResponse,
  SimplePolicyValuesRequest,
  SimplePolicyExampleResponse,
} from "../../api/generated/models";
import { compareDecimal, decimalInputValue, parseDecimalInput } from "../../decimal";
import { formatMoney } from "../../format";
import { Button, DeniedState, ErrorState, LoadingState, ValidatedForm } from "../../ui";
import { actionErrorDetail } from "../errors";
import { PricingRulesSettings } from "./PricingPage";
import "./simple-pricing.css";

type NumericKey =
  "labor_rate" | "installation_rate" | "margin" | "rounding_step" | "waste" | "tax_rate";
type Draft = Omit<SimplePolicyValuesRequest, NumericKey> & Record<NumericKey, string>;
const numericKeys: NumericKey[] = [
  "labor_rate",
  "installation_rate",
  "margin",
  "rounding_step",
  "waste",
  "tax_rate",
];
const percentageKeys = new Set<NumericKey>(["margin", "waste", "tax_rate"]);

// Input presentation only: move the decimal separator without binary arithmetic.
function percentInput(value: string): string {
  const [whole = "0", fraction = ""] = value.split(".");
  const digits = fraction.padEnd(2, "0");
  return decimalInputValue(
    `${BigInt(whole) * 100n + BigInt(digits.slice(0, 2))}.${digits.slice(2) || "0"}`,
  ).replace(".", ",");
}
function fractionInput(value: string): string {
  const [whole = "0", fraction = ""] = value.split(".");
  const digits = whole.padStart(3, "0");
  return decimalInputValue(`${digits.slice(0, -2)}.${digits.slice(-2)}${fraction}`);
}
function toDraft(policy: SimplePolicyResponse): Draft {
  const values: Draft = { ...policy };
  for (const key of numericKeys)
    values[key] = percentageKeys.has(key)
      ? percentInput(policy[key])
      : decimalInputValue(policy[key]).replace(".", ",");
  return values;
}
function parseDraft(draft: Draft): {
  values: SimplePolicyValuesRequest | null;
  errors: Partial<Record<NumericKey, string>>;
} {
  const values: SimplePolicyValuesRequest = {
    currency: draft.currency,
    labor_basis: draft.labor_basis,
    installation_basis: draft.installation_basis,
    use_advanced: draft.use_advanced,
    labor_rate: "",
    installation_rate: "",
    margin: "",
    rounding_step: "",
    waste: "",
    tax_rate: "",
  };
  const errors: Partial<Record<NumericKey, string>> = {};
  for (const key of numericKeys) {
    const percent = percentageKeys.has(key);
    const value = parseDecimalInput(draft[key], percent ? 2 : 4);
    if (value === null || compareDecimal(value, "0") < 0) {
      errors[key] = "Escribe un valor positivo o cero.";
    } else if (
      percent &&
      (compareDecimal(value, "100") > 0 || (key === "margin" && compareDecimal(value, "100") === 0))
    ) {
      errors[key] =
        key === "margin"
          ? "Escribe un porcentaje menor que 100."
          : "Escribe un porcentaje de hasta 100.";
    } else if (key === "rounding_step" && compareDecimal(value, "0") === 0) {
      errors[key] = "El redondeo debe ser mayor que cero.";
    } else if (!percent && compareDecimal(value, "9999999999.9999") > 0) {
      errors[key] = "El importe supera el máximo permitido.";
    } else {
      values[key] = percent ? fractionInput(value) : value;
    }
  }
  return { values: Object.keys(errors).length ? null : values, errors };
}

function Example({
  orgId,
  values,
}: {
  orgId: string;
  values: SimplePolicyValuesRequest | null;
}): JSX.Element {
  const key = JSON.stringify(values);
  const [result, setResult] = useState<{
    key: string;
    data?: SimplePolicyExampleResponse;
    error?: string;
  }>();
  useEffect(() => {
    if (!values || values.use_advanced) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const response = await pricingSimplePolicyExample(
            { values },
            {
              headers: { "X-Organization-ID": orgId },
              signal: controller.signal,
            },
          );
          if (response.status !== 200) throw new ApiError(response.status, response.data);
          if (!controller.signal.aborted) setResult({ key, data: response.data });
        } catch (error) {
          if (!controller.signal.aborted)
            setResult({
              key,
              error: actionErrorDetail(
                error,
                "No se pudo calcular el ejemplo. Revisa los precios de la serie y vuelve a intentar.",
              ),
            });
        }
      })();
    }, 180);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [key, orgId, values]);
  if (values?.use_advanced)
    return (
      <aside className="simple-pricing__example">
        <h3>Precio avanzado</h3>
        <p>
          Las obras usarán tus listas, recargos y reglas de aprobación al guardar esta
          configuración.
        </p>
      </aside>
    );
  const current = result?.key === key ? result : undefined;
  const data = current?.data;
  return (
    <aside className="simple-pricing__example" aria-label="Ejemplo de precio">
      <h3>Así queda una ventana</h3>
      <p>Una unidad de una ventana de tu obra, con sus materiales y medidas reales.</p>
      {!values ? (
        <p role="status">Completa los valores para calcular el ejemplo.</p>
      ) : current === undefined ? (
        <p role="status">Calculando precio…</p>
      ) : current.error ? (
        <p role="alert">{current.error}</p>
      ) : data?.breakdown == null ? (
        <>
          <p>{data?.detail}</p>
          <Link to="/projects">Crear una ventana</Link>
        </>
      ) : (
        <>
          <p>
            Ventana {data.position_index} · {data.currency}
          </p>
          <dl className="simple-pricing__breakdown">
            {(
              [
                ["Materiales", data.breakdown.materials],
                ["Merma de materiales", data.breakdown.waste],
                ["Mano de obra", data.breakdown.labor],
                ["Instalación", data.breakdown.installation],
                ["Accesorios y otros servicios", data.breakdown.extras_cost],
                ["Costo total", data.breakdown.direct_cost],
                ["Utilidad", data.breakdown.profit],
              ] as const
            ).map(([label, amount]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{formatMoney(amount, data.currency)}</dd>
              </div>
            ))}
            <div className="simple-pricing__net">
              <dt>Precio neto</dt>
              <dd>{formatMoney(data.project_net, data.currency)}</dd>
            </div>
            <div>
              <dt>IVA</dt>
              <dd>{formatMoney(data.project_tax, data.currency)}</dd>
            </div>
            <div className="simple-pricing__total">
              <dt>Total con IVA</dt>
              <dd>{formatMoney(data.project_gross, data.currency)}</dd>
            </div>
          </dl>
          <p className="simple-pricing__note">
            La utilidad incluye {formatMoney(data.breakdown.rounding, data.currency)} de redondeo.
            Calculado por el motor. Margen sobre venta: {percentInput(values.margin)} %. Los
            materiales usan los datos vigentes de la serie; los sugeridos conservan ese origen.
          </p>
        </>
      )}
    </aside>
  );
}

function PolicyForm({
  orgId,
  initial,
  reload,
}: {
  orgId: string;
  initial: SimplePolicyResponse;
  reload(): void;
}): JSX.Element {
  const client = useQueryClient();
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(() => toDraft(initial));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [failed, setFailed] = useState(false);
  const parsed = useMemo(() => parseDraft(draft), [draft]);
  function set<K extends keyof Draft>(key: K, value: Draft[K]): void {
    setDraft((previous) => ({ ...previous, [key]: value }));
    setMessage("");
  }
  function amount(key: NumericKey, label: string, suffix: string): JSX.Element {
    return (
      <label className="ui-field">
        <span>{label}</span>
        <div className="simple-pricing__input">
          <input
            aria-label={label}
            inputMode="decimal"
            value={draft[key]}
            maxLength={24}
            required
            aria-invalid={parsed.errors[key] ? true : undefined}
            aria-describedby={parsed.errors[key] ? `price-${key}-error` : undefined}
            onChange={(event) => set(key, event.target.value)}
          />
          <span>{suffix}</span>
        </div>
        {parsed.errors[key] && (
          <span className="simple-pricing__error" id={`price-${key}-error`}>
            {parsed.errors[key]}
          </span>
        )}
      </label>
    );
  }
  return (
    <>
      <div className="simple-pricing__layout">
        <ValidatedForm
          className="simple-pricing__form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!parsed.values || busy) return;
            setBusy(true);
            setMessage("");
            setFailed(false);
            void (async () => {
              try {
                const response = await pricingSaveSimplePolicy(
                  {
                    values: parsed.values!,
                    expected_revision: saved.revision,
                    reason: "Configuración de precios de mi empresa",
                  },
                  { headers: { "X-Organization-ID": orgId } },
                );
                if (response.status !== 200) throw new ApiError(response.status, response.data);
                setSaved(response.data);
                setDraft(toDraft(response.data));
                client.setQueryData(["simple-pricing-policy", orgId], response.data);
                await client.invalidateQueries({
                  predicate: (query) =>
                    query.queryKey.includes(orgId) && query.queryKey.includes("project"),
                });
                setMessage(
                  "Precios guardados. Las obras en borrador usarán esta configuración al abrirlas. Las cotizaciones emitidas conservan su precio.",
                );
              } catch (error) {
                setFailed(true);
                setMessage(
                  actionErrorDetail(
                    error,
                    "No se guardaron tus precios. Revisa la conexión y vuelve a intentar.",
                  ),
                );
              } finally {
                setBusy(false);
              }
            })();
          }}
        >
          {!saved.saved && (
            <p className="simple-pricing__suggested">
              Valores sugeridos. Ajústalos a tu taller antes de guardar.
            </p>
          )}
          <p>
            Materiales a los precios de tu serie, más trabajo e instalación, con el margen que
            elijas.
          </p>
          <fieldset disabled={busy}>
            <legend>Servicios del taller</legend>
            <div className="simple-pricing__service">
              {amount("labor_rate", "Mano de obra", draft.currency)}
              <label className="ui-field">
                <span>Cobrar mano de obra</span>
                <select
                  aria-label="Cobrar mano de obra"
                  value={draft.labor_basis}
                  onChange={(event) =>
                    set("labor_basis", event.target.value as Draft["labor_basis"])
                  }
                >
                  <option value="M2">Por m²</option>
                  <option value="WINDOW">Por ventana</option>
                </select>
              </label>
            </div>
            <div className="simple-pricing__service">
              {amount("installation_rate", "Instalación", draft.currency)}
              <label className="ui-field">
                <span>Cobrar instalación</span>
                <select
                  aria-label="Cobrar instalación"
                  value={draft.installation_basis}
                  onChange={(event) =>
                    set("installation_basis", event.target.value as Draft["installation_basis"])
                  }
                >
                  <option value="M2">Por m²</option>
                  <option value="WINDOW">Por ventana</option>
                </select>
              </label>
            </div>
            <p className="simple-pricing__note">
              Una instalación ya agregada como servicio de obra se cobra una sola vez.
            </p>
          </fieldset>
          <fieldset disabled={busy}>
            <legend>Del costo al precio</legend>
            <div className="simple-pricing__service">
              {amount("margin", "Margen sobre venta", "%")}
              {amount("rounding_step", "Redondear hacia arriba a múltiplos de", draft.currency)}
            </div>
            <p className="simple-pricing__note">
              El margen es la parte del precio neto que queda como utilidad. El redondeo conserva
              ese margen.
            </p>
            <details>
              <summary>Merma, IVA y moneda</summary>
              <div className="simple-pricing__service">
                {amount("waste", "Merma de materiales", "%")}
                {amount("tax_rate", "IVA", "%")}
              </div>
              <label className="ui-field">
                <span>Moneda de los precios</span>
                <select
                  value={draft.currency}
                  onChange={(event) => set("currency", event.target.value as Draft["currency"])}
                >
                  <option value="CLP">Peso chileno (CLP)</option>
                  <option value="USD">Dólar (USD)</option>
                </select>
              </label>
            </details>
          </fieldset>
          <label className="simple-pricing__toggle">
            <input
              type="checkbox"
              role="switch"
              checked={draft.use_advanced}
              disabled={busy}
              onChange={(event) => set("use_advanced", event.target.checked)}
            />
            <span>Usar precios avanzados</span>
          </label>
          <p className="simple-pricing__note">
            Activa listas con vigencia, recargos por color, matrices y aprobación de descuentos.
          </p>
          {message && <p role={failed ? "alert" : "status"}>{message}</p>}
          <div className="simple-pricing__actions">
            <Button type="submit" variant="primary" loading={busy} disabled={!parsed.values}>
              Guardar mis precios
            </Button>
            {failed && <Button onClick={reload}>Recargar configuración</Button>}
          </div>
        </ValidatedForm>
        <Example orgId={orgId} values={parsed.values} />
      </div>
      {saved.use_advanced && (
        <section className="simple-pricing__advanced">
          <h3>Configuración avanzada</h3>
          <p>
            <Link to="/pricing/cost-lists">Abrir listas, tarifas y recargos</Link>
          </p>
          <PricingRulesSettings orgId={orgId} />
        </section>
      )}
    </>
  );
}

export function SimplePricingSettings({
  orgId,
  owner,
}: {
  orgId: string;
  owner: boolean;
}): JSX.Element {
  const [version, setVersion] = useState(0);
  const query = useQuery({
    queryKey: ["simple-pricing-policy", orgId],
    enabled: owner,
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await pricingSimplePolicy({
        headers: { "X-Organization-ID": orgId },
        signal,
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  if (!owner)
    return (
      <DeniedState reason="El dueño configura los costos, el margen y la forma de calcular los precios de la empresa." />
    );
  return (
    <section className="settings-card simple-pricing" aria-labelledby="simple-pricing-title">
      <h2 id="simple-pricing-title">Cómo calculo mis precios</h2>
      {query.isPending ? (
        <LoadingState label="Cargando mis precios" />
      ) : query.isError ? (
        <ErrorState
          body={actionErrorDetail(query.error, "No se pudo consultar la configuración de precios.")}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <PolicyForm
          key={`${orgId}:${version}`}
          orgId={orgId}
          initial={query.data}
          reload={() => {
            void query.refetch().then((result) => {
              if (result.isSuccess) setVersion((previous) => previous + 1);
            });
          }}
        />
      )}
    </section>
  );
}

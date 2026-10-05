import { type ReactNode, useState } from "react";
import {
  type DecimalValue,
  formatDate,
  formatDateTime,
  formatDecimal,
  formatMoney,
  formatPercent,
  formatRelativeTimestamp,
} from "../decimal";
import { UnknownValue } from "./Signature";

function Value({
  text,
  unit,
  cause,
}: {
  text: string;
  unit?: string;
  cause?: string;
}): JSX.Element {
  if (text === "Sin dato") return <UnknownValue cause={cause} />;
  return (
    <span className="ui-value">
      {text}
      {unit ? (
        <>
          {" "}
          <span className="ui-value__unit">{unit}</span>
        </>
      ) : null}
    </span>
  );
}
type ScalarProps = { value: DecimalValue; cause?: string };
export function Money({
  value,
  currency = "CLP",
  cause,
}: ScalarProps & { currency?: string }): JSX.Element {
  return <Value text={formatMoney(value, currency)} cause={cause} />;
}
export function Dims({
  w,
  h,
  precision = 0,
  cause,
}: {
  w: DecimalValue;
  h: DecimalValue;
  precision?: number;
  cause?: string;
}): JSX.Element {
  const width = formatDecimal(w, precision),
    height = formatDecimal(h, precision);
  return (
    <Value
      text={width === "Sin dato" || height === "Sin dato" ? "Sin dato" : `${width} × ${height}`}
      unit="mm"
      cause={cause}
    />
  );
}
export function Length({
  mm,
  precision = 0,
  cause,
}: {
  mm: DecimalValue;
  precision?: number;
  cause?: string;
}): JSX.Element {
  return <Value text={formatDecimal(mm, precision)} unit="mm" cause={cause} />;
}
export function Area({ m2, cause }: { m2: DecimalValue; cause?: string }): JSX.Element {
  return <Value text={formatDecimal(m2, 2)} unit="m²" cause={cause} />;
}
export function Weight({ kg, cause }: { kg: DecimalValue; cause?: string }): JSX.Element {
  return <Value text={formatDecimal(kg, 1)} unit="kg" cause={cause} />;
}
export function Uvalue({ value, cause }: ScalarProps): JSX.Element {
  return <Value text={formatDecimal(value, 2)} unit="W/m²K" cause={cause} />;
}
export function Qty({
  value,
  unit = "un.",
  precision = 0,
  cause,
}: ScalarProps & { unit?: string; precision?: number }): JSX.Element {
  return <Value text={formatDecimal(value, precision)} unit={unit} cause={cause} />;
}
export function Percent({
  value,
  kind,
  cause,
}: ScalarProps & { kind: "fraction" | "points" }): JSX.Element {
  return <Value text={formatPercent(value, kind)} cause={cause} />;
}
export function DateOnly({ value }: { value: string | null | undefined }): JSX.Element {
  return <Value text={formatDate(value)} />;
}
export function Timestamp({ value }: { value: string | null | undefined }): JSX.Element {
  if (!value || formatDateTime(value) === "Sin dato") return <UnknownValue />;
  return (
    <time className="ui-value" dateTime={value} title={formatDateTime(value)}>
      {formatRelativeTimestamp(value)}
    </time>
  );
}

export function EntityCode({
  kind,
  code,
}: {
  kind: string;
  code: string | null | undefined;
}): JSX.Element {
  const [feedback, setFeedback] = useState<ReactNode>(null);
  if (!code) return <UnknownValue cause={`Todavía no se asignó el código de ${kind}`} />;
  async function copy(): Promise<void> {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(code!);
      setFeedback("Código copiado");
    } catch {
      setFeedback(
        <label className="ui-code__fallback">
          Selecciona y copia el código
          <input
            aria-label={`Código de ${kind} para copiar`}
            readOnly
            value={code!}
            onFocus={(event) => event.target.select()}
          />
        </label>,
      );
    }
  }
  return (
    <span className="ui-code">
      <button
        className="ui-code__button ui-value"
        type="button"
        title={`Copiar código de ${kind}`}
        onClick={() => void copy()}
      >
        {code}
      </button>
      {feedback ? <span role="status">{feedback}</span> : null}
    </span>
  );
}

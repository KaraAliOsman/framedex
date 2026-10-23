import { type HTMLAttributes, type ReactNode, useId } from "react";
import { Popover } from "./Overlays";
import { Button } from "./Controls";
import { Icon } from "./Icon";

/** Local, stable waiting state (constitution §3.5). The composition does not
 * move: a small activity mark beside the real task name. A bar appears only
 * when the caller knows the real progress; there is never an invented
 * percentage. */
export function Loading({
  label = "Cargando",
  progress,
  detail,
  quiet = false,
}: {
  label?: string;
  /** 0–100, only when the backend reports measurable progress. */
  progress?: number;
  /** Real step text, e.g. «Página 12 de 40». */
  detail?: string;
  /** Hide the label visually (inside a labelled button). */
  quiet?: boolean;
}): JSX.Element {
  const value = progress === undefined ? undefined : Math.max(0, Math.min(100, progress));
  if (value !== undefined)
    return (
      <span className="ui-loading ui-loading--progress">
        <span className="ui-loading__text">
          <span>{label}</span>
          {detail ? <span className="ui-loading__detail">{detail}</span> : null}
        </span>
        <span
          className="ui-loading__bar"
          role="progressbar"
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(value)}
          aria-valuetext={detail}
        >
          <span style={{ inlineSize: `${value}%` }} />
        </span>
      </span>
    );
  return (
    <span className={`ui-loading${quiet ? " ui-loading--quiet" : ""}`} role="status">
      <svg aria-hidden="true" viewBox="0 0 16 16" className="ui-loading__mark">
        <circle cx="8" cy="8" r="6" />
        <path d="M8 2a6 6 0 0 1 6 6" />
      </svg>
      <span className={quiet ? "sr-only" : "ui-loading__text"}>
        <span>{label}</span>
        {detail ? <span className="ui-loading__detail">{detail}</span> : null}
      </span>
    </span>
  );
}

export function SheetSurface({
  miter = false,
  className = "",
  ...props
}: HTMLAttributes<HTMLElement> & { miter?: boolean }): JSX.Element {
  return <section className={`ui-sheet ${miter ? "sheet-miter" : ""} ${className}`} {...props} />;
}

export function DemoBadge({
  source = "Datos sintéticos; revisa el origen antes de fabricar",
}: {
  source?: string;
}): JSX.Element {
  return (
    <span className="ui-demo" title={source}>
      DEMO
    </span>
  );
}

export function UnknownValue({
  cause = "Este valor todavía no está disponible",
  action,
}: {
  cause?: string;
  action?: ReactNode;
}): JSX.Element {
  return (
    <span className="ui-unknown">
      <span>Falta completar</span>
      <span className="ui-unknown__cause"> · {cause}</span>
      {action ? <span className="ui-unknown__action">{action}</span> : null}
    </span>
  );
}

/** A backend trace, presented verbatim. This component never derives a value. */
export type ValueTrace = {
  formula: string;
  inputs: readonly { label: string; value: string; unit?: string }[];
  authority: string;
  engineVersion: string;
  result?: string;
};

export function TraceButton({
  trace,
  cause,
  compact = false,
}: {
  trace: ValueTrace | null | undefined;
  cause?: string;
  compact?: boolean;
}): JSX.Element {
  const id = useId();
  return (
    <Popover
      label="¿De dónde sale?"
      trigger={
        <Button
          aria-label="¿De dónde sale?"
          title="¿De dónde sale?"
          className={compact ? "price-trace ui-trace-trigger" : "ui-trace-link"}
        >
          {compact ? <Icon name="info" size={16} /> : "¿De dónde sale?"}
        </Button>
      }
    >
      <div id={id} className="ui-trace">
        {trace ? (
          <>
            <p className="ui-trace__formula">{trace.formula}</p>
            <dl>
              {trace.inputs.map((input, index) => (
                <div key={index}>
                  <dt>{input.label}</dt>
                  <dd>
                    {input.value} {input.unit}
                  </dd>
                </div>
              ))}
              <div>
                <dt>Origen</dt>
                <dd>{trace.authority}</dd>
              </div>
              <div>
                <dt>Versión del motor</dt>
                <dd>{trace.engineVersion}</dd>
              </div>
              {trace.result ? (
                <div>
                  <dt>Resultado</dt>
                  <dd>{trace.result}</dd>
                </div>
              ) : null}
            </dl>
          </>
        ) : (
          <UnknownValue cause={cause ?? "El backend no adjuntó una traza a este valor"} />
        )}
      </div>
    </Popover>
  );
}

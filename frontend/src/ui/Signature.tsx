import { type HTMLAttributes, type ReactNode, useEffect, useId, useState } from "react";
import { Popover } from "./Overlays";
import { Button } from "./Controls";

export function DimLoader({
  label = "Midiendo el avance",
  progress,
}: {
  label?: string;
  progress?: number;
}): JSX.Element {
  const value = progress === undefined ? undefined : Math.max(0, Math.min(100, progress));
  const [drawn, setDrawn] = useState(0);
  useEffect(() => {
    if (value !== undefined) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setDrawn(100);
      return;
    }
    const timer = window.setInterval(
      () => setDrawn((current) => (current >= 100 ? 0 : current + 20)),
      160,
    );
    return () => clearInterval(timer);
  }, [value]);
  return (
    <span
      className="ui-dim-loader"
      role={value === undefined ? "status" : "progressbar"}
      aria-label={label}
      aria-valuemin={value === undefined ? undefined : 0}
      aria-valuemax={value === undefined ? undefined : 100}
      aria-valuenow={value}
    >
      <svg
        aria-hidden
        viewBox="0 0 100 16"
        className={value === undefined ? "is-indeterminate" : ""}
      >
        <path d="M3 3v10M97 3v10M1 13l4-4M95 13l4-4" />
        <path
          className="ui-dim-loader__measure"
          d="M3 9H97"
          pathLength="100"
          strokeDasharray="100"
          strokeDashoffset={100 - (value ?? drawn)}
        />
      </svg>
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
  source = "Datos sintéticos; revisa la autoridad antes de fabricar",
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
  cause = "La fuente todavía no entregó este valor",
  action,
}: {
  cause?: string;
  action?: ReactNode;
}): JSX.Element {
  return (
    <span className="ui-unknown">
      <span>Sin dato</span>
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
        <Button aria-label="¿De dónde sale?" className={compact ? "price-trace" : undefined}>
          {compact ? <span aria-hidden>?</span> : "¿De dónde sale?"}
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
                <dt>Autoridad</dt>
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

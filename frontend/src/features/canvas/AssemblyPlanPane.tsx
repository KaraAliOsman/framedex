import { useEffect, useRef, useState, type ComponentProps } from "react";
import { fmtMm } from "../../format";
import { BowPlanSvg } from "./BowPlanSvg";
import { Popover } from "../../ui/Overlays";
import type { ProductIssue } from "../../api/generated/models";

export function AssemblyPlanPane({
  onHide,
  preview,
  pending,
  onReviewIssue,
  issueLabel,
  ...props
}: ComponentProps<typeof BowPlanSvg> & {
  onHide(): void;
  preview: boolean;
  pending: boolean;
  onReviewIssue(issue: ProductIssue): void;
  issueLabel(issue: ProductIssue): string;
}) {
  const [height, setHeight] = useState(260),
    ref = useRef<HTMLDivElement>(null),
    detach = useRef<(() => void) | null>(null);
  useEffect(() => () => detach.current?.(), []);
  const issues = props.issues.filter(
    (issue) =>
      issue.target.startsWith("coupling:") ||
      issue.code === "assembly_folds_back" ||
      issue.code === "plan_self_intersection",
  );
  return (
    <section
      ref={ref}
      className="assembly-plan-pane"
      style={{ height }}
      aria-label="Planta acoplada"
    >
      <div
        className="plan-resize"
        role="separator"
        aria-label="Altura de planta"
        aria-orientation="horizontal"
        aria-valuemin={144}
        aria-valuemax={320}
        aria-valuenow={height}
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "ArrowUp" || event.key === "ArrowDown") {
            event.preventDefault();
            setHeight((current) =>
              Math.max(144, Math.min(320, current + (event.key === "ArrowUp" ? 16 : -16))),
            );
          }
        }}
        onPointerDown={(event) => {
          event.preventDefault();
          detach.current?.();
          const start = event.clientY,
            initial = height,
            id = event.pointerId;
          const move = (next: PointerEvent) => {
            if (next.pointerId === id)
              setHeight(Math.max(144, Math.min(320, initial + start - next.clientY)));
          };
          const stop = () => {
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", stop);
            window.removeEventListener("pointercancel", stop);
            detach.current = null;
          };
          detach.current = stop;
          window.addEventListener("pointermove", move);
          window.addEventListener("pointerup", stop);
          window.addEventListener("pointercancel", stop);
        }}
      />
      <header>
        <h3>Planta acoplada</h3>
        <span role="status">
          {preview
            ? pending
              ? "Calculando arrastre…"
              : "Vista previa de ángulo"
            : "Arrastra el módulo o edita la unión"}
        </span>
        <button type="button" onClick={onHide}>
          Ocultar planta
        </button>
      </header>
      <BowPlanSvg {...props} />
      {props.couplings.some((joint) => joint.kind === "STACKED") && (
        <div
          className="plan-stacked-modules"
          role="group"
          aria-label="Seleccionar módulos apilados"
        >
          {props.modules?.map((module, index) => (
            <button
              key={module.id}
              type="button"
              aria-pressed={props.selectedModuleId === module.id}
              onClick={() => props.onSelectModule(module.id)}
            >
              M{index + 1} · {fmtMm(module.width_mm)} × {fmtMm(module.height_mm)} mm
            </button>
          ))}
        </div>
      )}
      <div className="assembly-measures">
        {props.measures ? (
          <Popover
            label="Fuente de las cotas de conjunto"
            trigger={
              <button type="button" className="assembly-measures-source">
                <span>
                  Ancho desarrollado <strong>{fmtMm(props.measures.developed_width_mm)} mm</strong>
                </span>
                <span>
                  Frente / cuerda <strong>{fmtMm(props.measures.front_width_mm)} mm</strong>
                </span>
                <span>
                  Proyección <strong>{fmtMm(props.measures.projection_mm)} mm</strong>
                </span>
                <span>
                  Altura <strong>{fmtMm(props.measures.height_mm)} mm</strong>
                </span>
              </button>
            }
          >
            <p>{props.measures.source}</p>
            <p>
              Aporte neto de acoples: {fmtMm(props.measures.coupling_width_mm)} mm. Un pivote
              compartido puede declarar aporte cero y conserva su corte y precio.
            </p>
          </Popover>
        ) : (
          <p>
            {props.issues.some((issue) => issue.severity === "error")
              ? "Sin dato · corrige la unión señalada para obtener cotas válidas del motor."
              : "Sin dato · el catálogo no declara el aporte desarrollado de todos los acoples. Revisa su autoridad."}
          </p>
        )}
      </div>
      {issues.length > 0 && (
        <ul className="plan-errors">
          {issues.map((issue, index) => (
            <li key={index}>
              <button type="button" onClick={() => onReviewIssue(issue)}>
                {issueLabel(issue)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

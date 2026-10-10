import { fmtMm } from "../../format";
import { Button } from "../../ui/Controls";
import { type CncPreviewGeometry, type CncOp, faceLabel, loadingLabels, opLabel } from "./cncTypes";

/** Only viewport projection uses Number. All coordinates come from the motor. */
export function CncMemberDrawing({
  preview,
  label,
  operations,
  selectedOp,
  onSelectOp,
}: {
  preview: CncPreviewGeometry;
  label: string;
  operations: CncOp[];
  selectedOp: string | null;
  onSelectOp: (id: string) => void;
}) {
  const length = preview.length_mm == null ? NaN : Number(preview.length_mm);
  const validLength = Number.isFinite(length) && length > 0;
  const selected = operations.find((op) => op.operation_id === selectedOp) ?? operations[0];
  const section = preview.section;
  const points = section?.polygon.map((p) => ({ x: Number(p.x_mm), y: Number(p.y_mm) })) ?? [];
  const validSection =
    points.length >= 3 && points.every((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
  const minX = validSection ? Math.min(...points.map((p) => p.x)) : 0;
  const minY = validSection ? Math.min(...points.map((p) => p.y)) : 0;
  const maxX = validSection ? Math.max(...points.map((p) => p.x)) : 0;
  const maxY = validSection ? Math.max(...points.map((p) => p.y)) : 0;
  const span = Math.max(maxX - minX, maxY - minY);
  const endPlane =
    preview.marks.find((m) => m.operation_id === selected?.operation_id)?.section_coverage ===
    "END_PLANE";
  return (
    <figure className="cnc-drawing" data-region="vista-pieza">
      <figcaption>
        <strong>Vista longitudinal · {label}</strong>
        <span>{selected ? faceLabel(selected.face) : "Sin mecanizado emitido"}</span>
      </figcaption>
      {validLength ? (
        <>
          <div className="cnc-drawing-datums">
            <span>Origen inicial · X = 0 mm</span>
            <span>Extremo final · X = {fmtMm(preview.length_mm)} mm</span>
          </div>
          <svg
            viewBox="0 0 900 105"
            role="img"
            aria-label={`Operaciones de ${label}, medidas desde el extremo inicial`}
          >
            <rect className="cnc-outline" x="30" y="40" width="840" height="34" />
            <line className="cnc-axis" x1="30" y1="16" x2="30" y2="92" />
            <line className="cnc-axis" x1="870" y1="16" x2="870" y2="92" />
            {preview.marks.map((mark) => {
              const x = mark.x_mm == null ? NaN : Number(mark.x_mm);
              if (!Number.isFinite(x) || x < 0 || x > length) return null;
              const pixel = 30 + (x / length) * 840;
              return (
                <g
                  key={mark.operation_id}
                  className={
                    selected?.operation_id === mark.operation_id
                      ? "cnc-mark is-selected"
                      : "cnc-mark"
                  }
                  data-x-mm={mark.x_mm}
                >
                  <line x1={pixel} y1="28" x2={pixel} y2="82" />
                  <circle cx={pixel} cy="24" r="7" />
                </g>
              );
            })}
          </svg>
        </>
      ) : (
        <p className="cnc-person">
          Sin dato · falta el largo físico sellado. No se puede ubicar el mecanizado.
        </p>
      )}
      <nav className="cnc-mark-selectors" aria-label={`Elegir operación de ${label}`}>
        {operations.map((op, i) => (
          <Button
            key={op.operation_id}
            aria-pressed={selected?.operation_id === op.operation_id}
            onClick={() => onSelectOp(op.operation_id)}
          >
            <span className="cnc-number">{i + 1}</span> · {opLabel(op.kind)} · X{" "}
            {op.u_mm == null ? "Sin dato" : `${fmtMm(op.u_mm)} mm`}
          </Button>
        ))}
      </nav>
      <div className="cnc-section-view">
        {validSection && span > 0 ? (
          <svg
            viewBox="0 0 200 200"
            role="img"
            aria-label={`Sección sellada de ${label}${endPlane ? ", trabajo sobre plano de extremo" : ""}`}
          >
            <polygon
              className={endPlane ? "cnc-section-polygon has-end-work" : "cnc-section-polygon"}
              points={points
                .map(
                  (p) => `${20 + ((p.x - minX) / span) * 160},${20 + ((p.y - minY) / span) * 160}`,
                )
                .join(" ")}
            />
          </svg>
        ) : null}
        <div>
          <h5>Sección de perfil sellada</h5>
          {section ? (
            <>
              <p>
                {section.synthetic ? "DEMO · sección sintética" : "Sección declarada"} · Fuente:{" "}
                {section.authority_source}
              </p>
              <p>
                Orientación del dibujo:{" "}
                {section.orientation_declared
                  ? (loadingLabels[section.orientation] ?? "Sin dato")
                  : "Sin dato · no fue declarada explícitamente"}
                .
              </p>
              <p>La orientación de carga se revisa por perfil en la máquina.</p>
            </>
          ) : (
            <p className="cnc-person">
              Sin dato · la revisión no selló esta sección. Emite una nueva revisión con el catálogo
              revisado.
            </p>
          )}
          {selected ? (
            <p>
              {endPlane
                ? "Trabajo declarado sobre el plano completo del extremo; no representa una trayectoria de herramienta."
                : "Sin dato · no se declaró Y/Z de herramienta sobre esta sección; se muestra solo la posición longitudinal."}
            </p>
          ) : null}
        </div>
      </div>
    </figure>
  );
}

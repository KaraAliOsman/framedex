import { useRef, useState } from "react";
import type { PortalPosition, PositionDesign } from "../../api/generated/models";
import { PositionThumb, THUMB_MEMBERS } from "../projects/PositionThumb";
import { withFinishMembers } from "../canvas/members";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";
import { Dialog, Dims } from "../../ui";

export function proposalDesign(position: PortalPosition): PositionDesign {
  return {
    system_id: "",
    nominal_width_mm: position.width_mm,
    nominal_height_mm: position.height_mm,
    color: position.color_interior ?? "",
    parametric_tree: position.parametric_tree,
  };
}

export function ProposalThumb({ position }: { position: PortalPosition }): JSX.Element {
  const members = position.resolved_finish
    ? withFinishMembers(THUMB_MEMBERS, position.resolved_finish, "interior")
    : THUMB_MEMBERS;
  return (
    <PositionThumb
      design={proposalDesign(position)}
      members={members}
      openingLeaves={(position.opening_leaves ?? []) as OpeningLeafFact[]}
    />
  );
}

function Drawing({
  position,
  large = false,
}: {
  position: PortalPosition;
  large?: boolean;
}): JSX.Element {
  const [view, setView] = useState<"elevation" | "studio">("elevation");
  const [face, setFace] = useState<"interior" | "exterior">("interior");
  const [pose, setPose] = useState({ scale: 1, x: 0, y: 0 });
  const points = useRef(new Map<number, { x: number; y: number }>());
  const members = position.resolved_finish
    ? withFinishMembers(THUMB_MEMBERS, position.resolved_finish, face)
    : { ...THUMB_MEMBERS, viewFace: face };
  const reset = () => setPose({ scale: 1, x: 0, y: 0 });
  const zoom = (factor: number) =>
    setPose((p) => ({ ...p, scale: Math.max(1, Math.min(4, p.scale * factor)) }));
  return (
    <>
      <div className="portal-drawing-controls" aria-label="Vista del dibujo">
        <button
          type="button"
          aria-pressed={view === "elevation"}
          onClick={() => {
            setView("elevation");
            reset();
          }}
        >
          Técnica
        </button>
        <button
          type="button"
          aria-pressed={view === "studio"}
          onClick={() => {
            setView("studio");
            reset();
          }}
        >
          Comercial
        </button>
        <button
          type="button"
          onClick={() => setFace(face === "interior" ? "exterior" : "interior")}
        >
          Vista {face === "interior" ? "interior" : "exterior"}
        </button>
      </div>
      <div
        className={`portal-drawing ${large ? "portal-drawing--large" : ""}`}
        style={{ touchAction: large || pose.scale > 1 ? "none" : "pan-y" }}
        tabIndex={0}
        role="group"
        aria-label={`Dibujo de posición ${position.position_index}. Use más y menos para ampliar, flechas para desplazar y cero para ajustar.`}
        onKeyDown={(e) => {
          if (
            ["+", "=", "-", "0", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)
          )
            e.preventDefault();
          if (e.key === "+" || e.key === "=") zoom(1.25);
          else if (e.key === "-") zoom(0.8);
          else if (e.key === "0") reset();
          else if (e.key.startsWith("Arrow"))
            setPose((p) => ({
              ...p,
              x: p.x + (e.key === "ArrowLeft" ? 24 : e.key === "ArrowRight" ? -24 : 0),
              y: p.y + (e.key === "ArrowUp" ? 24 : e.key === "ArrowDown" ? -24 : 0),
            }));
        }}
        onPointerDown={(e) => {
          points.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          const old = points.current.get(e.pointerId);
          if (!old) return;
          const other = [...points.current.entries()].find(([id]) => id !== e.pointerId)?.[1];
          if (other) {
            const before = Math.hypot(old.x - other.x, old.y - other.y);
            const after = Math.hypot(e.clientX - other.x, e.clientY - other.y);
            if (before > 0) zoom(after / before);
          } else
            setPose((p) =>
              p.scale > 1 ? { ...p, x: p.x + e.clientX - old.x, y: p.y + e.clientY - old.y } : p,
            );
          points.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
        }}
        onPointerUp={(e) => points.current.delete(e.pointerId)}
        onPointerCancel={(e) => points.current.delete(e.pointerId)}
        onLostPointerCapture={(e) => points.current.delete(e.pointerId)}
      >
        <div
          className="portal-drawing-transform"
          style={{ transform: `translate(${pose.x}px,${pose.y}px) scale(${pose.scale})` }}
        >
          {position.parametric_tree ? (
            <PositionThumb
              design={proposalDesign(position)}
              members={members}
              variant={view}
              openingLeaves={(position.opening_leaves ?? []) as OpeningLeafFact[]}
            />
          ) : (
            <p>Sin dibujo · solicite la definición de esta posición al fabricante.</p>
          )}
        </div>
      </div>
      <div className="portal-drawing-tools">
        <button type="button" onClick={() => zoom(1.25)} aria-label="Ampliar dibujo">
          +
        </button>
        <button type="button" onClick={() => zoom(0.8)} aria-label="Reducir dibujo">
          −
        </button>
        <button type="button" onClick={reset}>
          Ajustar
        </button>
        <Dims w={position.width_mm} h={position.height_mm} />
      </div>
    </>
  );
}

export function ProposalDrawing({ position }: { position: PortalPosition }): JSX.Element {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="portal-drawing-sheet">
      <Drawing position={position} />
      <button type="button" className="portal-expand" onClick={() => setExpanded(true)}>
        Abrir dibujo ampliado
      </button>
      {expanded && (
        <Dialog
          width="l"
          onClose={() => setExpanded(false)}
          title={`Posición ${position.position_index} · ${position.location_tag || "Ubicación sin declarar"}`}
        >
          <Drawing position={position} large />
        </Dialog>
      )}
    </div>
  );
}

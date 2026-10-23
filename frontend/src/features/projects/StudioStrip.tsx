import { useState } from "react";
import { Link } from "react-router-dom";

import type { PositionResponse, ProjectResponse } from "../../api/generated/models";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";
import type { WorkView } from "../../app/workPreferences";
import { fmtMm } from "../../format";
import { Icon } from "../../ui/Icon";
import { PositionThumb } from "./PositionThumb";

/** Textual view selector of the work header: two named choices, the chosen
 * one legible. Switching never saves, recalculates or issues anything. */
export function WorkViewSwitch({
  view,
  onChange,
}: {
  view: WorkView;
  onChange(view: WorkView): void;
}): JSX.Element {
  return (
    <div className="work-view-switch ui-segmented" role="radiogroup" aria-label="Vista de la obra">
      {(
        [
          ["mesa", "Mesa de obra"],
          ["estudio", "Estudio"],
        ] as const
      ).map(([value, label]) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={view === value}
          onClick={() => view !== value && onChange(value)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function positionName(position: PositionResponse): string {
  return position.location_tag || `Ventana ${position.position_index}`;
}

/** Estudio's compact band of positions: name, faithful thumbnail,
 * previous/next and add. It selects the active position; the editing
 * session decides (with Guardar/Descartar/Cancelar) when the drawing changes. */
export function StudioStrip({
  project,
  activeId,
  canAdd,
  onSelect,
  unified = false,
}: {
  project: ProjectResponse;
  activeId: string | null;
  canAdd: boolean;
  onSelect(id: string): void;
  unified?: boolean;
}): JSX.Element {
  // Folded by default below the 1440 composition so the canvas keeps its budget.
  const [collapsed, setCollapsed] = useState(() => (unified ? false : window.innerWidth < 1400));
  const positions = project.positions ?? [];
  const index = positions.findIndex((position) => position.id === activeId);
  const previous = index > 0 ? positions[index - 1] : undefined;
  const next = index >= 0 && index < positions.length - 1 ? positions[index + 1] : undefined;
  return (
    <aside
      className={`studio-strip${unified ? " work-window-list" : ""}`}
      data-collapsed={collapsed || undefined}
      aria-label="Ventanas de la obra"
    >
      <div className="studio-strip__head">
        {!unified && (
          <button
            type="button"
            className="ui-icon-button"
            aria-expanded={!collapsed}
            aria-label={collapsed ? "Mostrar ventanas" : "Plegar ventanas"}
            title={collapsed ? "Mostrar ventanas" : "Plegar ventanas"}
            onClick={() => setCollapsed((value) => !value)}
          >
            <Icon name="sidebar" size={16} />
          </button>
        )}
        {!collapsed ? <strong>Ventanas · {positions.length}</strong> : null}
      </div>
      {!unified && (
        <div className="studio-strip__nav">
          <button
            type="button"
            className="ui-icon-button"
            disabled={!previous}
            aria-label="Ventana anterior"
            title="Ventana anterior"
            onClick={() => previous && onSelect(previous.id)}
          >
            <Icon name="chevronUp" size={16} />
          </button>
          <button
            type="button"
            className="ui-icon-button"
            disabled={!next}
            aria-label="Ventana siguiente"
            title="Ventana siguiente"
            onClick={() => next && onSelect(next.id)}
          >
            <Icon name="chevronDown" size={16} />
          </button>
        </div>
      )}
      {collapsed ? null : (
        <ol className="studio-strip__list" aria-label="Ventanas">
          {positions.map((position) => (
            <li key={position.id}>
              <button
                type="button"
                className="studio-strip__item"
                aria-current={position.id === activeId ? "true" : undefined}
                title={positionName(position)}
                aria-label={`Abrir ${positionName(position)} en el editor`}
                onClick={() => onSelect(position.id)}
              >
                <span className="studio-strip__thumb">
                  <PositionThumb
                    design={position.design}
                    openingLeaves={position.bom?.opening_leaves as OpeningLeafFact[] | undefined}
                  />
                </span>
                <span className="studio-strip__text">
                  <strong>{positionName(position)}</strong>
                  <span className="studio-strip__dims">
                    {fmtMm(position.design.nominal_width_mm)} ×{" "}
                    {fmtMm(position.design.nominal_height_mm)} mm
                  </span>
                  <span className="studio-strip__quantity">{position.quantity} u.</span>
                </span>
              </button>
            </li>
          ))}
        </ol>
      )}
      {canAdd ? (
        <Link
          className="ui-button studio-strip__add"
          to={`/projects/${project.id}/positions/new${unified ? "" : "?view=estudio"}`}
          aria-label="Añadir ventana"
          title="Añadir ventana"
        >
          <Icon name="plus" size={16} />
          {collapsed ? null : <span>Añadir ventana</span>}
        </Link>
      ) : null}
    </aside>
  );
}

import { lazy, Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type {
  PositionResponse,
  ProjectResponse,
  DesignOperationRequest,
} from "../../api/generated/models";
import { fmtMm, formatMoney, parseDecimalInput } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { StatusBadge, EmptyState, Loading, useConfirm } from "../../ui";
import { Icon } from "../../ui/Icon";
import { Menu } from "../../ui/Overlays";
import { PositionThumb } from "./PositionThumb";
import { VirtualPositionRows, type PositionRowEntry } from "./VirtualPositionRows";
import { ProjectOpsReview, useProjectOperations } from "./ProjectOpsReview";
import { QuotationGlobalChanges } from "./QuotationGlobalChanges";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";

const ProjectPositionLibrary = lazy(() =>
  import("./ProjectPositionLibrary").then((module) => ({ default: module.ProjectPositionLibrary })),
);

type Group = "none" | "floor" | "room" | "axis";
type Commercial = { unit_net?: string | null; line_net?: string | null; source?: string };
export function positionGlass(position: PositionResponse): string {
  const values = [
    ...new Set(
      position.bom.glasses.map((glass) => glass.glass_spec || glass.article_sku).filter(Boolean),
    ),
  ];
  return values.join(" · ") || (position.bom.panels.length ? "Panel" : "Sin vidrio");
}
export function positionReadiness(position: PositionResponse): {
  label: string;
  cause: string;
  tone: "success" | "warning" | "danger";
} {
  if (!position.bom)
    return {
      label: "Sin cálculo",
      cause: "Falta un cálculo guardado. Abre el editor y revisa el diseño.",
      tone: "danger",
    };
  const measurement = position.measurements as { current?: boolean; state?: string } | null;
  if (measurement && (!measurement.current || measurement.state !== "CONFIRMED"))
    return {
      label: "Confirmar medidas",
      cause:
        "Revisa y confirma las medidas del vano antes de fabricar. El precio usa la fabricación guardada.",
      tone: "warning",
    };
  if (!position.location_tag)
    return {
      label: "Falta ubicación",
      cause: "Indica dónde va esta ventana (por ejemplo, «Dormitorio») antes de emitir.",
      tone: "warning",
    };
  return {
    label: "Lista",
    cause:
      "Fuente: cálculo guardado del motor. Al preparar la emisión se comprueba que cada ventana se pueda fabricar.",
    tone: "success",
  };
}
function Dimensions({
  position,
  editable,
  busy,
  onPropose,
}: {
  position: PositionResponse;
  editable: boolean;
  busy: boolean;
  onPropose(ops: DesignOperationRequest[], title: string): Promise<unknown>;
}): JSX.Element {
  const [editing, setEditing] = useState(false);
  const [width, setWidth] = useState(position.design.nominal_width_mm);
  const [height, setHeight] = useState(position.design.nominal_height_mm);
  const w = parseDecimalInput(width, 2),
    h = parseDecimalInput(height, 2);
  const label = `${fmtMm(position.design.nominal_width_mm)} × ${fmtMm(position.design.nominal_height_mm)} mm`;
  if (!editable) return <span className="project-number">{label}</span>;
  if (!editing)
    return (
      <button
        type="button"
        className="project-dimension"
        aria-label={`Editar medidas de la ventana ${position.position_index}`}
        title="Cambiar medidas"
        onClick={(event) => {
          event.stopPropagation();
          setWidth(position.design.nominal_width_mm);
          setHeight(position.design.nominal_height_mm);
          setEditing(true);
        }}
      >
        {label}
      </button>
    );
  return (
    <form
      noValidate
      className="project-inline-dims"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
      onSubmit={(event) => {
        event.preventDefault();
        if (!w || !h || busy) return;
        void onPropose(
          [
            {
              op: "apply_to_positions",
              filter: { position_ids: [position.id] },
              ops: [
                { op: "set_total_width", width_mm: w },
                { op: "set_height", height_mm: h },
              ],
            },
          ],
          `Medidas de la posición ${position.position_index}`,
        );
        setEditing(false);
      }}
    >
      <label>
        Ancho (mm)
        <input
          autoFocus
          inputMode="decimal"
          value={width}
          onChange={(event) => setWidth(event.target.value)}
          aria-invalid={!w || undefined}
        />
      </label>
      <span aria-hidden>×</span>
      <label>
        Alto (mm)
        <input
          inputMode="decimal"
          value={height}
          onChange={(event) => setHeight(event.target.value)}
          aria-invalid={!h || undefined}
        />
      </label>
      <button
        type="submit"
        className="ui-button ui-button--primary ui-button--compact"
        disabled={!w || !h || busy}
      >
        Revisar
      </button>
      <button
        type="button"
        className="ui-button ui-button--compact"
        onClick={() => setEditing(false)}
      >
        Cancelar
      </button>
    </form>
  );
}

export function PositionCollection({
  project,
  orgId,
  editable,
  disabled,
  selectedId,
  onSelected,
  onOpen,
  onChanged,
  onImport,
  onDetails,
}: {
  project: ProjectResponse;
  orgId: string;
  editable: boolean;
  disabled: boolean;
  selectedId: string | null;
  onSelected(id: string): void;
  /** Opens the wide editor of a position (the host keeps view and return). */
  onOpen?(id: string): void;
  onChanged(): Promise<unknown>;
  onImport(): void;
  onDetails(): void;
}): JSX.Element {
  const navigate = useNavigate(),
    confirm = useConfirm();
  const [view, setView] = useState<"list" | "grid">(() =>
    (project.positions?.length ?? 0) > 24 ? "list" : "grid",
  );
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [group, setGroup] = useState<Group>("none");
  const [search, setSearch] = useState("");
  const [typology, setTypology] = useState("");
  const [glassFilter, setGlassFilter] = useState("");
  const [checked, setChecked] = useState<string[]>([]);
  const [batch, setBatch] = useState<"quantity" | "location" | "floor" | "room" | "axis">("floor");
  const [batchValue, setBatchValue] = useState("");
  const [library, setLibrary] = useState(false);
  const [global, setGlobal] = useState(false);
  const [columns, setColumns] = useState(3);
  const [scrollTo, setScrollTo] = useState<{ key: string; epoch: number } | null>(null);
  const host = useRef<HTMLDivElement>(null),
    refs = useRef(new Map<string, HTMLDivElement>());
  const focusId = useRef<string | null>(null);
  const operations = useProjectOperations(project, orgId, onChanged);
  const positions = project.positions ?? [];
  const choices = useMemo(() => [...new Set(positions.map(positionGlass))], [positions]);
  const visible = useMemo(
    () =>
      positions.filter(
        (position) =>
          (!typology || position.typology === typology) &&
          (!glassFilter || positionGlass(position) === glassFilter) &&
          `${position.position_index} ${position.location_tag} ${Object.values(position.placement ?? {}).join(" ")} ${positionGlass(position)} ${domainLabel(position.typology)} ${position.system_name ?? ""}`
            .toLocaleLowerCase("es-CL")
            .includes(search.toLocaleLowerCase("es-CL")),
      ),
    [positions, typology, glassFilter, search],
  );
  const ids = checked.filter((id) => positions.some((position) => position.id === id));
  const activeId = visible.some((position) => position.id === selectedId)
    ? selectedId
    : visible[0]?.id;
  const busy = disabled || operations.busy;
  useLayoutEffect(() => {
    const node = host.current;
    if (!node) return;
    const measure = () => setColumns(Math.max(1, Math.floor(node.clientWidth / 296)));
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!focusId.current) return;
    const frame = requestAnimationFrame(() => {
      const node = refs.current.get(focusId.current!);
      if (node) {
        node.focus();
        focusId.current = null;
      }
    });
    return () => cancelAnimationFrame(frame);
  });
  async function remove(targets: string[]): Promise<void> {
    if (!targets.length || !editable || busy) return;
    if (
      await confirm({
        title: `¿Preparar la eliminación de ${targets.length} posiciones?`,
        body: "Verás el detalle antes de aplicar. Puedes deshacer mientras no exista una edición posterior.",
        danger: true,
      })
    )
      await operations.propose(
        [{ op: "remove_positions", position_ids: targets }],
        "Eliminar posiciones seleccionadas",
      );
  }
  function toggle(id: string): void {
    setChecked((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id],
    );
  }
  function reorder(direction: -1 | 1): void {
    const wanted = new Set(ids),
      ordered = positions.map((position) => position.id);
    if (direction < 0)
      for (let index = 1; index < ordered.length; index++) {
        if (wanted.has(ordered[index]!) && !wanted.has(ordered[index - 1]!))
          [ordered[index - 1], ordered[index]] = [ordered[index]!, ordered[index - 1]!];
      }
    else
      for (let index = ordered.length - 2; index >= 0; index--) {
        if (wanted.has(ordered[index]!) && !wanted.has(ordered[index + 1]!))
          [ordered[index], ordered[index + 1]] = [ordered[index + 1]!, ordered[index]!];
      }
    void operations.propose(
      [{ op: "reorder_positions", position_ids: ordered }],
      "Reordenar posiciones; conservar números físicos",
    );
  }
  const rows: PositionRowEntry[] = [];
  const groups = new Map<string, PositionResponse[]>();
  for (const position of visible) {
    const key =
      group === "none"
        ? ""
        : position.placement?.[group] ||
          `Sin ${group === "floor" ? "piso" : group === "room" ? "recinto" : "eje"} · declara la ubicación`;
    groups.set(key, [...(groups.get(key) ?? []), position]);
  }
  const rowForPosition = new Map<string, string>();
  function positionName(position: PositionResponse): string {
    return position.location_tag || `Ventana ${position.position_index}`;
  }
  function finishLabel(position: PositionResponse): string {
    const finish = position.bom?.finish;
    if (!finish) return domainLabel(position.design.color);
    return finish.interior.name === finish.exterior.name
      ? finish.interior.name
      : `${finish.interior.name} / ${finish.exterior.name}`;
  }
  function positionCard(position: PositionResponse): JSX.Element {
    const state = positionReadiness(position),
      sale = position.commercial as Commercial | null;
    const open = () =>
      editable
        ? onOpen
          ? onOpen(position.id)
          : navigate(`/projects/${project.id}/positions/${position.id}/edit`)
        : (onSelected(position.id), onDetails());
    return (
      <div
        role="listitem"
        aria-label={`${positionName(position)} · ${domainLabel(position.typology)}`}
        aria-current={activeId === position.id ? "true" : undefined}
        aria-keyshortcuts="Enter Space Delete ArrowDown ArrowUp Home End"
        aria-posinset={visible.indexOf(position) + 1}
        aria-setsize={visible.length}
        tabIndex={position.id === activeId ? 0 : -1}
        className="position-row"
        data-active={activeId === position.id || undefined}
        data-selected={checked.includes(position.id) || undefined}
        key={position.id}
        ref={(node) => {
          if (node) refs.current.set(position.id, node);
          else refs.current.delete(position.id);
        }}
        onClick={() => onSelected(position.id)}
        onDoubleClick={open}
        onKeyDown={(event) => {
          if (event.target !== event.currentTarget) return;
          if (event.key === "Enter") {
            event.preventDefault();
            open();
          } else if (event.key === " ") {
            event.preventDefault();
            toggle(position.id);
          } else if (event.key === "Delete") {
            event.preventDefault();
            void remove(ids.length ? ids : [position.id]);
          } else if (
            ["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End"].includes(event.key)
          ) {
            event.preventDefault();
            let index = visible.indexOf(position);
            if (event.key === "Home") index = 0;
            else if (event.key === "End") index = visible.length - 1;
            else
              index = Math.max(
                0,
                Math.min(
                  visible.length - 1,
                  index + (["ArrowDown", "ArrowRight"].includes(event.key) ? 1 : -1),
                ),
              );
            const target = visible[index];
            if (target) {
              onSelected(target.id);
              focusId.current = target.id;
              setScrollTo({ key: rowForPosition.get(target.id)!, epoch: Date.now() });
            }
          }
        }}
      >
        <label className="project-position-check" onClick={(event) => event.stopPropagation()}>
          <input
            type="checkbox"
            aria-label={`Seleccionar ${positionName(position)}`}
            checked={checked.includes(position.id)}
            onChange={() => toggle(position.id)}
          />
          <span className="position-row__index">{position.position_index}</span>
        </label>
        <button
          type="button"
          className="position-row__thumb"
          aria-label={
            editable
              ? `Abrir ${positionName(position)} en el editor`
              : `Ver ${positionName(position)}`
          }
          onClick={(event) => {
            event.stopPropagation();
            open();
          }}
        >
          <PositionThumb
            design={position.design}
            openingLeaves={position.bom?.opening_leaves as OpeningLeafFact[] | undefined}
          />
        </button>
        <div className="position-row__identity">
          <strong className="position-row__name">{positionName(position)}</strong>
          <span className="position-row__type">
            {domainLabel(position.typology)}
            {position.system_name ? ` · ${position.system_name}` : ""}
            {position.system_demo && !position.system_name?.includes("DEMO") ? " · DEMO" : ""}
          </span>
          <Dimensions
            position={position}
            editable={editable}
            busy={busy}
            onPropose={operations.propose}
          />
          {/* Gallery summary: what a person reads first, in one calm line. */}
          <span className="position-row__summary" aria-hidden="true">
            <span>
              {finishLabel(position)} · {positionGlass(position)} ·{" "}
              {position.quantity === 1 ? "1 unidad" : `${position.quantity} unidades`}
            </span>
            {sale?.line_net != null ? (
              <strong>{formatMoney(sale.line_net, project.currency)}</strong>
            ) : null}
          </span>
        </div>
        <dl className="position-row__specs">
          <div>
            <dt>Acabado</dt>
            <dd>{finishLabel(position)}</dd>
          </div>
          <div>
            <dt>Vidrio</dt>
            <dd>{positionGlass(position)}</dd>
          </div>
          <div>
            <dt>Cantidad</dt>
            <dd className="is-numeric">{position.quantity}</dd>
          </div>
          <div>
            <dt>Total neto</dt>
            <dd className="is-numeric" title={sale?.source}>
              {sale?.line_net != null ? formatMoney(sale.line_net, project.currency) : "Sin precio"}
            </dd>
          </div>
          {group !== "none" && (
            <div>
              <dt>{group === "floor" ? "Piso" : group === "room" ? "Recinto" : "Eje"}</dt>
              <dd>{position.placement?.[group] || "Sin dato"}</dd>
            </div>
          )}
        </dl>
        <div className="position-row__state">
          {state.tone !== "success" ? (
            <StatusBadge tone={state.tone} title={state.cause}>
              {state.label}
            </StatusBadge>
          ) : null}
        </div>
        {editable ? (
          <div className="position-row__actions" onClick={(event) => event.stopPropagation()}>
            <button
              type="button"
              className="ui-button ui-button--compact position-row__open"
              aria-label={`Abrir ${positionName(position)} en el editor`}
              onClick={open}
            >
              Abrir editor
            </button>
            <button
              type="button"
              className="ui-icon-button"
              aria-label={`Duplicar ${positionName(position)}`}
              title="Duplicar"
              disabled={busy}
              onClick={() =>
                void operations.run(
                  [{ op: "duplicate_positions", position_ids: [position.id] }],
                  `${positionName(position)} duplicada al final de la obra.`,
                )
              }
            >
              <Icon name="copy" />
            </button>
            <button
              type="button"
              className="ui-icon-button"
              aria-label={`Eliminar ${positionName(position)}`}
              title="Eliminar"
              disabled={busy}
              onClick={() => void remove([position.id])}
            >
              <Icon name="trash" />
            </button>
          </div>
        ) : null}
      </div>
    );
  }
  for (const [title, entries] of groups) {
    if (title)
      rows.push({
        key: `group:${title}`,
        estimate: 40,
        content: (
          <h3 className="project-position-group">
            {title} · {entries.length === 1 ? "1 ventana" : `${entries.length} ventanas`}
          </h3>
        ),
      });
    const count = view === "grid" ? columns : 1;
    for (let index = 0; index < entries.length; index += count) {
      const chunk = entries.slice(index, index + count),
        key = chunk[0]!.id;
      chunk.forEach((position) => rowForPosition.set(position.id, key));
      rows.push({
        key,
        estimate: view === "grid" ? 360 : 76,
        content: (
          <div className="project-position-row-group" data-view={view}>
            {chunk.map(positionCard)}
          </div>
        ),
      });
    }
  }
  const filtered = Boolean(search || typology || glassFilter);
  return (
    <div ref={host} className="project-position-collection" data-view={view}>
      <div className="project-positions-toolbar">
        <h2>
          Ventanas <span className="project-positions-count">{positions.length}</span>
        </h2>
        <div className="project-positions-tools">
          {/* A short work needs no search: the cards are the index. */}
          {positions.length > 6 || filtered ? (
            <>
              <label className="project-positions-search">
                <Icon name="search" size={16} />
                <span className="sr-only">Buscar por ubicación, piso, vidrio o tipología</span>
                <input
                  type="search"
                  placeholder="Buscar ventana"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
              <button
                type="button"
                className="ui-button ui-button--compact"
                aria-expanded={filtersOpen}
                onClick={() => setFiltersOpen((value) => !value)}
              >
                <Icon name="filter" size={16} />
                Filtros{filtered ? " · activos" : ""}
              </button>
            </>
          ) : null}
          <div className="ui-segmented project-positions-view" role="radiogroup" aria-label="Vista">
            <button
              type="button"
              role="radio"
              aria-checked={view === "grid"}
              aria-label="Galería"
              title="Galería"
              onClick={() => {
                setView("grid");
                setScrollTo(null);
              }}
            >
              <Icon name="grid" size={16} />
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={view === "list"}
              aria-label="Tabla"
              title="Tabla"
              onClick={() => {
                setView("list");
                setScrollTo(null);
              }}
            >
              <Icon name="list" size={16} />
            </button>
          </div>
          {editable ? (
            <>
              <Menu
                label="Más"
                items={[
                  {
                    id: "library",
                    label: "Agregar varias desde la biblioteca",
                    onSelect: () => setLibrary(true),
                  },
                  { id: "import", label: "Importar planilla o plano", onSelect: onImport },
                  ...(selectedId
                    ? [{ id: "details", label: "Ficha técnica de la ventana", onSelect: onDetails }]
                    : []),
                ]}
              />
              <Link
                className={`ui-button${positions.length ? "" : " ui-button--primary"}`}
                to={`/projects/${project.id}/positions/new`}
              >
                <Icon name="plus" />
                Añadir ventana
              </Link>
            </>
          ) : selectedId ? (
            <button type="button" className="ui-button" onClick={onDetails}>
              Ficha técnica
            </button>
          ) : null}
        </div>
      </div>
      {filtersOpen ? (
        <div className="project-positions-filters">
          <label>
            Agrupar
            <select
              aria-label="Agrupar"
              value={group}
              onChange={(event) => setGroup(event.target.value as Group)}
            >
              <option value="none">Orden de la obra</option>
              <option value="floor">Piso</option>
              <option value="room">Recinto</option>
              <option value="axis">Eje</option>
            </select>
          </label>
          <label>
            Tipología
            <select
              aria-label="Tipología"
              value={typology}
              onChange={(event) => setTypology(event.target.value)}
            >
              <option value="">Todas</option>
              {[...new Set(positions.map((position) => position.typology))].map((value) => (
                <option key={value} value={value}>
                  {domainLabel(value)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Vidrio
            <select
              aria-label="Vidrio"
              value={glassFilter}
              onChange={(event) => setGlassFilter(event.target.value)}
            >
              <option value="">Todos</option>
              {choices.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="project-positions-all">
            <input
              type="checkbox"
              aria-label="Seleccionar ventanas filtradas"
              checked={visible.length > 0 && visible.every((position) => ids.includes(position.id))}
              onChange={(event) =>
                setChecked(
                  event.target.checked
                    ? [...new Set([...ids, ...visible.map((position) => position.id)])]
                    : ids.filter((id) => !visible.some((position) => position.id === id)),
                )
              }
            />
            Seleccionar las {visible.length} visibles
          </label>
        </div>
      ) : null}
      {ids.length > 0 && (
        <section
          className="project-batch-actions"
          aria-label="Acciones sobre las ventanas elegidas"
        >
          <strong>
            {ids.length === 1 ? "1 ventana elegida" : `${ids.length} ventanas elegidas`}
          </strong>
          {(() => {
            const hidden = ids.filter(
              (id) => !visible.some((position) => position.id === id),
            ).length;
            return hidden > 0 ? (
              <span className="project-batch-hidden" role="status">
                {hidden === 1
                  ? "1 está fuera del filtro y también se incluye"
                  : `${hidden} están fuera del filtro y también se incluyen`}
              </span>
            ) : null;
          })()}
          {editable ? (
            <>
              <button
                type="button"
                className="ui-button ui-button--compact"
                disabled={busy}
                onClick={() => setGlobal(true)}
              >
                <Icon name="swatch" size={16} />
                Cambiar acabado o vidrio
              </button>
              <button
                type="button"
                className="ui-button ui-button--compact"
                disabled={busy}
                onClick={() =>
                  void operations.run(
                    [{ op: "duplicate_positions", position_ids: ids }],
                    `${ids.length === 1 ? "Ventana duplicada" : `${ids.length} ventanas duplicadas`} al final de la obra.`,
                  )
                }
              >
                <Icon name="copy" size={16} />
                Duplicar
              </button>
              <label className="project-batch-set">
                <select
                  aria-label="Dato a cambiar"
                  value={batch}
                  onChange={(event) => {
                    setBatch(event.target.value as typeof batch);
                    setBatchValue("");
                  }}
                >
                  <option value="floor">Piso</option>
                  <option value="room">Recinto</option>
                  <option value="axis">Eje</option>
                  <option value="location">Ubicación</option>
                  <option value="quantity">Cantidad</option>
                </select>
                <input
                  aria-label="Nuevo valor"
                  placeholder="Nuevo valor"
                  inputMode={batch === "quantity" ? "numeric" : "text"}
                  maxLength={batch === "location" ? 120 : 80}
                  value={batchValue}
                  onChange={(event) => setBatchValue(event.target.value)}
                />
                <button
                  type="button"
                  className="ui-button ui-button--compact"
                  disabled={
                    busy ||
                    !batchValue.trim() ||
                    (batch === "quantity" &&
                      (!/^\d+$/.test(batchValue) ||
                        Number(batchValue) < 1 ||
                        Number(batchValue) > 2147483647))
                  }
                  onClick={() =>
                    void operations.propose(
                      [
                        {
                          op: "set_positions",
                          position_ids: ids,
                          ...(batch === "quantity"
                            ? { quantity: Number(batchValue) }
                            : batch === "location"
                              ? { location: batchValue }
                              : { placement: { [batch]: batchValue } }),
                        },
                      ],
                      "Cambiar ubicación o cantidad de las ventanas elegidas",
                    )
                  }
                >
                  Revisar
                </button>
              </label>
              <Menu
                label="Más"
                items={[
                  { id: "up", label: "Subir en el orden", onSelect: () => reorder(-1) },
                  { id: "down", label: "Bajar en el orden", onSelect: () => reorder(1) },
                  {
                    id: "remove",
                    label: "Eliminar",
                    danger: true,
                    onSelect: () => void remove(ids),
                  },
                ]}
              />
            </>
          ) : (
            <p>
              La revisión está cerrada o tu rol es de consulta; crea una revisión para cambiar
              ventanas.
            </p>
          )}
          <button
            type="button"
            className="ui-button ui-button--ghost ui-button--compact"
            onClick={() => setChecked([])}
          >
            Quitar selección
          </button>
        </section>
      )}
      <ProjectOpsReview operations={operations} orgId={orgId} currency={project.currency} />
      {global && (
        <div className="project-global-change">
          <div className="project-section-head">
            <h3>Cambiar acabado o vidrio</h3>
            <button type="button" className="ui-button" onClick={() => setGlobal(false)}>
              Cerrar
            </button>
          </div>
          <QuotationGlobalChanges
            project={project}
            orgId={orgId}
            canWrite={editable}
            onChanged={onChanged}
            initialSelection={ids}
            expanded
          />
        </div>
      )}
      {!positions.length ? (
        <EmptyState
          kind="positions"
          title="Agrega la primera ventana"
          body="Elige una tipología y ajusta sus medidas sobre el dibujo."
          action={
            editable ? (
              <Link
                className="ui-button ui-button--primary"
                to={`/projects/${project.id}/positions/new`}
              >
                Añadir ventana
              </Link>
            ) : (
              <Link to="/projects">Volver a proyectos</Link>
            )
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          title="Ninguna ventana coincide"
          body="Cambia la búsqueda o los filtros; las ventanas de la obra se conservan."
          action={
            <button
              type="button"
              className="ui-button"
              onClick={() => {
                setSearch("");
                setTypology("");
                setGlassFilter("");
              }}
            >
              Limpiar filtros
            </button>
          }
        />
      ) : (
        <div role="list" aria-label="Ventanas">
          <VirtualPositionRows
            key={`${view}:${group}:${search}:${typology}:${glassFilter}:${columns}`}
            rows={rows}
            virtual={positions.length >= 100}
            scrollTo={scrollTo}
          />
        </div>
      )}
      {library && (
        <Suspense fallback={<Loading label="Cargando la biblioteca" />}>
          <ProjectPositionLibrary
            orgId={orgId}
            initialSystem={positions[0]?.design.system_id}
            busy={busy}
            error={operations.error}
            onClose={() => setLibrary(false)}
            onPropose={operations.propose}
          />
        </Suspense>
      )}
    </div>
  );
}

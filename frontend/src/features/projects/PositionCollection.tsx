import { lazy, Suspense, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type {
  PositionResponse,
  ProjectResponse,
  DesignOperationRequest,
} from "../../api/generated/models";
import { fmtMm, formatMoney, parseDecimalInput } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { StatusBadge, EmptyState, useConfirm } from "../../ui";
import { Icon } from "../../ui/Icon";
import { PositionThumb } from "./PositionThumb";
import { VirtualPositionRows, type PositionRowEntry } from "./VirtualPositionRows";
import { ProjectOpsReview, useProjectOperations } from "./ProjectOpsReview";
import { QuotationGlobalChanges } from "./QuotationGlobalChanges";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";

const ProjectPositionLibrary = lazy(() =>
  import("./ProjectPositionLibrary").then((module) => ({ default: module.ProjectPositionLibrary })),
);

type Group = "none" | "floor" | "room" | "axis";
function collectionState(key: string): Record<string, unknown> {
  try {
    return JSON.parse(sessionStorage.getItem(key) ?? "{}") as Record<string, unknown>;
  } catch {
    return {};
  }
}
type Commercial = { unit_net?: string | null; line_net?: string | null; source?: string };
export function positionGlass(position: PositionResponse): string {
  const values = [
    ...new Set(
      position.bom.glasses.map((glass) => glass.glass_spec || glass.article_sku).filter(Boolean),
    ),
  ];
  return (
    values.join(" · ") ||
    (position.bom.panels.length
      ? "Panel declarado en el motor"
      : "Sin dato · asigna el vidrio en el editor")
  );
}
export function positionReadiness(position: PositionResponse): {
  label: string;
  cause: string;
  tone: "success" | "warning" | "danger";
} {
  if (!position.bom)
    return {
      label: "Bloqueada",
      cause: "Falta un cálculo guardado. Abre el editor y revisa el diseño.",
      tone: "danger",
    };
  const measurement = position.measurements as { current?: boolean; state?: string } | null;
  if (measurement && (!measurement.current || measurement.state !== "CONFIRMED"))
    return {
      label: "Avisos",
      cause:
        "Revisa y confirma las medidas del vano antes de fabricar. El precio usa la fabricación guardada.",
      tone: "warning",
    };
  if (!position.location_tag)
    return {
      label: "Avisos",
      cause: "Falta la ubicación de la posición. Declárala antes de emitir.",
      tone: "warning",
    };
  return {
    label: "Geometría válida",
    cause:
      "Fuente: cálculo guardado del motor. La preparación de emisión comprueba la autoridad de fabricación.",
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
        aria-label={`Editar medidas de la posición ${position.position_index}`}
        title="Fuente: fabricación guardada del motor"
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
      <button type="submit" disabled={!w || !h || busy}>
        Revisar medidas
      </button>
      <button type="button" onClick={() => setEditing(false)}>
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
  onChanged(): Promise<unknown>;
  onImport(): void;
  onDetails(): void;
}): JSX.Element {
  const navigate = useNavigate(),
    confirm = useConfirm();
  const storageKey = `dk:collection:${orgId}:${project.id}`;
  const saved = useMemo(() => collectionState(storageKey), [storageKey]);
  const [view, setView] = useState<"list" | "grid">(saved.view === "list" ? "list" : "grid");
  const [group, setGroup] = useState<Group>(
    ["floor", "room", "axis"].includes(String(saved.group)) ? (saved.group as Group) : "none",
  );
  const [search, setSearch] = useState(typeof saved.search === "string" ? saved.search : "");
  const [typology, setTypology] = useState(
    typeof saved.typology === "string" ? saved.typology : "",
  );
  const [glassFilter, setGlassFilter] = useState(
    typeof saved.glassFilter === "string" ? saved.glassFilter : "",
  );
  const [checked, setChecked] = useState<string[]>(
    Array.isArray(saved.checked)
      ? saved.checked.filter((id): id is string => typeof id === "string")
      : [],
  );
  useEffect(() => {
    sessionStorage.setItem(
      storageKey,
      JSON.stringify({ view, group, search, typology, glassFilter, checked }),
    );
  }, [storageKey, view, group, search, typology, glassFilter, checked]);
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
  function positionCard(position: PositionResponse): JSX.Element {
    const state = positionReadiness(position),
      sale = position.commercial as Commercial | null;
    const finish = position.bom.finish;
    return (
      <div
        role="listitem"
        aria-label={`Posición ${position.position_index} · ${position.location_tag || "Sin ubicación"}`}
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
        onDoubleClick={() =>
          editable && navigate(`/projects/${project.id}/positions/${position.id}/edit`)
        }
        onKeyDown={(event) => {
          if (event.target !== event.currentTarget) return;
          if (event.key === "Enter") {
            event.preventDefault();
            if (editable) navigate(`/projects/${project.id}/positions/${position.id}/edit`);
            else onDetails();
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
            aria-label={`Seleccionar posición ${position.position_index}`}
            checked={checked.includes(position.id)}
            onChange={() => toggle(position.id)}
          />
          <span className="project-number">{position.position_index}</span>
        </label>
        <div className="position-row__thumb">
          <PositionThumb
            design={position.design}
            orgId={orgId}
            systemId={position.design.system_id}
            finish={finish}
            cuts={position.bom.profile_cuts}
            openingLeaves={position.bom.opening_leaves as OpeningLeafFact[] | undefined}
          />
          <span>Vista interior</span>
        </div>
        <div className="position-row__identity">
          <strong>{position.location_tag || `Ventana ${position.position_index}`}</strong>
          <span>{domainLabel(position.typology)}</span>
          <Dimensions
            position={position}
            editable={editable}
            busy={busy}
            onPropose={operations.propose}
          />
          <StatusBadge tone={state.tone} title={state.cause}>
            {state.label}
          </StatusBadge>
          <div className="position-row__actions">
            {editable && (
              <button
                type="button"
                className="ui-button"
                onClick={(event) => {
                  event.stopPropagation();
                  navigate(`/projects/${project.id}/positions/${position.id}/edit`);
                }}
              >
                Editar diseño
              </button>
            )}
            <button
              type="button"
              className="ui-button ui-button--ghost"
              onClick={(event) => {
                event.stopPropagation();
                onSelected(position.id);
                onDetails();
              }}
            >
              Ficha
            </button>
          </div>
        </div>
        <dl className="position-row__specs">
          <div>
            <dt>Serie</dt>
            <dd>
              {position.system_name || "Sin dato · revisa Catálogo"}
              {position.system_demo && !position.system_name?.includes("DEMO") ? " · DEMO" : ""}
            </dd>
          </div>
          <div>
            <dt>Color int. / ext.</dt>
            <dd>
              {finish
                ? `${finish.interior.name} / ${finish.exterior.name}`
                : domainLabel(position.design.color)}
            </dd>
          </div>
          <div>
            <dt>Vidrio</dt>
            <dd>{positionGlass(position)}</dd>
          </div>
          <div>
            <dt>Vano / fabricación</dt>
            <dd className="project-number">
              {position.measurements
                ? "Medición declarada · ver ficha"
                : "Vano sin dato · medir antes de fabricar"}{" "}
              / {fmtMm(position.design.nominal_width_mm)} ×{" "}
              {fmtMm(position.design.nominal_height_mm)} mm
            </dd>
          </div>
          <div>
            <dt>Cantidad</dt>
            <dd className="project-number">{position.quantity}</dd>
          </div>
          <div>
            <dt>P. unitario neto</dt>
            <dd className="project-number" title={sale?.source}>
              {sale?.unit_net != null
                ? formatMoney(sale.unit_net, project.currency)
                : "Por preparar"}
            </dd>
          </div>
          <div>
            <dt>Total neto</dt>
            <dd className="project-number" title={sale?.source}>
              {sale?.line_net != null
                ? formatMoney(sale.line_net, project.currency)
                : "Por preparar"}
            </dd>
          </div>
          {group !== "none" && (
            <div>
              <dt>{group === "floor" ? "Piso" : group === "room" ? "Recinto" : "Eje"}</dt>
              <dd>{position.placement?.[group] || "Sin dato · declara la ubicación"}</dd>
            </div>
          )}
        </dl>
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
            {title} · {entries.length} posiciones
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
        estimate: view === "grid" ? 480 : 180,
        content: (
          <div className="project-position-row-group" data-view={view}>
            {chunk.map(positionCard)}
          </div>
        ),
      });
    }
  }
  return (
    <div ref={host} className="project-position-collection" data-view={view}>
      <div className="project-positions-toolbar">
        <h2>
          Ventanas y puertas · <span className="project-number">{positions.length}</span>
        </h2>
        <label>
          Vista
          <select
            aria-label="Vista"
            value={view}
            onChange={(event) => {
              setView(event.target.value as "list" | "grid");
              setScrollTo(null);
            }}
          >
            <option value="list">Lista</option>
            <option value="grid">Grilla</option>
          </select>
        </label>
        <label>
          Agrupar
          <select
            aria-label="Agrupar"
            value={group}
            onChange={(event) => setGroup(event.target.value as Group)}
          >
            <option value="none">Orden del proyecto</option>
            <option value="floor">Piso</option>
            <option value="room">Recinto</option>
            <option value="axis">Eje</option>
          </select>
        </label>
        {editable && (
          <button
            type="button"
            className="ui-button ui-button--primary"
            disabled={busy}
            onClick={() => setLibrary(true)}
          >
            <Icon name="plus" size={17} /> Agregar ventana
          </button>
        )}
        {editable ? (
          <button
            type="button"
            className="ui-button"
            onClick={() =>
              window.dispatchEvent(
                new CustomEvent("dekopen:assistant", {
                  detail: {
                    prompt:
                      "Ayúdame a diseñar las ventanas de esta obra. Usa sus preferencias y prepara una muestra antes de aplicar el conjunto.",
                  },
                }),
              )
            }
          >
            <Icon name="assistant" size={17} />
            Diseñar con IA
          </button>
        ) : null}
        <button type="button" onClick={onImport}>
          Importar documento o plano
        </button>
        {selectedId && (
          <button type="button" onClick={onDetails}>
            Ficha de posición
          </button>
        )}
      </div>
      <details className="project-filter-panel">
        <summary>Buscar, filtrar y seleccionar</summary>
        <div className="project-positions-filters">
          <label>
            Filtrar piso, recinto, eje o ubicación
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
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
          <label>
            <input
              type="checkbox"
              aria-label="Seleccionar posiciones filtradas"
              checked={visible.length > 0 && visible.every((position) => ids.includes(position.id))}
              onChange={(event) =>
                setChecked(
                  event.target.checked
                    ? [...new Set([...ids, ...visible.map((position) => position.id)])]
                    : ids.filter((id) => !visible.some((position) => position.id === id)),
                )
              }
            />
            Seleccionar filtradas ({visible.length})
          </label>
        </div>
      </details>
      {ids.length > 0 && (
        <section
          className="project-batch-actions"
          aria-label="Acciones sobre posiciones seleccionadas"
        >
          <strong>{ids.length} seleccionadas</strong>
          {editable ? (
            <>
              <button
                disabled={busy}
                onClick={() =>
                  void operations.propose(
                    [{ op: "duplicate_positions", position_ids: ids }],
                    "Duplicar lote de posiciones",
                  )
                }
              >
                Duplicar lote
              </button>
              <button disabled={busy} onClick={() => void remove(ids)}>
                Eliminar lote
              </button>
              <button disabled={busy} onClick={() => setGlobal(true)}>
                Cambio global
              </button>
              <button disabled={busy} onClick={() => reorder(-1)}>
                Subir lote
              </button>
              <button disabled={busy} onClick={() => reorder(1)}>
                Bajar lote
              </button>
              <label>
                Cambiar
                <select
                  aria-label="Cambiar"
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
              </label>
              <label>
                Nuevo valor
                <input
                  inputMode={batch === "quantity" ? "numeric" : "text"}
                  maxLength={batch === "location" ? 120 : 80}
                  value={batchValue}
                  onChange={(event) => setBatchValue(event.target.value)}
                />
              </label>
              <button
                disabled={
                  busy ||
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
                    "Cambiar ubicación o cantidad del lote",
                  )
                }
              >
                Revisar lote
              </button>
            </>
          ) : (
            <p>
              Revisión cerrada o rol de consulta. Crea una revisión o solicita acceso para cambiar
              posiciones.
            </p>
          )}
          <button onClick={() => setChecked([])}>Limpiar selección</button>
        </section>
      )}
      <ProjectOpsReview operations={operations} orgId={orgId} currency={project.currency} />
      {global && (
        <div>
          <button type="button" onClick={() => setGlobal(false)}>
            Cerrar cambio global
          </button>
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
          title="Agrega la primera posición"
          body="Elige una tipología de la biblioteca o importa un plano para comenzar la obra."
          action={
            editable ? (
              <button onClick={() => setLibrary(true)}>Abrir biblioteca</button>
            ) : (
              <Link to="/projects">Volver a proyectos</Link>
            )
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          title="Sin posiciones para estos filtros"
          body="Revisa piso, tipología y vidrio; las posiciones del proyecto se conservan."
          action={
            <button
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
        <div role="list" aria-label="Posiciones">
          <VirtualPositionRows
            key={`${view}:${group}:${search}:${typology}:${glassFilter}:${columns}`}
            rows={rows}
            virtual={positions.length >= 100}
            scrollTo={scrollTo}
          />
        </div>
      )}
      {library && (
        <Suspense fallback={<p role="status">Cargando biblioteca de posiciones…</p>}>
          <ProjectPositionLibrary
            orgId={orgId}
            initialSystem={
              (positions.find((position) => position.id === selectedId) ?? positions[0])?.design
                .system_id
            }
            initialGlass={
              (positions.find((position) => position.id === selectedId) ?? positions[0])?.bom
                .glasses[0]?.article_sku ?? undefined
            }
            initialColor={
              (positions.find((position) => position.id === selectedId) ?? positions[0])?.design
                .color
            }
            busy={busy}
            error={operations.error}
            onClose={() => setLibrary(false)}
            onPropose={(ops, title) => operations.propose(ops, title, true)}
          />
        </Suspense>
      )}
    </div>
  );
}

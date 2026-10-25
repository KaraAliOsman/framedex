import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/apiMutator";
import { projectCutDraft, projectMaterials } from "../../api/generated/dekopen";
import type {
  CutDraft,
  MaterialGroups,
  MaterialRow,
  ProjectResponse,
} from "../../api/generated/models";
import { fmtMm, formatRevision } from "../../format";
import { Button, Icon, Loading, SegmentedControl } from "../../ui";
import "./materials.css";

type Tab = "consolidated" | "windows" | "cut";
type CutView = "sequence" | "compact" | "window";

const GROUPS: { key: keyof MaterialGroups; label: string }[] = [
  { key: "profiles", label: "Perfiles" },
  { key: "reinforcements", label: "Refuerzos" },
  { key: "glass", label: "Vidrios" },
  { key: "hardware", label: "Herrajes" },
  { key: "other", label: "Otros" },
];

type Cut = {
  sequence: number;
  length_mm: string;
  angle_left?: string | null;
  angle_right?: string | null;
  window?: string;
  role_label?: string;
  workshop_sku: string;
  unit_index?: number;
  source_kind?: string;
};
type Bar = {
  bar_index: number;
  commercial_sku: string;
  name?: string | null;
  material?: string;
  stock_length_mm: string;
  head_trim_mm: string;
  tail_trim_mm: string;
  kerf_mm: string;
  remainder_mm: string;
  remainder_reusable?: boolean;
  yield_pct: string;
  cuts: Cut[];
};
type Purchase = {
  commercial_sku: string;
  stock_length_mm: string;
  qty_bars: number;
  color: string;
  name?: string | null;
};
type Metrics = { cuts?: number; productive_length_mm?: string; reusable_remnant_mm?: string };

const percentFormat = new Intl.NumberFormat("es-CL", { maximumFractionDigits: 0 });
function percent(value: number): string {
  return `${percentFormat.format(value)} %`;
}

const meterFormat = new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 });
function fmtMeters(mm: string | undefined): string {
  return mm === undefined ? "—" : `${meterFormat.format(Number(mm) / 1000)} m`;
}

function consumption(row: MaterialRow): string {
  if (row.length_m !== null) return `${fmtMm(row.length_m)} m`;
  if (row.area_m2 !== null) return `${fmtMm(row.area_m2)} m²`;
  return `${row.count} ${row.unit}`;
}

function pieces(row: MaterialRow): string {
  if (row.unit === "kit" || row.unit === "un.") return "";
  return `${row.count} ${row.count === 1 ? "pieza" : "piezas"}`;
}

function angles(cut: Cut): string {
  if (cut.angle_left == null || cut.angle_right == null) return "—";
  return `${fmtMm(cut.angle_left)}° / ${fmtMm(cut.angle_right)}°`;
}

/** «V3 · Baño · fijo» → «V3»: the window number the cutter writes on the piece. */
function windowMark(cut: Cut): string {
  const mark = (cut.window ?? "").split(" · ")[0] ?? "";
  return cut.unit_index && cut.unit_index > 1 ? `${mark}·${cut.unit_index}` : mark;
}

/** What the saved design consumes and its draft cut, from the engine's
 * results; nothing is recalculated here. */
export function ProjectMaterials({
  project,
  orgId,
  production,
}: {
  project: ProjectResponse;
  orgId: string;
  /** Released work orders of this work (existing production list). */
  production: JSX.Element;
}): JSX.Element {
  const headers = useMemo(() => ({ headers: { "X-Organization-ID": orgId } }), [orgId]);
  const [params] = useSearchParams();
  const [tab, setTab] = useState<Tab>(params.get("tab") === "cut" ? "cut" : "consolidated");
  const requested = params.get("tab");
  useEffect(() => {
    if (requested === "cut") setTab("cut");
  }, [requested]);
  const [filter, setFilter] = useState("");
  const query = useQuery({
    queryKey: ["project-materials", orgId, project.id, project.updated_at],
    queryFn: async () => {
      const response = await projectMaterials(project.id, headers);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  const cut = useQuery({
    queryKey: ["project-cut-draft", orgId, project.id, project.updated_at],
    enabled: tab === "cut",
    queryFn: async () => {
      const response = await projectCutDraft(project.id, headers);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });

  const freshness = query.data?.freshness;
  return (
    <section className="materials" aria-label="Materiales y corte">
      <header className="materials__head">
        <div>
          <h2>Materiales y corte</h2>
          <p>Calculado por el motor desde el diseño guardado de cada ventana.</p>
        </div>
        <Button
          variant="primary"
          icon={<Icon name="cut" size={16} />}
          onClick={() => setTab("cut")}
          aria-pressed={tab === "cut"}
        >
          Orden de corte
        </Button>
      </header>
      {freshness?.design_changed ? (
        <p className="materials__stale" role="status">
          <Icon name="warning" size={16} /> El diseño cambió después de la revisión{" "}
          {formatRevision(freshness.latest_revision)}. Sus documentos y órdenes quedan como
          históricos; lo que ves aquí corresponde al diseño actual.
        </p>
      ) : null}
      <SegmentedControl
        label="Vista de materiales"
        value={tab}
        options={[
          { value: "consolidated", label: "Consolidado" },
          { value: "windows", label: "Por ventana" },
          { value: "cut", label: "Orden de corte" },
        ]}
        onValueChange={(value) => setTab(value as Tab)}
      />
      {query.isPending ? (
        <Loading label="Calculando materiales" />
      ) : query.isError ? (
        <p role="alert">
          No se pudieron cargar los materiales.{" "}
          <button type="button" onClick={() => void query.refetch()}>
            Reintentar
          </button>
        </p>
      ) : tab === "consolidated" ? (
        <>
          <label className="materials__search">
            <span className="sr-only">Buscar material</span>
            <Icon name="search" size={16} />
            <input
              type="search"
              placeholder="Buscar por nombre o referencia"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            />
          </label>
          <MaterialTables groups={query.data.consolidated} filter={filter} showWindows />
        </>
      ) : tab === "windows" ? (
        <div className="materials__windows">
          {query.data.windows.map((window) => (
            <details key={window.position_id} className="materials__window">
              <summary>
                <strong>{window.label}</strong>
                <span>
                  {window.quantity} {window.quantity === 1 ? "unidad" : "unidades"} · materiales por
                  unidad
                </span>
              </summary>
              <MaterialTables groups={window.materials} filter="" />
            </details>
          ))}
        </div>
      ) : (
        <CutDraftView state={cut} project={project} />
      )}
      <div className="materials__production">
        <h3>Órdenes liberadas</h3>
        {production}
      </div>
    </section>
  );
}

function MaterialTables({
  groups,
  filter,
  showWindows = false,
}: {
  groups: MaterialGroups;
  filter: string;
  showWindows?: boolean;
}): JSX.Element {
  const needle = filter.trim().toLocaleLowerCase("es-CL");
  const visible = GROUPS.map((group) => ({
    ...group,
    rows: groups[group.key].filter(
      (row) =>
        !needle ||
        row.name.toLocaleLowerCase("es-CL").includes(needle) ||
        row.reference.toLocaleLowerCase("es-CL").includes(needle),
    ),
  })).filter((group) => group.rows.length > 0);
  if (!visible.length) return <p className="materials__empty">No hay materiales que coincidan.</p>;
  return (
    <div className="materials__groups">
      {visible.map((group) => (
        <section key={group.key} className="materials__group">
          <h3>
            {group.label} <span>{group.rows.length}</span>
          </h3>
          <table className="materials__table">
            <thead>
              <tr>
                <th>Material</th>
                <th>Referencia</th>
                <th>Acabado</th>
                <th className="num">Piezas</th>
                <th className="num">Consumo</th>
                {showWindows ? <th>Ventanas</th> : null}
              </tr>
            </thead>
            <tbody>
              {group.rows.map((row) => (
                <tr key={`${row.reference}-${row.finish ?? ""}`}>
                  <td>{row.name}</td>
                  <td className="materials__ref">{row.reference}</td>
                  <td>{row.finish ?? ""}</td>
                  <td className="num">{pieces(row)}</td>
                  <td className="num">{consumption(row)}</td>
                  {showWindows ? (
                    <td className="materials__muted">{row.windows.join(", ")}</td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      <p className="materials__note">
        Consumo de diseño: largos de corte y superficies sin redondear. Las barras a comprar
        aparecen en la orden de corte.
      </p>
    </div>
  );
}

function CutDraftView({
  state,
  project,
}: {
  state: { isPending: boolean; isError: boolean; data?: CutDraft; refetch: () => unknown };
  project: ProjectResponse;
}): JSX.Element {
  const [view, setView] = useState<CutView>("sequence");
  if (state.isPending) return <Loading label="Preparando la orden de corte" />;
  if (state.isError || !state.data)
    return (
      <p role="alert">
        No se pudo preparar la orden de corte.{" "}
        <button type="button" onClick={() => void state.refetch()}>
          Reintentar
        </button>
      </p>
    );
  const draft = state.data;
  if (draft.state === "EMPTY") return <p>La obra no tiene piezas de perfil para cortar.</p>;
  if (draft.state === "MISSING")
    return (
      <div className="materials__missing">
        <h3>Falta información para cortar</h3>
        <ul>
          {draft.missing.map((item, index) => (
            <li key={index}>
              <p>
                {item.window ? <strong>{item.window}: </strong> : null}
                {item.cause}
              </p>
              <Link to={item.path}>{item.action}</Link>
            </li>
          ))}
        </ul>
      </div>
    );
  const bars = (draft.bars ?? []) as unknown as Bar[];
  const purchase = (draft.purchase ?? []) as unknown as Purchase[];
  const metrics = (draft.metrics ?? {}) as Metrics;
  const used = Number(metrics.productive_length_mm ?? 0);
  const bought = bars.reduce((total, bar) => total + Number(bar.stock_length_mm), 0);
  return (
    <div className="materials__cut">
      <section className="cutplan-summary" aria-label="Resumen del corte">
        <dl>
          <div>
            <dt>Barras</dt>
            <dd>{bars.length}</dd>
          </div>
          <div>
            <dt>Piezas</dt>
            <dd>{metrics.cuts ?? bars.reduce((total, bar) => total + bar.cuts.length, 0)}</dd>
          </div>
          <div>
            <dt>Aprovechamiento</dt>
            <dd>{bought > 0 ? percent((used / bought) * 100) : "—"}</dd>
          </div>
          <div>
            <dt>Sobrante reutilizable</dt>
            <dd>{fmtMeters(metrics.reusable_remnant_mm)}</dd>
          </div>
        </dl>
        <p>
          Corte con disco de {fmtMm(draft.profile?.kerf_mm)} mm y despuntes de{" "}
          {fmtMm(draft.profile?.head_trim_mm)} / {fmtMm(draft.profile?.tail_trim_mm)} mm, en barras
          nuevas. <Link to="/settings/general?section=production">Cambiar en Empresa › Taller</Link>
          . Al liberar la orden en Producción se usan el stock y los retazos reales.
        </p>
      </section>
      <section className="cutplan-buy" aria-label="Barras a comprar">
        <h3>Barras a comprar</h3>
        <table className="materials__table">
          <thead>
            <tr>
              <th>Material</th>
              <th>Código</th>
              <th className="num">Barras</th>
              <th className="num">Largo</th>
            </tr>
          </thead>
          <tbody>
            {purchase.map((line) => (
              <tr key={`${line.commercial_sku}-${line.stock_length_mm}`}>
                <td>{line.name ?? line.commercial_sku}</td>
                <td className="mono">{line.commercial_sku}</td>
                <td className="num">{line.qty_bars}</td>
                <td className="num">{fmtMm(line.stock_length_mm)} mm</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <SegmentedControl
        label="Diseño de la orden de corte"
        value={view}
        options={[
          { value: "sequence", label: "Barras" },
          { value: "compact", label: "Lista compacta" },
          { value: "window", label: "Por ventana" },
        ]}
        onValueChange={(value) => setView(value as CutView)}
      />
      {view === "sequence" ? (
        <CutBars bars={bars} />
      ) : view === "compact" ? (
        <CompactCuts bars={bars} />
      ) : (
        <WindowCuts bars={bars} project={project} />
      )}
    </div>
  );
}

/** Bars grouped by what is cut — profiles first, then steel — each drawn to
 * scale with every piece's length and window written on it, as the cutter
 * marks them. Mitred ends are drawn mitred. */
function CutBars({ bars }: { bars: Bar[] }): JSX.Element {
  const groups = new Map<string, Bar[]>();
  for (const bar of bars)
    groups.set(bar.commercial_sku, [...(groups.get(bar.commercial_sku) ?? []), bar]);
  const ordered = [...groups].sort(
    ([, left], [, right]) =>
      Number(left[0]?.material === "STEEL") - Number(right[0]?.material === "STEEL"),
  );
  return (
    <div className="cutplan-groups">
      {ordered.map(([sku, items]) => (
        <section key={sku} className="cutplan-group" aria-label={items[0]?.name ?? sku}>
          <header className="cutplan-group__head">
            <h3>{items[0]?.name ?? sku}</h3>
            <p>
              <span className="mono">{sku}</span> · {items.length}{" "}
              {items.length === 1 ? "barra" : "barras"} de {fmtMm(items[0]?.stock_length_mm)} mm
            </p>
          </header>
          <ol className="cutplan-group__bars">
            {items.map((bar, index) => (
              <CutBar
                key={bar.bar_index}
                bar={bar}
                number={index + 1}
                of={items.length}
                showRole={
                  new Set(items.flatMap((item) => item.cuts.map((cut) => cut.role_label))).size > 1
                }
              />
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

function CutBar({
  bar,
  number,
  of,
  showRole,
}: {
  bar: Bar;
  number: number;
  of: number;
  showRole: boolean;
}): JSX.Element {
  const total = Number(bar.stock_length_mm) || 1;
  const share = (mm: string | number) => `${(Number(mm) / total) * 100}%`;
  const kerf = Number(bar.kerf_mm) || 0;
  return (
    <li className="cutplan-bar">
      <p className="cutplan-bar__title">
        <strong>
          Barra {number} de {of}
        </strong>
        <span>
          {bar.cuts.length} {bar.cuts.length === 1 ? "pieza" : "piezas"} · aprovecha{" "}
          {percent(Number(bar.yield_pct))} · sobra {fmtMm(bar.remainder_mm)} mm
          {bar.remainder_reusable ? " reutilizable" : ""}
        </span>
      </p>
      <div className="cutplan-bar__track" role="img" aria-label={barDescription(bar)}>
        <span className="cutplan-bar__trim" style={{ flexBasis: share(bar.head_trim_mm) }} />
        {bar.cuts.map((cut, index) => (
          <span
            key={cut.sequence}
            className="cutplan-piece"
            data-steel={cut.source_kind === "REINFORCEMENT" || undefined}
            data-left={
              cut.angle_left != null && Number(cut.angle_left) !== 90 ? "mitre" : undefined
            }
            data-right={
              cut.angle_right != null && Number(cut.angle_right) !== 90 ? "mitre" : undefined
            }
            style={{
              flexBasis: share(cut.length_mm),
              marginRight: index < bar.cuts.length - 1 ? share(kerf) : undefined,
            }}
            title={`${cut.role_label ?? ""} · ${cut.window ?? ""} · ${fmtMm(cut.length_mm)} mm · ${angles(cut)}`}
          >
            <b>{fmtMm(cut.length_mm)}</b>
            <small>{windowMark(cut)}</small>
          </span>
        ))}
        <span
          className="cutplan-bar__rest"
          data-reusable={bar.remainder_reusable || undefined}
          style={{ flexBasis: share(bar.remainder_mm) }}
        />
      </div>
      <ol className="cutplan-bar__pieces">
        {bar.cuts.map((cut) => (
          <li key={cut.sequence}>
            <span className="cutplan-bar__seq">{cut.sequence}</span>
            <b>{fmtMm(cut.length_mm)}</b>
            <span className="cutplan-bar__window">
              {showRole ? `${cut.role_label} · ` : ""}
              {cut.window}
            </span>
            <span className="cutplan-bar__angles">{cut.angle_left == null ? "" : angles(cut)}</span>
          </li>
        ))}
      </ol>
    </li>
  );
}

function barDescription(bar: Bar): string {
  const pieces = bar.cuts.map((cut) => `${fmtMm(cut.length_mm)} mm ${windowMark(cut)}`).join(", ");
  return `Barra ${bar.bar_index} de ${fmtMm(bar.stock_length_mm)} mm: ${pieces}; sobran ${fmtMm(bar.remainder_mm)} mm.`;
}

function CompactCuts({ bars }: { bars: Bar[] }): JSX.Element {
  const groups = new Map<string, Map<string, { count: number; windows: Set<string>; cut: Cut }>>();
  for (const bar of bars)
    for (const piece of bar.cuts) {
      const byLength = groups.get(bar.commercial_sku) ?? new Map();
      const key = `${piece.length_mm}|${angles(piece)}`;
      const entry = byLength.get(key) ?? { count: 0, windows: new Set<string>(), cut: piece };
      entry.count += 1;
      if (piece.window) entry.windows.add(piece.window);
      byLength.set(key, entry);
      groups.set(bar.commercial_sku, byLength);
    }
  return (
    <div className="materials__groups">
      {[...groups.entries()].map(([sku, entries]) => (
        <section key={sku} className="materials__group">
          <h3>{sku}</h3>
          <table className="materials__table materials__table--dense">
            <thead>
              <tr>
                <th className="num">Largo mm</th>
                <th>Ángulos</th>
                <th className="num">Cant.</th>
                <th>Pieza</th>
                <th>Ventanas</th>
              </tr>
            </thead>
            <tbody>
              {[...entries.values()]
                .sort((a, b) => Number(b.cut.length_mm) - Number(a.cut.length_mm))
                .map((entry) => (
                  <tr key={`${entry.cut.length_mm}-${angles(entry.cut)}`}>
                    <td className="num">{fmtMm(entry.cut.length_mm)}</td>
                    <td>{angles(entry.cut)}</td>
                    <td className="num">{entry.count}</td>
                    <td>{entry.cut.role_label}</td>
                    <td className="materials__muted">{[...entry.windows].join(", ")}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}

function WindowCuts({ bars, project }: { bars: Bar[]; project: ProjectResponse }): JSX.Element {
  const byWindow = new Map<string, { bar: Bar; cut: Cut }[]>();
  for (const bar of bars)
    for (const piece of bar.cuts) {
      const key = piece.window ?? "";
      byWindow.set(key, [...(byWindow.get(key) ?? []), { bar, cut: piece }]);
    }
  const order = (project.positions ?? []).map(
    (position) =>
      `V${position.position_index}${position.location_tag ? ` · ${position.location_tag}` : ""}`,
  );
  const keys = [...byWindow.keys()].sort((a, b) => order.indexOf(a) - order.indexOf(b));
  return (
    <div className="materials__groups">
      {keys.map((key) => (
        <section key={key} className="materials__group">
          <h3>{key}</h3>
          <table className="materials__table materials__table--dense">
            <thead>
              <tr>
                <th>Pieza</th>
                <th>Material</th>
                <th className="num">Largo mm</th>
                <th>Ángulos</th>
                <th>Barra</th>
              </tr>
            </thead>
            <tbody>
              {(byWindow.get(key) ?? [])
                .sort((a, b) => Number(b.cut.length_mm) - Number(a.cut.length_mm))
                .map(({ bar, cut }, index) => (
                  <tr key={index}>
                    <td>
                      {cut.role_label}
                      {cut.unit_index && cut.unit_index > 1 ? ` · u${cut.unit_index}` : ""}
                    </td>
                    <td className="materials__ref">{cut.workshop_sku}</td>
                    <td className="num">{fmtMm(cut.length_mm)}</td>
                    <td>{angles(cut)}</td>
                    <td>
                      {bar.commercial_sku} · {bar.bar_index}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}

import { CatalogProvenance, SectionReviewFacts, SourceHighlight } from "./CatalogProvenance";
import { WorkspaceGlasses, WorkspaceCosts } from "./WorkspaceMaterials";
import { DemoBadge, DimLoader } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";
import { useEffect, useState } from "react";
import { WorkCenterRequestKindEnum } from "../../api/generated/models";
import type {
  ArticleResponse,
  EvidenceRow,
  BeadResponse,
  KitResponse,
  PurchaseMappingRow,
  ReinforcementRow,
  SystemWorkspace,
  WorkCenter,
  WorkCenterRequestRequest,
} from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { fmtMm, formatDecimal, formatDateTime } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { centerKindLabel, opKindLabel, stationCodeLabel } from "../production/labels";
import { SectionPreviewSvg } from "../canvas/SectionPreviewSvg";
import { catalogVocabulary, type Resource, type Row, type catalogApi } from "./catalogModel";

type Label = Parameters<typeof t>[0];
const ct = (key: string) => catalogVocabulary[key] ?? t(`catalog.${key}` as Label);
const wst = (key: string) => t(`catalog.ws.${key}` as Label);

function TechnicalCode({ value }: { value: string }) {
  return (
    <details className="ws-technical-code">
      <summary>Detalles técnicos</summary>
      <code>{value}</code>
    </details>
  );
}

function productKindLabel(kind: string): string {
  const key = `catalog.productKind.${kind}` as Label;
  return ["catalog.productKind.STANDARD", "catalog.productKind.FRAMELESS"].includes(key)
    ? t(key)
    : kind;
}

function joiningMethodLabel(method: string | null | undefined): string {
  if (!method) return "—";
  const key = `catalog.joining.${method}` as Label;
  return ["catalog.joining.WELD", "catalog.joining.CRIMP", "catalog.joining.NONE"].includes(key)
    ? t(key)
    : method;
}

/** Entity references in blocker text carry raw UUIDs — a record id means
 * nothing read as prose. The system's own id renders as its name; any other
 * keeps a short code. */
const UUID_RE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;

function levelOk(level: { ok?: boolean; state?: string; blockers: unknown[] }): boolean {
  if (level.state) return level.state === "COMPLETE";
  return level.ok === true;
}

function ArticleCard({
  article,
  purchased,
  beads,
  canEdit,
  onEdit,
  evidence,
}: {
  article: ArticleResponse;
  purchased: boolean;
  evidence: EvidenceRow[];
  beads: number;
  canEdit: boolean;
  onEdit: () => void;
}) {
  const depth = article.section?.depth_mm;
  return (
    <article className="ws-article-card" id={`article-${article.id}`}>
      <div className="ws-article-section">
        {article.section ? (
          <SectionPreviewSvg
            section={article.section}
            faceWidthMm={Number(article.face_width_mm)}
            material={article.material}
          />
        ) : (
          <p className="ws-empty">Sección: Sin dato. Declara la geometría del proveedor.</p>
        )}
        <SectionReviewFacts facts={article.section_facts} />
        <small>
          {article.section
            ? `${ct(`sectionSource.${article.section.source}`)}${depth ? ` · ${fmtMm(depth)} mm` : ""}`
            : wst("sectionApprox")}
        </small>
      </div>
      <div className="ws-article-body">
        <header>
          <strong>{article.name}</strong>
          <TechnicalCode value={article.sku} />
        </header>
        <dl>
          <div>
            <dt>{wst("role")}</dt>
            <dd>{ct(`option.${article.role}`)}</dd>
          </div>
          <div>
            <dt>{wst("face")}</dt>
            <dd>{fmtMm(article.face_width_mm)} mm</dd>
          </div>
          <div>
            <dt>{wst("commercialLength")}</dt>
            <dd>
              {article.commercial_length_mm
                ? `${fmtMm(article.commercial_length_mm)} mm`
                : wst("unknown")}
            </dd>
          </div>
          <div>
            <dt>{wst("weight")}</dt>
            <dd title={article.weight_kg_m ? `${fmtMm(article.weight_kg_m)} kg/m` : undefined}>
              {article.weight_kg_m
                ? `${formatDecimal(article.weight_kg_m, 2)} kg/m`
                : wst("unknown")}
            </dd>
          </div>
          <div>
            <dt>Pérdida de soldadura</dt>
            <dd>
              {article.welding_loss_mm == null
                ? "Sin dato"
                : `${fmtMm(article.welding_loss_mm)} mm`}
            </dd>
          </div>
          <div>
            <dt>{wst("purchaseState")}</dt>
            <dd>
              {purchased ? (
                <span className="ws-badge ws-badge--ok">{wst("mapped")}</span>
              ) : (
                <span className="ws-badge ws-badge--warn">{wst("unmapped")}</span>
              )}
            </dd>
          </div>
          <div>
            <dt>{wst("beads")}</dt>
            <dd>{beads === 0 ? wst("noBeads") : `${beads}`}</dd>
          </div>
        </dl>
        <footer>
          <CatalogProvenance row={article} evidence={evidence} />
          {canEdit && (
            <button type="button" className="ui-button ui-button--small" onClick={onEdit}>
              {ct(article.read_only === false ? "edit" : "view")}
            </button>
          )}
          {!canEdit && (
            <button type="button" className="ui-button ui-button--small" onClick={onEdit}>
              {ct("view")}
            </button>
          )}
        </footer>
      </div>
    </article>
  );
}

function ReadinessLadder({ system }: { system: Row<"systems"> }) {
  const readiness = system.readiness;
  if (!readiness) return <p className="ws-empty">{ct("readinessUnknown")}</p>;
  const levels = readiness.levels ?? [];
  /** Blocker text arrives with the raw system UUID embedded — it means
   * this very record, so name it instead of showing a hex fragment. */
  const labelFor = (text: string) =>
    text
      .replace(UUID_RE, (id) =>
        id.toLowerCase() === String(system.id).toLowerCase()
          ? system.name
          : "referencia del catálogo",
      )
      .replace(
        /\b(CRIMP|CUT|GLAZE|HARDWARE|MACHINING|PACK|QC|SASH_ASSEMBLE)\b/g,
        (code) =>
          ({
            CRIMP: "Engaste",
            CUT: "Corte",
            GLAZE: "Acristalado",
            HARDWARE: "Herrajes",
            MACHINING: "Mecanizado",
            PACK: "Embalaje",
            QC: "Control de calidad",
            SASH_ASSEMBLE: "Armado de hoja",
          })[code] ?? "Operación de taller",
      );
  // Levels carry cumulative blocker lists — attribute each blocker to the
  // first level that reports it so nothing repeats down the ladder.
  const blockerRows: { level: string; blocker: (typeof levels)[number]["blockers"][number] }[] = [];
  const seen = new Set<string>();
  for (const level of levels) {
    for (const blocker of level.blockers) {
      const key = `${blocker.code}|${blocker.affected}`;
      if (!seen.has(key)) {
        seen.add(key);
        blockerRows.push({ level: level.level, blocker });
      }
    }
  }
  return (
    <>
      <ol className="ws-ladder">
        {levels.map((level) => {
          const ok = levelOk(level);
          return (
            <li key={level.level} className={`ws-ladder-level ${ok ? "is-ok" : "is-blocked"}`}>
              <header>
                <span className="ws-ladder-state" aria-hidden="true">
                  {ok ? "●" : "◐"}
                </span>
                <strong>{wst(`level.${level.level}`)}</strong>
                <em>
                  {level.state
                    ? t(`catalog.ws.state.${level.state}` as Label)
                    : ok
                      ? wst("complete")
                      : wst("incomplete")}
                </em>
              </header>
            </li>
          );
        })}
      </ol>
      {blockerRows.length > 0 && (
        <ul className="ws-blockers">
          {blockerRows.map(({ level, blocker }, index) => (
            <li key={`${level}-${blocker.code}-${index}`} className="ws-blocker">
              <div className="ws-blocker-head">
                <span className="ws-blocker-level">{wst(`level.${level}`)}</span>
                <strong className="ws-blocker-target">
                  {ct(`readiness.${blocker.code}`)}
                  <span className="ws-blocker-affected"> — {labelFor(blocker.affected)}</span>
                </strong>
              </div>
              {blocker.targets?.map((target) => (
                <a key={`${target.row_id}-${target.field}`} href={target.href}>
                  {target.label}
                </a>
              ))}
              <p className="ws-blocker-detail">
                <strong>{wst("missingAuthority")}:</strong> {labelFor(blocker.missing_authority)}
                <br />
                <strong>{wst("consequence")}:</strong> {labelFor(blocker.why)}
                <br />
                <strong>{wst("resolution")}:</strong> {labelFor(blocker.action)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

type WorkspaceProps = {
  api: ReturnType<typeof catalogApi>;
  systemId: string;
  canEdit: boolean;
  onEdit: (resource: Resource, id?: string) => void;
  onDeleted: (resource: Resource, id: string) => void;
  /** Jump to the tabbed record list for one resource (articles, kits, …). */
  onShowRecords: (resource: Resource) => void;
  reloadKey: number;
};

/** Current authority, its sources and the exact requirements to resolve. */
export function SystemWorkspaceView({
  api,
  systemId,
  canEdit,
  onEdit,
  onDeleted,
  onShowRecords,
  reloadKey,
}: WorkspaceProps): JSX.Element {
  const [workspace, setWorkspace] = useState<SystemWorkspace | null>(null);
  const [centers, setCenters] = useState<WorkCenter[] | null>(null);
  const [evidenceRows, setEvidenceRows] = useState<EvidenceRow[] | null>(null);
  const [error, setError] = useState(false);
  const [tab, setTab] = useState(
    () => new URLSearchParams(window.location.search).get("tab") ?? "perfiles",
  );
  const [evidenceError, setEvidenceError] = useState("");
  const [fetchReload, setFetchReload] = useState(0);

  useEffect(() => {
    // Per-effect flag: a shared ref lets a superseded fetch's AbortError
    // set the error banner after the fresh one already loaded data.
    let alive = true;
    const controller = new AbortController();
    setWorkspace(null);
    setCenters(null);
    setError(false);
    setEvidenceError("");
    setCenterError(null);
    setEvidenceRows(null);
    void api
      .workspace(systemId, controller.signal)
      .then((result) => {
        if (alive) setWorkspace(result);
      })
      .catch(() => {
        if (alive && !controller.signal.aborted) setError(true);
      });
    void api
      .workCenters(controller.signal)
      .then((result) => {
        if (alive) setCenters(result);
      })
      .catch(() => {
        if (alive)
          setCenterError(
            "No se pudieron cargar los centros. Reintenta para revisar su disponibilidad.",
          );
      });
    void api
      .evidence(systemId, controller.signal)
      .then((result) => {
        if (alive) setEvidenceRows(result);
      })
      .catch(() => {
        if (alive)
          setEvidenceError(
            "No se pudieron cargar las fuentes. Reintenta antes de revisar sus valores.",
          );
      });
    return () => {
      alive = false;
      controller.abort();
    };
  }, [api, systemId, reloadKey, fetchReload]);

  const [centerForm, setCenterForm] = useState<{
    code: string;
    name: string;
    kind: WorkCenterRequestRequest["kind"];
  } | null>(null);
  const [centerSaving, setCenterSaving] = useState(false);
  const [centerSeeding, setCenterSeeding] = useState(false);
  const [centerError, setCenterError] = useState<string | null>(null);
  useEffect(() => {
    if (!workspace) return;
    const anchor = new URLSearchParams(window.location.search).get("anchor");
    if (!anchor) return;
    const frame = window.requestAnimationFrame(() => {
      const target = document.getElementById(anchor);
      target?.focus();
      target?.scrollIntoView({ block: "center" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [workspace]);

  /** One-click standard station set — the read no longer self-seeds, so an
   * empty org resolves its work_centers blocker here (or at first release). */
  const seedCenters = async () => {
    setCenterSeeding(true);
    setCenterError(null);
    try {
      setCenters(await api.seedWorkCenters());
    } catch {
      setCenterError(t("catalog.errorNetwork"));
    } finally {
      setCenterSeeding(false);
    }
  };

  const reactivateCenter = async (center: WorkCenter) => {
    try {
      await api.upsertWorkCenter({
        code: center.code,
        name: center.name,
        kind: center.kind as WorkCenterRequestRequest["kind"],
        display_order: center.display_order,
      });
      setCenters(await api.workCenters());
    } catch {
      setCenterError(
        "No se pudo activar el centro. Reintenta y revisa su estado antes de fabricar.",
      );
    }
  };

  /** A readiness blocker that says 'missing work centers' resolves here —
   * the upsert endpoint creates or revives the row the routing needs. */
  const createCenter = async () => {
    if (!centerForm) return;
    const code = centerForm.code.trim().toUpperCase();
    const name = centerForm.name.trim();
    if (!code || !name) return;
    setCenterSaving(true);
    setCenterError(null);
    try {
      await api.upsertWorkCenter({
        code,
        name,
        kind: centerForm.kind,
        display_order: (centers?.length ?? 0) + 1,
      });
      setCenters(await api.workCenters());
      setCenterForm(null);
    } catch (createError) {
      setCenterError(
        createError instanceof Error ? createError.message : "work_center_write_failed",
      );
    } finally {
      setCenterSaving(false);
    }
  };

  if (error)
    return (
      <div>
        <p role="alert">{ct("errorNetwork")}</p>
        <button type="button" onClick={() => setFetchReload((value) => value + 1)}>
          Reintentar catálogo
        </button>
      </div>
    );
  if (!workspace) return <DimLoader label={ct("loading")} />;

  const { system, articles, beads, kits, reinforcements, purchase_mappings, process_profile } =
    workspace;

  const purchased = new Set(purchase_mappings.map((map) => map.profile_article_id));
  const beadsByArticle = new Map<string, number>();
  for (const bead of beads) {
    beadsByArticle.set(bead.bead_article_id, (beadsByArticle.get(bead.bead_article_id) ?? 0) + 1);
  }

  // Fuentes: human-readable name for the row each evidence attests.
  const targetName = (row: EvidenceRow): string => {
    if (row.authority_table === "profile_systems" && row.row_id === system.id) return system.name;
    const article = articles.find((a) => a.id === row.row_id);
    if (article) return article.name;
    const bead = beads.find((b) => b.id === row.row_id);
    if (bead) return `${wst("bead")} ${bead.glass_thickness_mm} mm`;
    const kit = kits.find((k) => k.id === row.row_id);
    if (kit) return kit.name;
    const reinforcement = reinforcements.find((r) => r.id === row.row_id);
    if (reinforcement) return reinforcement.name;
    return "Regla de la serie";
  };
  const reviewEvidence = (row: EvidenceRow, state: "REVIEWED" | "REJECTED") => {
    setEvidenceError("");
    void api
      .reviewEvidence(row.id, state)
      .then((updated) => {
        setEvidenceRows((rows) =>
          rows ? rows.map((r) => (r.id === updated.id ? updated : r)) : rows,
        );
      })
      .catch(() =>
        setEvidenceError("No se pudo revisar esta evidencia. Actualiza el catálogo y reintenta."),
      );
  };

  return (
    <div className="ws">
      <header className="ws-identity" id="ws.system">
        <div className="ws-identity-head">
          <h2>{system.name} </h2>
          <div className="ws-identity-meta">
            {system.manufacturer && <span className="ws-chip">{system.manufacturer}</span>}
            {system.family && <span className="ws-chip">{system.family}</span>}
            <span className="ws-chip">{ct(`option.${system.material}`)}</span>
            {(system.applications ?? []).map((app) => (
              <span key={app} className="ws-chip ws-chip--app">
                {app}
              </span>
            ))}
            {system.is_demo ? <DemoBadge /> : null}
            <span className="ws-badge">{system.is_active ? ct("active") : ct("inactive")}</span>
          </div>
          <dl className="ws-identity-facts">
            <div>
              <dt>{ct("field.depth_mm")}</dt>
              <dd>{fmtMm(system.depth_mm)} mm</dd>
            </div>
            <div>
              <dt>{ct("field.chamber_count")}</dt>
              <dd>{system.chamber_count}</dd>
            </div>
            <div>
              <dt>{wst("processAuthority")}</dt>
              <dd>
                {process_profile
                  ? `${process_profile.label} · v${process_profile.version}`
                  : wst("noProcess")}
              </dd>
            </div>
            <div>
              <dt>{wst("provenance")}</dt>
              <dd>
                <CatalogProvenance row={system} evidence={evidenceRows ?? []} />
              </dd>
            </div>
          </dl>
          <button
            type="button"
            className="ui-button ui-button--small"
            onClick={() => onEdit("systems", system.id)}
          >
            {canEdit ? ct("edit") : "Consultar sistema"}
          </button>
        </div>
        <p className="ws-readiness-summary">
          <strong>
            {system.readiness.state === "PASS"
              ? "Listo"
              : system.readiness.state === "WARN"
                ? "Cotizable; revisa fabricación"
                : "Bloqueado"}
          </strong>{" "}
          · Cobertura de la serie. La emisión comprueba los artículos usados y sella su decisión.
        </p>
        <details className="ws-readiness">
          <summary>Ver requisitos para cotizar y fabricar</summary>
          <ReadinessLadder system={system} />
        </details>
      </header>

      <nav className="ws-tabs" aria-label="Datos técnicos del sistema">
        {[
          ["perfiles", "Perfiles"],
          ["refuerzos", "Refuerzos"],
          ["vidrios", "Vidrios"],
          ["herrajes", "Herrajes"],
          ["reglas", "Reglas de compatibilidad"],
          ["costos", "Costos"],
          ["historial", "Historial"],
        ].map(([key, label]) => (
          <button
            type="button"
            key={key}
            aria-pressed={tab === key}
            onClick={() => setTab(key ?? "perfiles")}
          >
            {label}
          </button>
        ))}
      </nav>
      {centerError ? (
        <div role="alert">
          <p>{centerError}</p>
          <button type="button" onClick={() => setFetchReload((value) => value + 1)}>
            Reintentar centros
          </button>
        </div>
      ) : null}
      {tab === "vidrios" ? <WorkspaceGlasses glasses={workspace.glasses} /> : null}
      {tab === "costos" ? <WorkspaceCosts /> : null}
      {tab === "perfiles" && (
        <section className="ws-section" id="ws.articles">
          <header className="ws-section-head">
            <h3>
              {wst("articles")} <span className="ws-count">{articles.length}</span>
            </h3>
            <button
              type="button"
              className="ui-button ui-button--ghost ui-button--small"
              onClick={() => onShowRecords("articles")}
            >
              {wst("allRecords")}
            </button>
            {canEdit && (
              <button
                type="button"
                className="ui-button ui-button--small"
                onClick={() => onEdit("articles")}
              >
                {ct("create")}
              </button>
            )}
          </header>
          {!articles.length ? (
            <p className="ws-empty">{wst("noArticles")}</p>
          ) : (
            <div className="ws-article-grid">
              {articles.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  evidence={evidenceRows ?? []}
                  purchased={purchased.has(article.id)}
                  beads={beadsByArticle.get(article.id) ?? 0}
                  canEdit={canEdit}
                  onEdit={() => onEdit("articles", article.id)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "reglas" && (
        <section className="ws-section">
          <header className="ws-section-head">
            <h3>
              {wst("glazing")} <span className="ws-count">{beads.length}</span>
            </h3>
            <button
              type="button"
              className="ui-button ui-button--ghost ui-button--small"
              onClick={() => onShowRecords("glazing")}
            >
              {wst("allRecords")}
            </button>
            {canEdit && (
              <button
                type="button"
                className="ui-button ui-button--small"
                onClick={() => onEdit("glazing")}
              >
                {ct("create")}
              </button>
            )}
          </header>
          {!beads.length ? (
            <p className="ws-empty">{wst("noBeadsRows")}</p>
          ) : (
            <div className="catalog-table-scroll">
              <table className="ws-table">
                <thead>
                  <tr>
                    <th scope="col">{wst("bead")}</th>
                    <th scope="col">{ct("field.glass_thickness_mm")}</th>
                    <th scope="col">{ct("field.bead_width_mm")}</th>
                    <th scope="col">{ct("field.gasket_interior_mm")}</th>
                    <th scope="col">{ct("field.gasket_exterior_mm")}</th>
                    <th scope="col">{ct("field.cut_add_mm")}</th>
                    <th scope="col">{ct("actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {beads.map((bead: BeadResponse) => {
                    const article = articles.find((a) => a.id === bead.bead_article_id);
                    return (
                      <tr key={bead.id}>
                        <th scope="row">{article?.name ?? bead.bead_article_id}</th>
                        <td>{fmtMm(bead.glass_thickness_mm)} mm</td>
                        <td>{fmtMm(bead.bead_width_mm)} mm</td>
                        <td>{fmtMm(bead.gasket_interior_mm)} mm</td>
                        <td>{fmtMm(bead.gasket_exterior_mm)} mm</td>
                        <td>{fmtMm(bead.cut_add_mm)} mm</td>
                        <td>
                          <button
                            type="button"
                            className="ui-button ui-button--small"
                            onClick={() => onEdit("glazing", bead.id)}
                          >
                            {ct(canEdit && !bead.read_only ? "edit" : "view")}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "herrajes" && (
        <section className="ws-section">
          <header className="ws-section-head">
            <h3>
              {wst("hardware")} <span className="ws-count">{kits.length}</span>
            </h3>
            <button
              type="button"
              className="ui-button ui-button--ghost ui-button--small"
              onClick={() => onShowRecords("hardware-kits")}
            >
              {wst("allRecords")}
            </button>
            {canEdit && (
              <button
                type="button"
                className="ui-button ui-button--small"
                onClick={() => onEdit("hardware-kits")}
              >
                {ct("create")}
              </button>
            )}
          </header>
          {!kits.length ? (
            <p className="ws-empty">{wst("noKits")}</p>
          ) : (
            <div className="ws-kit-row">
              {kits.map((kit: KitResponse) => (
                <button
                  key={kit.id}
                  type="button"
                  className="ws-kit-card"
                  title={kit.sku}
                  onClick={() => onEdit("hardware-kits", kit.id)}
                >
                  <strong>{kit.name}</strong>
                  <small>
                    {ct(`option.${kit.opening_type}`)} · {ct(`option.${kit.rail_type}`)}
                  </small>
                  <span>
                    {system.is_demo ? (
                      <DemoBadge />
                    ) : kit.authority_provenance?.state === "VERIFIED" ? (
                      "Verificado con evidencia"
                    ) : (
                      "Declarado; consulta su fuente"
                    )}
                  </span>
                  <span>
                    {kit.min_leaf_width_mm == null || kit.max_leaf_width_mm == null
                      ? "Ancho de hoja: Sin dato"
                      : `${fmtMm(kit.min_leaf_width_mm)}–${fmtMm(kit.max_leaf_width_mm)} mm`}
                  </span>
                  <span>
                    {kit.min_leaf_height_mm == null || kit.max_leaf_height_mm == null
                      ? "Alto de hoja: Sin dato"
                      : `${fmtMm(kit.min_leaf_height_mm)}–${fmtMm(kit.max_leaf_height_mm)} mm`}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "refuerzos" && (
        <section className="ws-section">
          <header className="ws-section-head">
            <h3>
              {wst("reinforcements")} <span className="ws-count">{reinforcements.length}</span>
            </h3>
          </header>
          {!reinforcements.length ? (
            <p className="ws-empty">{wst("noReinforcements")}</p>
          ) : (
            <div className="catalog-table-scroll">
              <table className="ws-table">
                <thead>
                  <tr>
                    <th scope="col">{wst("parent")}</th>
                    <th scope="col">{ct("field.sku")}</th>
                    <th scope="col">{wst("name")}</th>
                    <th scope="col">{wst("thickness")}</th>
                    <th scope="col">{wst("inertia")}</th>
                    <th scope="col">{wst("stockLength")}</th>
                    <th scope="col">{wst("supplier")}</th>
                  </tr>
                </thead>
                <tbody>
                  {reinforcements.map((row: ReinforcementRow) => {
                    const parent = articles.find((a) => a.id === row.parent_profile_article_id);
                    return (
                      <tr key={row.id}>
                        <th scope="row">{parent?.name ?? wst("unknown")}</th>
                        <td>
                          <TechnicalCode value={row.sku} />
                          {row.is_default && <span className="ws-badge">{wst("default")}</span>}
                        </td>
                        <td>
                          {row.name} {system.is_demo ? <DemoBadge /> : null}
                        </td>
                        <td>
                          {row.thickness_mm ? `${fmtMm(row.thickness_mm)} mm` : wst("unknown")}
                        </td>
                        <td>{row.ix_cm4 ? `${row.ix_cm4} cm⁴` : wst("unknown")}</td>
                        <td>{fmtMm(row.stock_length_mm)} mm</td>
                        <td>{row.supplier_name ?? row.manufacturer_name ?? wst("unknown")}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "costos" && (
        <section className="ws-section catalog-field-target" id="ws.purchase" tabIndex={-1}>
          <header className="ws-section-head">
            <h3>
              {wst("purchase")} <span className="ws-count">{purchase_mappings.length}</span>
            </h3>
          </header>
          {!purchase_mappings.length ? (
            <p className="ws-empty">{wst("noPurchase")}</p>
          ) : (
            <div className="catalog-table-scroll">
              <table className="ws-table">
                <thead>
                  <tr>
                    <th scope="col">{wst("article")}</th>
                    <th scope="col">{wst("commercialSku")}</th>
                    <th scope="col">{wst("manufacturer")}</th>
                    <th scope="col">{wst("supplier")}</th>
                    <th scope="col">{wst("unit")}</th>
                    <th scope="col">{ct("state")}</th>
                  </tr>
                </thead>
                <tbody>
                  {purchase_mappings.map((map: PurchaseMappingRow) => {
                    const article = articles.find((a) => a.id === map.profile_article_id);
                    return (
                      <tr key={map.id}>
                        <th scope="row">{article?.name ?? wst("unknown")}</th>
                        <td>
                          <TechnicalCode value={map.commercial_sku} />
                        </td>
                        <td>{map.manufacturer_name}</td>
                        <td>{map.supplier_name ?? wst("unknown")}</td>
                        <td>{domainLabel(map.purchase_unit)}</td>
                        <td>{ct(map.is_active ? "active" : "inactive")}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === "reglas" && (
        <section className="ws-section catalog-field-target" id="ws.process" tabIndex={-1}>
          <section id="ws.policies" className="catalog-field-target" tabIndex={-1}>
            <h3>Políticas de fabricación</h3>
            <p>
              Estas autoridades versionadas se sellan al emitir. Una corrección requiere una nueva
              política del responsable técnico; las revisiones emitidas conservan la anterior.
            </p>
            {(workspace.manufacturing_policies ?? []).map((policy) => {
              const sources = (evidenceRows ?? []).filter((row) => row.row_id === policy.id);
              return (
                <article
                  key={policy.kind}
                  id={`ws.policy-${policy.kind}`}
                  className="catalog-field-target"
                  tabIndex={-1}
                >
                  <h4>
                    {policy.label} {system.is_demo ? <DemoBadge /> : null}
                  </h4>
                  <p>
                    {policy.id === null
                      ? "Sin dato: falta una política declarada por el responsable técnico."
                      : policy.valid
                        ? `Declarada · revisión ${policy.version}`
                        : "Bloqueada: la política no cumple el contrato del motor. El responsable técnico debe publicar una revisión válida."}
                  </p>
                  {policy.global_authority ? (
                    <p>Autoridad de plataforma; la organización puede consultarla.</p>
                  ) : null}
                  {sources.length ? (
                    sources.map((source) => (
                      <div key={source.id}>
                        <p>{source.source_document}</p>
                        <SourceHighlight
                          quote={source.source_quote}
                          literal={source.source_literal}
                        />
                      </div>
                    ))
                  ) : (
                    <p>
                      Fuente documental: Sin dato. La validez del contrato no acredita certificación
                      del fabricante.
                    </p>
                  )}
                </article>
              );
            })}
          </section>
          <header className="ws-section-head">
            <h3>{wst("process")}</h3>
          </header>
          {!process_profile ? (
            <p className="ws-empty">
              {wst("noProcessBound")}{" "}
              {canEdit && (
                <button
                  type="button"
                  className="ui-button ui-button--small"
                  onClick={() => onEdit("systems", system.id)}
                >
                  {wst("bindProcess")}
                </button>
              )}
            </p>
          ) : (
            <div className="ws-process">
              <header>
                <strong>
                  {process_profile.label} <code>{process_profile.code}</code> v
                  {process_profile.version}
                </strong>
                <div className="ws-identity-meta">
                  {process_profile.org_id === null && (
                    <span className="ws-chip">{ct("global")}</span>
                  )}
                  {process_profile.material && (
                    <span className="ws-chip">{ct(`option.${process_profile.material}`)}</span>
                  )}
                  {process_profile.product_kind && (
                    <span className="ws-chip">
                      {productKindLabel(process_profile.product_kind)}
                    </span>
                  )}
                  <span className="ws-chip">
                    {joiningMethodLabel(process_profile.joining_method)}
                  </span>
                </div>
              </header>
              <div className="ws-process-cols">
                <div>
                  <h4>{wst("stations")}</h4>
                  <ul className="ws-stations">
                    {(
                      process_profile.stations as {
                        code?: string;
                        station?: string;
                        when?: string;
                        work_center?: string;
                      }[]
                    ).map((station, index) => (
                      <li key={index}>
                        <strong>{stationCodeLabel(station.code ?? station.station ?? "?")}</strong>
                        {station.when && (
                          <small>
                            {" "}
                            ·{" "}
                            {station.when === "required"
                              ? "Requerida"
                              : station.when === "auto"
                                ? "Según el trabajo emitido"
                                : "Condicional"}
                          </small>
                        )}
                        {station.work_center && <small> · {station.work_center}</small>}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>{wst("operationMap")}</h4>
                  <ul className="ws-stations">
                    {Object.entries(process_profile.operation_station_map).map(([op, station]) => (
                      <li key={op}>
                        <code>{opKindLabel(op)}</code> →{" "}
                        <strong>{stationCodeLabel(String(station))}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4>{wst("capabilities")}</h4>
                  <ul className="ws-stations">
                    {[
                      ["sashAssembly", process_profile.sash_assembly_required],
                      ["hardwareStation", process_profile.hardware_station],
                      ["glazing", process_profile.glazing],
                      ["qc", process_profile.qc],
                      ["packaging", process_profile.packaging],
                    ].map(([key, enabled]) => (
                      <li key={String(key)} className={enabled ? "" : "ws-off"}>
                        {wst(String(key))}: {enabled ? "✓" : "—"}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
          {centers !== null ? (
            <div className="ws-centers catalog-field-target" id="ws.centers" tabIndex={-1}>
              <h4>{wst("centers")}</h4>
              {centers.length === 0 && (
                <p className="ws-empty">
                  {wst("noCenters")}
                  {canEdit && (
                    <>
                      {" "}
                      <button
                        type="button"
                        className="ui-button ui-button--small"
                        disabled={centerSeeding}
                        onClick={() => void seedCenters()}
                      >
                        {centerSeeding ? wst("seedingCenters") : wst("seedCenters")}
                      </button>
                    </>
                  )}
                </p>
              )}
              <ul className="ws-stations">
                {centers.map((center) => (
                  <li key={center.id}>
                    <strong>{center.name}</strong>
                    <small> · {centerKindLabel(center.kind)}</small>
                    <TechnicalCode value={center.code} />
                    {!center.active && (
                      <>
                        {" "}
                        <span className="ws-chip ws-chip--off">{wst("centerInactive")}</span>
                        {canEdit && (
                          <>
                            {" "}
                            <button
                              type="button"
                              className="link-button"
                              onClick={() => void reactivateCenter(center)}
                            >
                              {wst("centerActivate")}
                            </button>
                          </>
                        )}
                      </>
                    )}
                  </li>
                ))}
              </ul>
              {canEdit &&
                (centerForm ? (
                  <ValidatedForm
                    className="ws-center-form"
                    onSubmit={(event) => {
                      event.preventDefault();
                      void createCenter();
                    }}
                  >
                    <input
                      value={centerForm.code}
                      placeholder={wst("centerCode")}
                      maxLength={50}
                      aria-label={wst("centerCode")}
                      onChange={(event) =>
                        setCenterForm({ ...centerForm, code: event.target.value })
                      }
                    />
                    <input
                      value={centerForm.name}
                      placeholder={wst("centerName")}
                      maxLength={200}
                      aria-label={wst("centerName")}
                      onChange={(event) =>
                        setCenterForm({ ...centerForm, name: event.target.value })
                      }
                    />
                    <select
                      value={centerForm.kind}
                      aria-label={wst("centerKind")}
                      onChange={(event) =>
                        setCenterForm({
                          ...centerForm,
                          kind: event.target.value as WorkCenterRequestRequest["kind"],
                        })
                      }
                    >
                      {Object.values(WorkCenterRequestKindEnum).map((kind) => (
                        <option key={kind} value={kind}>
                          {centerKindLabel(kind)}
                        </option>
                      ))}
                    </select>
                    <button
                      type="submit"
                      className="ui-button ui-button--small"
                      disabled={centerSaving || !centerForm.code.trim() || !centerForm.name.trim()}
                    >
                      {wst("centerCreate")}
                    </button>
                    <button
                      type="button"
                      className="link-button"
                      onClick={() => {
                        setCenterForm(null);
                        setCenterError(null);
                      }}
                    >
                      {t("projects.cancel")}
                    </button>
                    {centerError ? <span role="alert">{centerError}</span> : null}
                  </ValidatedForm>
                ) : (
                  <button
                    type="button"
                    className="ui-button ui-button--small"
                    onClick={() => setCenterForm({ code: "", name: "", kind: "CUT" })}
                  >
                    {wst("newCenter")}
                  </button>
                ))}
            </div>
          ) : null}
        </section>
      )}

      {tab === "historial" && (
        <section className="ws-section" id="ws.sources">
          <header className="ws-section-head">
            <h3>{wst("sources")}</h3>
          </header>
          <p className="ws-hint">
            Cada evidencia conserva su fuente, revisor y fecha. Una corrección no se atribuye al
            fabricante.
          </p>
          {evidenceError ? <p role="alert">{evidenceError}</p> : null}
          {evidenceRows === null ? (
            <p className="ws-empty">{ct("loading")}</p>
          ) : !evidenceRows.length ? (
            <p className="ws-empty">{wst("noSources")}</p>
          ) : (
            <table className="ui-table ws-evidence">
              <thead>
                <tr>
                  <th>{wst("evidenceTarget")}</th>
                  <th>{wst("evidenceField")}</th>
                  <th>{wst("evidenceValue")}</th>
                  <th>{wst("evidenceSource")}</th>
                  <th>{wst("evidenceScope")}</th>
                  <th>{wst("evidenceStateCol")}</th>
                  {canEdit && <th />}
                </tr>
              </thead>
              <tbody>
                {evidenceRows.map((row) => (
                  <tr key={row.id}>
                    <td>{targetName(row)}</td>
                    <td>{catalogVocabulary[`field.${row.field_name}`] ?? "Parámetro técnico"}</td>
                    <td>
                      <details>
                        <summary>Valor declarado</summary>
                        <p>{row.value_text ?? "Sin dato"}</p>
                        <SourceHighlight quote={row.source_quote} literal={row.source_literal} />
                      </details>
                    </td>
                    <td>
                      {row.source_url ? (
                        <a href={row.source_url} target="_blank" rel="noreferrer">
                          {row.source_document}
                        </a>
                      ) : (
                        row.source_document
                      )}
                      {row.source_ref ?? (row.source_page ? ` · página ${row.source_page}` : "")}
                      {row.source_import_id ? (
                        <a href={`/catalogs/systems?import=${row.source_import_id}`}>
                          Ver importación e historial
                        </a>
                      ) : null}
                      <time>
                        {row.reviewed_at ? formatDateTime(row.reviewed_at) : "Sin revisión"}
                      </time>
                      {row.applicability ? (
                        <small className="ws-evidence-applies">
                          {" "}
                          {wst("evidenceOn")} {row.applicability}
                        </small>
                      ) : null}
                    </td>
                    <td>
                      {{
                        SYSTEM: "Sistema",
                        SERIES: "Serie",
                        GLOBAL: "Catálogo global",
                        ORG: "Organización",
                      }[row.scope ?? ""] ?? "Sin dato"}
                    </td>
                    <td>
                      <span
                        className={`ws-badge ${row.review_state === "REVIEWED" ? "ws-badge--ok" : row.review_state === "REJECTED" ? "ws-badge--warn" : ""}`}
                      >
                        {wst(`evidenceState.${row.review_state}`)}
                      </span>
                    </td>
                    {canEdit && (
                      <td>
                        {row.review_state === "PENDING" && (
                          <span className="ws-evidence-actions">
                            <button
                              type="button"
                              className="ui-button ui-button--small"
                              onClick={() => reviewEvidence(row, "REVIEWED")}
                            >
                              {wst("evidenceReview")}
                            </button>
                            <button
                              type="button"
                              className="ui-button ui-button--ghost ui-button--small"
                              onClick={() => reviewEvidence(row, "REJECTED")}
                            >
                              {wst("evidenceReject")}
                            </button>
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {canEdit && (
        <p className="ws-delete">
          <button
            type="button"
            className="ui-button ui-button--small ui-button--danger"
            onClick={() => onDeleted("systems", system.id)}
          >
            {ct("delete")}
          </button>
        </p>
      )}
    </div>
  );
}

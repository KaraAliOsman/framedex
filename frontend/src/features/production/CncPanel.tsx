import { useCallback, useEffect, useState } from "react";
import {
  productionOrderCncReadiness,
  productionOrderCncPreview,
  productionOrderCncProgramGenerate,
} from "../../api/generated/dekopen";
import { apiFetchBlob } from "../../api/apiMutator";
import { fmtMm, formatDateTime } from "../../format";
import { tOptional } from "../../i18n/es-CL";
import { Button, Field, TextInput } from "../../ui/Controls";
import { EmptyState, ErrorState, LoadingState } from "../../ui/States";
import { StatusBadge } from "../../ui/StatusBadge";
import { actionErrorDetail, CncSelect as Select } from "./cncControls";
import { CncMemberDrawing } from "./CncMemberDrawing";
import {
  type CncGap,
  type CncMember,
  type CncProgram,
  type CncReview,
  type CncFinding,
  type CncMachine,
  type Verdict,
  datumLabel,
  faceLabel,
  findingText,
  opLabel,
  verdictLabel,
} from "./cncTypes";

type Readiness = {
  order_code: string;
  members: CncMember[];
  machines: CncMachine[];
  programs: CncProgram[];
  declared_unemitted: CncGap[];
  identity: Record<string, string>;
  plan_fingerprint: string;
};
const mm = (value: string | null | undefined) =>
  value == null || value === "" ? "Sin dato" : `${fmtMm(value)} mm`;
export function VerdictBadge({ value }: { value: Verdict }) {
  return (
    <StatusBadge tone={value === "BLOCK" ? "blocked" : value === "WARN" ? "person" : "success"}>
      {verdictLabel(value)}
    </StatusBadge>
  );
}
export function GapList({ gaps }: { gaps: CncGap[] }) {
  const groups = new Map<string, CncGap[]>();
  for (const gap of gaps) {
    const key = JSON.stringify([
      gap.kind,
      gap.name,
      gap.detail,
      gap.source,
      gap.component_name,
      gap.declaration,
      gap.position_index,
      gap.bay_id,
      gap.leaf_id,
      gap.member_id,
    ]);
    groups.set(key, [...(groups.get(key) ?? []), gap]);
  }
  return (
    <section className="cnc-gap-region" data-region="operaciones-no-emitidas">
      <h4>Operaciones declaradas no emitidas</h4>
      {gaps.length ? (
        <ul>
          {[...groups.values()].map((group, index) => {
            const gap = group[0]!;
            const units = [...new Set(group.map((entry) => entry.unit_index).filter(Boolean))];
            return (
              <li key={index}>
                <strong>{gap.name ?? gap.declaration ?? opLabel(gap.kind)}</strong>
                {gap.component_name ? ` · ${gap.component_name}` : ""}
                {gap.position_index ? (
                  <span className="cnc-number"> · Posición {gap.position_index}</span>
                ) : null}
                {units.length ? (
                  <span className="cnc-number">
                    {" "}
                    · {units.length === 1 ? "Unidad" : "Unidades"} {units.join(" · ")}
                  </span>
                ) : null}
                <p>{gap.detail}</p>
                <small>Fuente: {gap.source || "Datos sellados de taller"}</small>
              </li>
            );
          })}
        </ul>
      ) : (
        <p>
          No hay declaraciones pendientes detectadas en esta revisión. Esto no declara operaciones
          adicionales.
        </p>
      )}
    </section>
  );
}
export function Findings({ items }: { items: CncFinding[] }) {
  const unique = [...new Map(items.map((item) => [findingText(item), item])).entries()];
  return (
    <ul className="cnc-findings">
      {unique.map(([text]) => (
        <li key={text}>{text}</li>
      ))}
    </ul>
  );
}
function openAuthority() {
  const target = document.getElementById("cnc-authorities");
  if (target instanceof HTMLDetailsElement) {
    target.open = true;
    target.querySelector("summary")?.focus();
  }
}
export function CncPanel({ orderId, canWrite }: { orderId: string; canWrite: boolean }) {
  const [data, setData] = useState<Readiness | null>(null),
    [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null),
    [filter, setFilter] = useState("");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<string | null>(null),
    [machine, setMachine] = useState("");
  const [op, setOp] = useState<string | null>(null),
    [review, setReview] = useState<CncReview | null>(null);
  const [busy, setBusy] = useState(false),
    [confirmed, setConfirmed] = useState(false);
  const [reviewedMember, setReviewedMember] = useState(""),
    [notice, setNotice] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await productionOrderCncReadiness(orderId);
      const d = r.data as Readiness;
      setData(d);
      setError(null);
      setSelected((value) =>
        value && d.members.some((m) => m.member_id === value)
          ? value
          : (d.members.find((m) => m.operation_count)?.member_id ??
            d.members[0]?.member_id ??
            null),
      );
      setMachine((value) =>
        d.machines.some((m) => m.id === value) ? value : (d.machines[0]?.id ?? ""),
      );
    } catch (err) {
      setError(
        actionErrorDetail(
          err,
          "No se pudo cargar el mecanizado. Revisa el plan de corte y vuelve a intentar.",
        ),
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [orderId]);
  useEffect(() => {
    setReview(null);
    setConfirmed(false);
    void load();
  }, [load]);
  useEffect(() => {
    const refresh = () => {
      setReview(null);
      setConfirmed(false);
      void load();
    };
    window.addEventListener("dekopen:cnc-authority", refresh);
    return () => window.removeEventListener("dekopen:cnc-authority", refresh);
  }, [load]);
  async function preview(member: CncMember) {
    setBusy(true);
    setReview(null);
    setConfirmed(false);
    setError(null);
    try {
      const r = await productionOrderCncPreview(orderId, {
        machine_id: machine,
        member_id: member.member_id,
      });
      setReview(r.data as unknown as CncReview);
      setReviewedMember(member.member_id);
    } catch (err) {
      setError(
        actionErrorDetail(err, "No se pudo revisar el programa. Actualiza el plan y la máquina."),
      );
    } finally {
      setBusy(false);
    }
  }
  async function generate() {
    if (!review || !confirmed) return;
    setBusy(true);
    try {
      await productionOrderCncProgramGenerate(orderId, {
        machine_id: machine,
        member_id: reviewedMember,
        expected_preview: review.review_fingerprint,
        confirmed: true,
      });
      setNotice(
        `Intercambio de ${review.member_label} generado para ${review.machine_code}. Revisa su manifiesto antes de usarlo.`,
      );
      setReview(null);
      setConfirmed(false);
      await load();
    } catch (err) {
      setError(
        actionErrorDetail(
          err,
          "La vista previa dejó de ser vigente. Revisa otra vez antes de generar.",
        ),
      );
      setConfirmed(false);
    } finally {
      setBusy(false);
    }
  }
  async function download(program: CncProgram, filename: string) {
    setBusy(true);
    try {
      const manifest = await apiFetchBlob(
        `/api/v1/production/cnc/programs/${program.id}/file/manifest.json`,
      );
      const target =
        filename === "manifest.json"
          ? manifest
          : await apiFetchBlob(`/api/v1/production/cnc/programs/${program.id}/file/${filename}`);
      if (filename !== "manifest.json") {
        const reference = (
          (await manifest.blob.text().then(JSON.parse)) as {
            files: Record<string, { sha256: string; bytes: number }>;
          }
        ).files[filename];
        const bytes = await target.blob.arrayBuffer();
        const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");
        if (!reference || hash !== reference.sha256 || bytes.byteLength !== reference.bytes)
          throw new Error("El archivo no coincide con su manifiesto sellado.");
      }
      const url = URL.createObjectURL(target.blob),
        anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = target.filename ?? filename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        actionErrorDetail(
          err,
          "No se pudo verificar la descarga. El programa puede estar reemplazado; actualiza el historial.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }
  if (loading && !data)
    return <LoadingState label="Revisando mecanizado y autoridad de máquinas" />;
  if (!data)
    return (
      <ErrorState
        title="Mecanizado sin verificar"
        body={error ?? "Esta OT necesita un plan de corte vigente."}
        onRetry={() => void load()}
      />
    );
  const members = data.members.filter((m) =>
    `${m.member_label} ${m.workshop_sku ?? ""}`
      .toLocaleLowerCase("es-CL")
      .includes(filter.toLocaleLowerCase("es-CL")),
  );
  return (
    <section className="cnc-panel" data-region="mecanizado">
      <header className="cnc-heading">
        <div>
          <h3>Mecanizado por pieza</h3>
          <p>
            Intercambio neutro revisado. El formato ejecutable depende del adaptador del fabricante.
          </p>
        </div>
        <Button
          onClick={() => {
            setReview(null);
            void load();
          }}
          disabled={busy}
        >
          Actualizar
        </Button>
      </header>
      {error ? (
        <ErrorState title="La acción necesita revisión" body={error} onRetry={() => void load()} />
      ) : null}
      {notice ? (
        <p role="status" className="cnc-notice">
          {notice}
        </p>
      ) : null}
      {!canWrite ? (
        <p className="cnc-permission">
          Puedes revisar las piezas. El dueño o jefe de taller genera programas y declara máquinas.
        </p>
      ) : null}
      <div className="cnc-controls">
        <Field label="Buscar pieza o perfil">
          <TextInput
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setPage(0);
            }}
          />
        </Field>
        <Field label="Máquina para revisar">
          <Select
            disabled={busy}
            value={machine}
            onChange={(e) => {
              setMachine(e.target.value);
              setReview(null);
              setConfirmed(false);
            }}
          >
            <option value="">Elige una máquina</option>
            {data.machines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.code} · {m.name}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      {!data.machines.length ? (
        <p className="cnc-person">
          Sin máquinas activas.{" "}
          <a href="#cnc-authorities" onClick={openAuthority}>
            Declara una máquina y su autoridad
          </a>{" "}
          con el jefe de taller.
        </p>
      ) : null}
      <GapList gaps={data.declared_unemitted} />
      {members.length > 20 ? (
        <nav className="cnc-file-actions" aria-label="Páginas de piezas">
          <Button
            disabled={busy || page === 0}
            onClick={() => {
              setPage(page - 1);
              setReview(null);
            }}
          >
            Piezas anteriores
          </Button>
          <span className="cnc-number">
            {page * 20 + 1}–{Math.min((page + 1) * 20, members.length)} de {members.length} piezas
          </span>
          <Button
            disabled={busy || (page + 1) * 20 >= members.length}
            onClick={() => {
              setPage(page + 1);
              setReview(null);
            }}
          >
            Piezas siguientes
          </Button>
        </nav>
      ) : null}
      {!members.length ? (
        <EmptyState
          title="Sin piezas para este filtro"
          body="El plan no tiene piezas que coincidan. Revisa el filtro o el plan de corte."
          action={<Button onClick={() => setFilter("")}>Mostrar piezas</Button>}
        />
      ) : null}
      <div className="cnc-members">
        {members.slice(page * 20, (page + 1) * 20).map((member) => {
          const verdict = member.machines.find((m) => m.machine_id === machine),
            expanded = selected === member.member_id;
          return (
            <article
              className="cnc-member-card"
              key={member.member_id}
              data-region={`pieza-${member.member_label}`}
            >
              <button
                className="cnc-member-heading"
                disabled={busy}
                type="button"
                aria-expanded={expanded}
                onClick={() => {
                  setSelected(expanded ? null : member.member_id);
                  setOp(null);
                  setReview(null);
                  setConfirmed(false);
                }}
              >
                <span>
                  <strong>{member.member_label}</strong>
                  <span>
                    {member.workshop_sku ?? "Sin dato · perfil no sellado"} ·{" "}
                    {member.role
                      ? (tOptional("production.role." + member.role) ?? "Función no declarada")
                      : "Sin dato · función"}
                  </span>
                </span>
                <span className="cnc-number">{mm(member.length_mm)}</span>
                {member.operation_count && verdict ? (
                  <VerdictBadge value={verdict.verdict} />
                ) : (
                  <span>
                    {member.operation_count ? "Elige una máquina" : "Sin operaciones emitidas"}
                  </span>
                )}
              </button>
              {expanded ? (
                <div className="cnc-member-body">
                  <CncMemberDrawing
                    preview={member.preview}
                    label={member.member_label}
                    operations={member.operations}
                    selectedOp={op}
                    onSelectOp={setOp}
                  />
                  <div className="cnc-operation-list">
                    {member.operations.map((operation, i) => (
                      <section
                        key={operation.operation_id}
                        className={
                          op === operation.operation_id
                            ? "cnc-operation is-selected"
                            : "cnc-operation"
                        }
                      >
                        <button
                          type="button"
                          className="cnc-operation-select"
                          aria-pressed={op === operation.operation_id}
                          onClick={() => setOp(operation.operation_id)}
                        >
                          {i + 1} · {opLabel(operation.kind)}
                        </button>
                        <dl>
                          <div>
                            <dt>Cara</dt>
                            <dd>{faceLabel(operation.face)}</dd>
                          </div>
                          <div>
                            <dt>X desde inicio</dt>
                            <dd className="cnc-number">{mm(operation.u_mm)}</dd>
                          </div>
                          <div>
                            <dt>Origen</dt>
                            <dd>{datumLabel(operation.reference)}</dd>
                          </div>
                          <div>
                            <dt>Profundidad</dt>
                            <dd className="cnc-number">{mm(operation.depth_mm)}</dd>
                          </div>
                          <div>
                            <dt>Herramienta</dt>
                            <dd className="cnc-number">
                              {operation.tool_id ?? "Sin dato · falta herramienta"}
                            </dd>
                          </div>
                          <div>
                            <dt>Fuente</dt>
                            <dd>
                              {operation.detail.source ??
                                (operation.basis === "member_end_overlap"
                                  ? "Solape sellado: diferencia entre largo de corte y tramo físico, por extremo"
                                  : operation.basis.startsWith("handle_policy:")
                                    ? "Regla de manilla sellada de la revisión"
                                    : "Regla técnica sellada; abre los detalles")}
                            </dd>
                          </div>
                        </dl>
                        <details className="ui-tech">
                          <summary>Coordenadas del vano y detalles técnicos</summary>
                          <p>
                            Estas coordenadas pertenecen al plano del vano; no son Y/Z de
                            herramienta.
                          </p>
                          <p className="cnc-number">
                            X: {mm(operation.x_mm)} · Y: {mm(operation.y_mm)}
                          </p>
                          <pre>
                            {JSON.stringify(
                              { basis: operation.basis, detail: operation.detail },
                              null,
                              2,
                            )}
                          </pre>
                        </details>
                      </section>
                    ))}
                  </div>
                  {!member.operations.length ? (
                    <p>
                      No se emitió mecanizado sobre esta pieza. Revisa las declaraciones pendientes
                      de la OT.
                    </p>
                  ) : null}
                  <section className="cnc-verdicts">
                    <h4>Veredicto por máquina</h4>
                    {member.machines.map((v) => (
                      <div key={v.machine_id} className="cnc-machine-verdict">
                        <h5>
                          {v.machine_code} · {v.machine_name}
                        </h5>
                        {member.operation_count ? (
                          <>
                            <VerdictBadge value={v.verdict} />
                            <Findings items={[...v.blockers, ...v.warnings]} />
                            {v.declared_unemitted.length ? (
                              <p>
                                Las declaraciones pendientes de la OT también siguen sin emitirse en
                                esta máquina.
                              </p>
                            ) : null}
                          </>
                        ) : (
                          <p>No hay operaciones emitidas que validar para esta pieza.</p>
                        )}
                      </div>
                    ))}
                  </section>
                  {member.operation_count && machine ? (
                    <Button variant="primary" disabled={busy} onClick={() => void preview(member)}>
                      Revisar intercambio
                    </Button>
                  ) : null}
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
      {review ? (
        <section className="cnc-review" data-region="vista-previa-programa">
          <header>
            <h4>
              Antes de generar · {review.member_label} · {review.machine_code}
            </h4>
            <VerdictBadge value={review.verdict} />
          </header>
          <p>
            Se generará un intercambio neutro de esta pieza. No se envía automáticamente a la
            máquina.
          </p>
          <Findings items={review.blockers} />
          <h5>Comparación con {review.previous_no ?? "el primer programa"}</h5>
          {!review.diff.has_previous ? (
            <p>No existe un programa anterior para esta pieza y máquina.</p>
          ) : null}
          <dl className="cnc-diff">
            <div>
              <dt>Operaciones agregadas</dt>
              <dd>{review.diff.added.length}</dd>
            </div>
            <div>
              <dt>Retiradas</dt>
              <dd>{review.diff.removed.length}</dd>
            </div>
            <div>
              <dt>Modificadas</dt>
              <dd>{review.diff.changed.length}</dd>
            </div>
          </dl>
          <ul>
            {review.diff.added.map((x) => (
              <li key={`add-${x.operation_id}`}>
                Agregar {opLabel(x.kind)} · X {mm(x.u_mm)} · {faceLabel(x.face)} · profundidad{" "}
                {mm(x.depth_mm)}
              </li>
            ))}
            {review.diff.removed.map((x) => (
              <li key={`del-${x.operation_id}`}>
                Retirar {opLabel(x.kind)} · X {mm(x.u_mm)}
              </li>
            ))}
            {review.diff.changed.map((x) => (
              <li key={x.after.operation_id}>
                {opLabel(x.after.kind)} · X {mm(x.before.u_mm)} → {mm(x.after.u_mm)} · profundidad{" "}
                {mm(x.before.depth_mm)} → {mm(x.after.depth_mm)}
              </li>
            ))}
            {review.diff.authority_changes.map((x) => (
              <li key={x.field}>
                Revisar{" "}
                {(
                  {
                    machine: "máquina y herramientas",
                    preview: "sección y posición física",
                    identity: "plan y semilla",
                    declared_intent_gaps: "declaraciones pendientes",
                  } as Record<string, string>
                )[x.field] ?? "autoridad"}
                .
              </li>
            ))}
          </ul>
          <details className="ui-tech">
            <summary>Detalles de la comparación y huella</summary>
            <pre>
              {JSON.stringify(
                { comparison: review.diff, fingerprint: review.review_fingerprint },
                null,
                2,
              )}
            </pre>
          </details>
          <GapList gaps={review.declared_unemitted} />
          {canWrite && review.verdict !== "BLOCK" ? (
            <>
              <label className="cnc-confirm">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                Revisé esta pieza, la máquina, la comparación y el trabajo que queda sin emitir.
                Confirmo generar el intercambio.
              </label>
              <Button
                variant="primary"
                disabled={!confirmed || busy}
                onClick={() => void generate()}
              >
                Generar intercambio revisado
              </Button>
            </>
          ) : (
            <p className="cnc-person">
              {review.verdict === "BLOCK"
                ? "Completa las autoridades señaladas con el jefe de taller antes de generar."
                : "El dueño o jefe de taller debe confirmar la generación."}{" "}
              <a href="#cnc-authorities" onClick={openAuthority}>
                Abrir máquinas y herramientas
              </a>
            </p>
          )}
        </section>
      ) : null}
      <section className="cnc-programs" data-region="historial-programas">
        <h4>Programas y manifiestos</h4>
        <p>
          JSON y CSV contienen intercambio neutro. El manifiesto conserva hashes, plan y semilla.
          Cada descarga vigente verifica sus bytes.
        </p>
        {!data.programs.length ? (
          <p>Aún no se generó un intercambio. Revisa una pieza y su máquina.</p>
        ) : (
          <ul>
            {data.programs.map((program) => (
              <li key={program.id} id={`cnc-program-${program.id}`}>
                <h5 className="cnc-number">{program.program_no}</h5>
                <p>
                  {program.member_label} · {program.machine_code} ·{" "}
                  <span className="cnc-number">
                    {program.operation_count} operaciones · {formatDateTime(program.created_at)}
                  </span>
                </p>
                <StatusBadge tone={program.status === "SUPERSEDED" ? "person" : "success"}>
                  {program.status === "SUPERSEDED" ? "Reemplazado" : "Vigente"}
                </StatusBadge>
                {program.status === "SUPERSEDED" ? (
                  <p>
                    {program.replacement_id ? (
                      <a href={`#cnc-program-${program.replacement_id}`}>
                        Abrir vigente · {program.replacement_no}
                      </a>
                    ) : (
                      "Sin programa vigente para esta configuración. Revisa la pieza para generar uno nuevo."
                    )}
                  </p>
                ) : (
                  <div className="cnc-file-actions">
                    {[
                      ["operations.json", "Intercambio estructurado"],
                      ["operations.csv", "Lista de operaciones"],
                      ["manifest.json", "Manifiesto y hashes"],
                    ].map(([file, label]) => (
                      <Button
                        key={file}
                        disabled={busy}
                        onClick={() => void download(program, file!)}
                      >
                        {label}
                      </Button>
                    ))}
                  </div>
                )}
                <details className="ui-tech">
                  <summary>Detalles técnicos del plan y semilla</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        identity: program.identity,
                        input_fingerprint: program.input_fingerprint,
                        fingerprint: program.fingerprint,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}

import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import { ErrorState, LoadingState, Qty, useConfirm } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";
import { formatDecimal } from "../../format";

type Request = <T>(path: string, method?: string, body?: unknown) => Promise<T>;
type Need = {
  requirement_id: string;
  version_id: string;
  project_code: string;
  order_type: string;
  sku: string;
  unit: string;
  required: string;
  reserved: string;
  stock: string;
  incoming: string;
  draft: string;
  uncovered: string;
  cause: string | null;
  is_demo: boolean;
  purchase: string;
  maximum: string;
  supplier_name: string | null;
  supplier_eligibility_id: string | null;
  orders: { id: string; code: string; quantity: string }[];
};
type Proposal = {
  preview_hash: string;
  lines: Need[];
  blockers: { order_id: string; order_code: string; cause: string }[];
  remnant_offers: { remnant_id: string; order_id: string; order_code: string; reserved: boolean }[];
};
const units: Record<string, string> = {
  BAR: "barras",
  EA: "un.",
  KIT: "kits",
  M: "m",
  M2: "m²",
  SHEET: "planchas",
};

export function PurchaseNeeds({
  request,
  canWrite,
  revision,
  onCreated,
}: {
  request: Request;
  canWrite: boolean;
  revision: number;
  onCreated: () => void;
}): JSX.Element {
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [filter, setFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [key, setKey] = useState(() => crypto.randomUUID());
  const [choices, setChoices] = useState<Record<string, { quantity: string; price: string }>>({});
  const confirm = useConfirm();
  useEffect(() => {
    let current = true;
    setProposal(null);
    setError("");
    void request<Proposal>("purchasing/needs/")
      .then((value) => {
        if (!current) return;
        setProposal(value);
        setChoices(
          Object.fromEntries(
            value.lines.map((line) => [
              line.requirement_id,
              { quantity: line.cause ? "0" : line.purchase, price: "" },
            ]),
          ),
        );
      })
      .catch(() => {
        if (current)
          setError("No se pudieron calcular las necesidades. Reintenta la consulta de OT y stock.");
      });
    return () => {
      current = false;
    };
  }, [request, revision, reload]);
  const groups = new Map<string, Need[]>();
  const visible = (proposal?.lines ?? []).filter((line) =>
    [line.sku, line.project_code, line.supplier_name ?? "", ...line.orders.map((o) => o.code)]
      .join(" ")
      .toLowerCase()
      .includes(filter.toLowerCase()),
  );
  for (const line of visible.slice(offset, offset + 50)) {
    if (Number(line.required) <= 0 && !line.cause) continue;
    const label = line.supplier_name ?? "Sin proveedor asignado";
    groups.set(label, [...(groups.get(label) ?? []), line]);
  }
  const selected = visible
    .slice(offset, offset + 50)
    .filter(
      (line) =>
        !line.cause &&
        line.supplier_eligibility_id &&
        Number(choices[line.requirement_id]?.quantity) > 0,
    );
  async function submit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!proposal || !selected.length) return;
    const ok = await confirm({
      title: "¿Crear estas órdenes de compra?",
      body: `Se compran las líneas visibles de esta página con cantidad mayor a cero:\n${selected
        .map(
          (line) =>
            `${line.supplier_name} · ${line.project_code} · ${line.sku}: ${formatDecimal(choices[line.requirement_id]?.quantity ?? "0")} ${units[line.unit] ?? "un."}`,
        )
        .join(
          "\n",
        )}\nCada OC quedará lista para registrar su envío; cancelar libera solo lo pendiente.`,
      confirmLabel: "Crear órdenes revisadas",
    });
    if (!ok) return;
    setBusy(true);
    setError("");
    try {
      await request("purchasing/needs/confirm/", "POST", {
        operation_key: key,
        preview_hash: proposal.preview_hash,
        confirmed: true,
        lines: selected.map((line) => ({
          requirement_id: line.requirement_id,
          quantity: choices[line.requirement_id]?.quantity ?? "0",
          unit_price: choices[line.requirement_id]?.price || null,
        })),
      });
      setKey(crypto.randomUUID());
      onCreated();
    } catch (failure) {
      const detail =
        failure instanceof ApiError
          ? (failure.payload as { error?: { detail?: string } })?.error?.detail
          : null;
      setError(
        detail || "No se crearon las órdenes. Actualiza la propuesta y revisa las cantidades.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="purchase-needs" aria-label="Necesidades de las OT">
      <h2>Comprar lo que falta</h2>
      <p>
        El motor compara las OT liberadas con retazos compatibles, reservas, stock útil y material
        en tránsito.
      </p>
      {error && (
        <ErrorState
          title="Revisa las necesidades"
          body={error}
          onRetry={() => setReload((n) => n + 1)}
        />
      )}
      {!proposal && !error && <LoadingState label="Calculando necesidades de las OT" />}
      {proposal && !proposal.lines.length && (
        <p>
          No hay OT liberadas pendientes de material. <Link to="/production">Abrir producción</Link>
        </p>
      )}
      {proposal?.blockers.map((b) => (
        <p key={b.order_id} role="alert">
          <Link to={`/production?order=${b.order_id}`}>{b.order_code}</Link> · {b.cause}
        </p>
      ))}
      <ValidatedForm onSubmit={(event) => void submit(event)}>
        {proposal && proposal.lines.length > 0 && (
          <label>
            Buscar material, proveedor, proyecto u OT
            <input
              type="search"
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value);
                setOffset(0);
              }}
            />
          </label>
        )}
        {[...groups].map(([supplier, lines]) => (
          <section key={supplier} className="purchase-need-group">
            <h3>{supplier}</h3>
            <table>
              <thead>
                <tr>
                  <th>Material y origen</th>
                  <th>Necesidad</th>
                  <th>Reservado</th>
                  <th>Stock útil</th>
                  <th>En tránsito</th>
                  <th>OC preparada</th>
                  <th>Comprar</th>
                  <th>Precio neto unitario</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line) => (
                  <Fragment key={line.requirement_id}>
                    <tr>
                      <td>
                        <span className="ui-value">{line.sku}</span>
                        {line.is_demo && <small>DEMO · catálogo sintético</small>}
                        <details>
                          <summary>¿De dónde sale?</summary>
                          <p>
                            {line.project_code} · Necesidad del modelo sellado y del plan de corte.
                            Las mermas y la compatibilidad las decide el motor.
                          </p>
                          <ul>
                            {line.orders.map((o) => (
                              <li key={o.id}>
                                <Link to={`/production?order=${o.id}`}>{o.code}</Link> ·{" "}
                                <Qty value={o.quantity} unit={units[line.unit] ?? "un."} />
                              </li>
                            ))}
                          </ul>
                          <Link to={`/purchasing?version=${line.version_id}`}>
                            Revisar proveedor y especificación
                          </Link>
                        </details>
                      </td>
                      {[line.required, line.reserved, line.stock, line.incoming, line.draft].map(
                        (value, i) => (
                          <td
                            key={i}
                            data-label={
                              [
                                "Necesidad",
                                "Reservado",
                                "Stock útil",
                                "En tránsito",
                                "OC preparada",
                              ][i]
                            }
                          >
                            <Qty value={value} unit={units[line.unit] ?? "un."} />
                          </td>
                        ),
                      )}
                      <td data-label="Comprar">
                        {line.cause ? (
                          <span>Revisa el plan</span>
                        ) : canWrite && line.supplier_eligibility_id ? (
                          <input
                            aria-label={`Comprar · ${line.sku} · ${line.project_code}`}
                            type="number"
                            min="0"
                            max={line.maximum}
                            step="1"
                            value={choices[line.requirement_id]?.quantity ?? "0"}
                            onChange={(e) =>
                              setChoices((p) => ({
                                ...p,
                                [line.requirement_id]: {
                                  ...(p[line.requirement_id] ?? { quantity: "0", price: "" }),
                                  quantity: e.target.value,
                                },
                              }))
                            }
                          />
                        ) : (
                          <>
                            <Qty value={line.purchase} unit={units[line.unit] ?? "un."} />
                            {!line.supplier_eligibility_id && (
                              <Link to={`/purchasing?version=${line.version_id}`}>
                                Asignar proveedor
                              </Link>
                            )}
                          </>
                        )}
                      </td>
                      <td data-label="Precio neto unitario">
                        {!line.cause && canWrite && line.supplier_eligibility_id ? (
                          <label>
                            CLP
                            <input
                              aria-label={`Precio unitario · ${line.sku} · ${line.project_code}`}
                              type="number"
                              min="0"
                              step="0.01"
                              placeholder="Sin dato"
                              value={choices[line.requirement_id]?.price ?? ""}
                              onChange={(e) =>
                                setChoices((p) => ({
                                  ...p,
                                  [line.requirement_id]: {
                                    ...(p[line.requirement_id] ?? { quantity: "0", price: "" }),
                                    price: e.target.value,
                                  },
                                }))
                              }
                            />
                          </label>
                        ) : (
                          "Sin dato · falta cotización del proveedor"
                        )}
                      </td>
                    </tr>
                    {line.cause && (
                      <tr className="purchase-need-cause">
                        <td colSpan={8}>
                          <p role="alert">
                            {line.cause}
                            {Number(line.uncovered) > 0 && (
                              <>
                                {" "}
                                Faltan{" "}
                                <Qty value={line.uncovered} unit={units[line.unit] ?? "un."} />{" "}
                                fuera de la compra sellada.
                              </>
                            )}{" "}
                            <Link to={`/production?order=${line.orders[0]?.id ?? ""}`}>
                              Revisar OT
                            </Link>
                          </p>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </section>
        ))}
        {visible.length > 50 && (
          <nav aria-label="Páginas de necesidades">
            <button
              type="button"
              className="secondary"
              disabled={offset === 0}
              onClick={() => setOffset((n) => n - 50)}
            >
              Anteriores
            </button>
            <span className="ui-value">
              {offset + 1}–{Math.min(offset + 50, visible.length)} de {visible.length}
            </span>
            <button
              type="button"
              className="secondary"
              disabled={offset + 50 >= visible.length}
              onClick={() => setOffset((n) => n + 50)}
            >
              Siguientes
            </button>
          </nav>
        )}
        {canWrite && proposal && proposal.lines.length > 0 && (
          <button type="submit" disabled={busy || !selected.length}>
            {busy ? "Creando órdenes…" : "Comprar lo que falta"}
          </button>
        )}
      </ValidatedForm>
      {!canWrite && (
        <p>
          El dueño o jefe de taller puede crear órdenes y reservar material. Solicita su revisión.
        </p>
      )}
      {proposal?.remnant_offers.length ? (
        <details>
          <summary>Retazos elegidos por el motor</summary>
          <ul>
            {proposal.remnant_offers.map((r) => (
              <li key={`${r.order_id}:${r.remnant_id}`}>
                <Link to={`/inventory?remnant=${r.remnant_id}`}>Encontrar retazo</Link> ·{" "}
                {r.order_code} ·{" "}
                {r.reserved
                  ? "Reservado en el plan"
                  : "Compatible · revisa y reserva desde inventario"}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
      {proposal && groups.size > 0 && selected.length === 0 && (
        <p>
          Las necesidades tienen cobertura o falta asignar su proveedor. Revisa cada origen antes de
          comprar.
        </p>
      )}
    </section>
  );
}

export function PurchaseMail({
  request,
  orderId,
}: {
  request: Request;
  orderId: string;
}): JSX.Element {
  const [preview, setPreview] = useState<{
    recipient: string;
    subject: string;
    text: string;
  } | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const confirm = useConfirm();
  return (
    <details className="purchase-mail">
      <summary
        onClick={() => {
          void request<{ recipient: string; subject: string; text: string }>(
            `purchasing/orders/${orderId}/mail/`,
          )
            .then(setPreview)
            .catch(() =>
              setMessage(
                "No se pudo preparar el correo. Revisa el proveedor y el estado de envío de la OC.",
              ),
            );
        }}
      >
        Correo al proveedor
      </summary>
      {preview && (
        <>
          <p>Para: {preview.recipient || "Sin dato · falta correo en la elegibilidad sellada"}</p>
          <p>{preview.subject}</p>
          <p>{preview.text}</p>
          <button
            type="button"
            className="secondary"
            disabled={busy || !preview.recipient}
            onClick={() =>
              void (async () => {
                const ok = await confirm({
                  title: "¿Enviar la OC por correo?",
                  body: `Se adjunta el PDF sellado para ${preview.recipient}. Consulta el resultado en la bandeja de correo de esta revisión.`,
                  confirmLabel: "Enviar correo y PDF",
                });
                if (!ok) return;
                setBusy(true);
                try {
                  await request(`purchasing/orders/${orderId}/mail/`, "POST", {
                    confirmed: true,
                    expected_recipient: preview.recipient,
                  });
                  setMessage(
                    "Correo preparado para entrega. Consulta la bandeja de esta revisión.",
                  );
                } catch {
                  setMessage(
                    "No se pudo preparar el correo. Reintenta con la misma OC para conservar una sola entrega.",
                  );
                } finally {
                  setBusy(false);
                }
              })()
            }
          >
            Enviar correo y PDF
          </button>
        </>
      )}
      {message && <p role="status">{message}</p>}
    </details>
  );
}

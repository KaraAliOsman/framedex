import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../../api/apiMutator";
import {
  pricingApply,
  pricingPreview,
  projectsRetrieve,
  quotationPreparePreview,
} from "../../api/generated/dekopen";
import type {
  AiAgentStep,
  PriceRequestRequest,
  PriceResponse,
  ProjectResponse,
  QuotationPreview,
} from "../../api/generated/models";
import { compareDecimal } from "../../decimal";
import { formatMoney } from "../../format";
import { DocumentViewer } from "../../ui/DocumentViewer";
import { actionErrorDetail } from "../errors";

export type Preparation = {
  valid: boolean;
  project_id: string;
  project_code: string;
  project_name: string;
  currency: string;
  totals: { net: string; tax: string; gross: string };
  lines: { index: number; location: string; quantity: number; net: string }[];
  price_applied: boolean;
  request: PriceRequestRequest | null;
  basis?: { updated_at: string; revision: string; positions: { id: string; updated_at: string }[] };
  missing: { code: string; detail: string }[];
  scope: string;
};

function basisFor(project: ProjectResponse): Preparation["basis"] {
  return {
    updated_at: project.updated_at,
    revision: project.current_revision,
    positions: (project.positions ?? []).map(({ id, updated_at }) => ({ id, updated_at })),
  };
}

function sameBasis(before: Preparation["basis"], after: Preparation["basis"]): boolean {
  // Job JSONB reorders object keys and stores datetimes through a different
  // serializer than the project API. Compare identities and full precision,
  // rather than serialization order or a millisecond-truncated Date value.
  const stamp = (value: string) =>
    value
      .replace(" ", "T")
      .replace(/\+00:00$/, "Z")
      .replace(/(\.\d*?[1-9])0+(?=Z$)/, "$1")
      .replace(/\.0+(?=Z$)/, "");
  return (
    !!before &&
    !!after &&
    stamp(before.updated_at) === stamp(after.updated_at) &&
    before.revision === after.revision &&
    before.positions.length === after.positions.length &&
    before.positions.every((position, index) => {
      const current = after.positions[index];
      return (
        !!current &&
        position.id === current.id &&
        stamp(position.updated_at) === stamp(current.updated_at)
      );
    })
  );
}

export function QuotationStep({
  step,
  organizationId,
  onOpen,
}: {
  step: AiAgentStep;
  organizationId: string;
  onOpen(path: string, state: unknown): void;
}): JSX.Element | null {
  const queryClient = useQueryClient();
  const [value, setValue] = useState(step.simulation as Preparation | undefined);
  const [operation, setOperation] = useState<PriceResponse | null>(null);
  const [pdf, setPdf] = useState<QuotationPreview | null>(null);
  const [document, setDocument] = useState<Blob | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);

  async function prepare(): Promise<void> {
    if (!value || inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setMessage("");
    const options = { headers: { "X-Organization-ID": organizationId } };
    try {
      const current = await projectsRetrieve(value.project_id, options);
      if (current.status !== 200) throw new ApiError(current.status, current.data);
      const project = current.data;
      if (project.status !== "DRAFT") {
        onOpen(`/projects/${value.project_id}?section=quote`, undefined);
        return;
      }
      const basis = basisFor(project);
      let pricingId = project.current_pricing_operation_id;
      if (!project.pricing_current) {
        if (!value.request) {
          setMessage(
            "La obra cambió desde esta propuesta. Pide una cotización actualizada al asistente.",
          );
          return;
        }
        let price = operation;
        if (!price || !sameBasis(value.basis, basis)) {
          const calculated = await pricingPreview(value.request, options);
          if (calculated.status !== 200) throw new ApiError(calculated.status, calculated.data);
          price = calculated.data;
          setOperation(price);
        }
        const totals = {
          net: price.project_net,
          tax: price.project_tax,
          gross: price.project_gross,
        };
        const changed =
          !sameBasis(value.basis, basis) ||
          price.currency !== value.currency ||
          (Object.keys(totals) as (keyof typeof totals)[]).some(
            (key) => compareDecimal(totals[key], value.totals[key]) !== 0,
          );
        const updated = {
          ...value,
          basis,
          currency: price.currency,
          totals,
          lines: price.lines.map((line) => {
            const position = project.positions?.find(
              (item) => item.position_index === line.position_index,
            );
            if (!position) throw new Error("quotation_position_changed");
            return {
              index: line.position_index,
              location: position.location_tag || `Ventana ${line.position_index}`,
              quantity: position.quantity,
              net: line.line_net,
            };
          }),
        };
        setValue(updated);
        if (price.state === "PENDING") {
          setMessage(
            "El precio necesita la aprobación del dueño. La solicitud quedó preparada en Precios.",
          );
          return;
        }
        if (changed) {
          setMessage(
            "La obra o sus precios cambiaron. Revisa la muestra actualizada antes de confirmarla.",
          );
          return;
        }
        const applied = await pricingApply(
          price.id,
          { reason: "Precio revisado en la propuesta del asistente", confirmed: true },
          options,
        );
        if (applied.status !== 200) throw new ApiError(applied.status, applied.data);
        if (applied.data.state !== "APPLIED") {
          setMessage("El precio sigue pendiente de aprobación en Precios.");
          return;
        }
        pricingId = applied.data.id;
        setValue({ ...updated, price_applied: true });
        void queryClient.invalidateQueries({ queryKey: ["projects"] });
      } else if (
        !value.price_applied ||
        compareDecimal(project.total_price_gross, value.totals.gross) !== 0 ||
        !sameBasis(value.basis, basis)
      ) {
        setValue({
          ...value,
          basis,
          price_applied: true,
          currency: project.currency,
          totals: {
            net: project.total_price_net,
            tax: project.total_price_tax,
            gross: project.total_price_gross,
          },
          lines: (project.positions ?? []).map((position) => ({
            index: position.position_index,
            location: position.location_tag || `Ventana ${position.position_index}`,
            quantity: position.quantity,
            net: position.price_net,
          })),
        });
        setMessage(
          "La obra ya tiene un precio aplicado. Revisa el importe actual y prepara el PDF.",
        );
        return;
      }
      if (!pricingId) {
        setMessage("Falta el precio vigente. Abre la cotización para actualizarlo.");
        return;
      }
      const prepared = await quotationPreparePreview(
        value.project_id,
        { pricing_operation_id: pricingId },
        options,
      );
      if (prepared.status !== 201) throw new ApiError(prepared.status, prepared.data);
      setPdf(prepared.data);
      setMessage("PDF preparado para tu revisión. La propuesta conserva su estado de borrador.");
    } catch (error) {
      setMessage(
        actionErrorDetail(
          error,
          "No pudimos terminar. Revisa la conexión y vuelve a intentar; puedes continuar desde la cotización.",
        ),
      );
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

  async function viewPdf(): Promise<void> {
    if (!pdf || busy) return;
    setBusy(true);
    try {
      const response = await fetch(pdf.pdf_url, { credentials: "omit" });
      if (!response.ok) throw new Error("preview_unavailable");
      setDocument(await response.blob());
    } catch {
      setMessage(
        "El acceso al PDF venció o no pudo abrirse. Prepara una nueva vista previa desde la cotización.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (!value?.valid) return null;
  const missing = value.missing.filter(
    (item) => !value.price_applied || item.code !== "pricing_not_applied",
  );
  return (
    <section className="ask-dock__ops quotation-preparation" aria-label="Cotización preparada">
      <strong>
        {value.project_code} · {value.project_name}
      </strong>
      <p>
        {value.price_applied
          ? "Precio aplicado de la revisión actual"
          : "Propuesta calculada con las preferencias de tu empresa"}
      </p>
      <dl className="quotation-preparation__totals">
        <dt>Neto</dt>
        <dd>{formatMoney(value.totals.net, value.currency)}</dd>
        <dt>IVA</dt>
        <dd>{formatMoney(value.totals.tax, value.currency)}</dd>
        <dt>Total</dt>
        <dd>
          <strong>{formatMoney(value.totals.gross, value.currency)}</strong>
        </dd>
      </dl>
      <details>
        <summary>Ver ventanas y puertas incluidas</summary>
        <ol>
          {value.lines.map((line) => (
            <li key={line.index}>
              <span>
                {line.location || `Ventana ${line.index}`} · {line.quantity} ud.
              </span>
              <span className="ui-value">{formatMoney(line.net, value.currency)}</span>
            </li>
          ))}
        </ol>
      </details>
      {missing.length ? (
        <details>
          <summary>Antes de emitir</summary>
          <ul>
            {missing.map((item, index) => (
              <li key={index}>{item.detail}</li>
            ))}
          </ul>
        </details>
      ) : null}
      <p className="ask-dock__hint">{value.scope}</p>
      {message ? <p role="status">{message}</p> : null}
      <button
        type="button"
        className="ask-dock__action"
        disabled={busy}
        onClick={() => void (pdf ? viewPdf() : prepare())}
      >
        {busy
          ? "Preparando…"
          : pdf
            ? "Ver el PDF preparado"
            : value.price_applied
              ? "Preparar PDF"
              : "Usar este precio y preparar PDF"}
      </button>
      <button
        type="button"
        className="ask-dock__action"
        disabled={busy}
        onClick={() =>
          onOpen(
            `/projects/${value.project_id}?section=quote`,
            pdf
              ? {
                  quotationPreview: {
                    organizationId,
                    projectId: value.project_id,
                    previewId: pdf.id,
                  },
                }
              : undefined,
          )
        }
      >
        {pdf ? "Revisar y emitir" : "Completar datos de la propuesta"}
      </button>
      {operation?.state === "PENDING" ? (
        <button
          type="button"
          className="ask-dock__action"
          onClick={() => onOpen(`/projects/${value.project_id}/pricing`, undefined)}
        >
          Abrir aprobación de precio
        </button>
      ) : null}
      {document && pdf ? (
        <DocumentViewer
          blob={document}
          filename={`${value.project_code}-borrador.pdf`}
          title={`Propuesta · ${value.project_code}`}
          onClose={() => setDocument(null)}
        />
      ) : null}
    </section>
  );
}

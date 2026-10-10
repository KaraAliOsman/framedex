import { useEffect, useState } from "react";
import type { QuotationPreview } from "../../api/generated/models";
import { formatDate, formatMoney } from "../money";
import { formatDateTime, formatRevision } from "../../format";
import { DimLoader } from "../../ui/Signature";

/** Opens ancestor disclosures before scrolling and focusing the exact missing field. */
export function focusQuotationField(id: string): void {
  const field = document.getElementById(id);
  if (!field) return;
  let ancestor = field.parentElement;
  while (ancestor) {
    if (ancestor instanceof HTMLDetailsElement) ancestor.open = true;
    ancestor = ancestor.parentElement;
  }
  field.scrollIntoView?.({ block: "center", behavior: "instant" });
  field.focus();
  field.classList.remove("quotation-field-target");
  void field.offsetWidth;
  field.classList.add("quotation-field-target");
  field.addEventListener("blur", () => field.classList.remove("quotation-field-target"), {
    once: true,
  });
}

export type QuotationCheck = { key: string; label: string; complete: boolean; target: string };
export function QuotationChecklist({
  items,
  onTarget,
}: {
  items: QuotationCheck[];
  onTarget: (target: string) => void;
}): JSX.Element {
  return (
    <nav className="quotation-checklist" aria-label="Qué falta para emitir">
      <h3>Qué falta para emitir</h3>
      <ol>
        {items.map((item) => (
          <li key={item.key} data-complete={item.complete}>
            <button type="button" onClick={() => onTarget(item.target)}>
              <span aria-hidden="true">{item.complete ? "✓" : "□"}</span>
              <span>{item.label}</span>
              <small>{item.complete ? "Completo" : "Pendiente"}</small>
            </button>
          </li>
        ))}
      </ol>
      <p>Los faltantes te llevan al campo exacto. Los precios y límites los verifica el motor.</p>
    </nav>
  );
}

export function QuotationReview({
  preview,
  previousRevision,
  code,
  busy,
  confirmed,
  onConfirmed,
  onReady,
  onIssue,
}: {
  preview: QuotationPreview | null;
  previousRevision?: string;
  code: string;
  busy: boolean;
  confirmed: boolean;
  onConfirmed: (value: boolean) => void;
  onReady: (value: boolean) => void;
  onIssue: () => void;
}): JSX.Element {
  const [objectUrl, setObjectUrl] = useState("");
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [expired, setExpired] = useState(false);
  useEffect(() => {
    setObjectUrl("");
    setError("");
    setLoaded(false);
    onReady(false);
    if (!preview) return;
    const abort = new AbortController();
    let url = "";
    void (async () => {
      const response = await fetch(preview.pdf_url, { signal: abort.signal });
      if (!response.ok) throw Error("pdf_access_failed");
      const content = await response.arrayBuffer();
      const hash = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", content)),
        (byte) => byte.toString(16).padStart(2, "0"),
      ).join("");
      if (
        hash !== preview.file_sha256 ||
        content.byteLength !== preview.byte_size ||
        new TextDecoder().decode(content.slice(0, 5)) !== "%PDF-"
      )
        throw Error("pdf_integrity_failed");
      if (abort.signal.aborted) return;
      url = URL.createObjectURL(new Blob([content], { type: "application/pdf" }));
      setObjectUrl(url);
    })().catch(() => {
      if (!abort.signal.aborted)
        setError(
          "No se pudo abrir el PDF con su huella verificada. Revisa la conexión y vuelve a intentar; si venció la vista, prepara un PDF nuevo.",
        );
    });
    return () => {
      abort.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [preview, attempt, onReady]);
  useEffect(() => {
    const refresh = (): void =>
      setExpired(Boolean(preview && Date.parse(preview.expires_at) <= Date.now()));
    refresh();
    const timer = window.setInterval(refresh, 1000);
    return () => window.clearInterval(timer);
  }, [preview]);
  return (
    <aside className="quotation-review sheet-miter" aria-label="Revisión del documento">
      <h3>El documento que recibirá el cliente</h3>
      {!preview ? (
        <p>Completa el checklist y prepara el PDF. La vista usa el documento real de cotización.</p>
      ) : (
        <>
          <div className="quotation-revision-seal">
            <strong>{formatRevision(preview.revision_code)}</strong>
            <span>Lista para revisar</span>
          </div>
          {error ? (
            <div>
              <p role="alert">{error}</p>
              <button type="button" onClick={() => setAttempt((value) => value + 1)}>
                Reintentar PDF
              </button>
            </div>
          ) : objectUrl === "" ? (
            <p>
              <DimLoader label="Abriendo el PDF" /> Abriendo el PDF…
            </p>
          ) : (
            <iframe
              title="Vista previa del PDF real"
              src={`${objectUrl}#view=FitH`}
              onLoad={() => {
                setLoaded(true);
                onReady(true);
              }}
            />
          )}
          {objectUrl && (
            <a
              className="link-button"
              href={objectUrl}
              download={`COT-${code}-${preview.revision_code}.pdf`}
            >
              Descargar PDF revisado
            </a>
          )}
          <dl className="quotation-confirmation">
            <div>
              <dt>Cliente</dt>
              <dd>{preview.client_name}</dd>
            </div>
            <div>
              <dt>Destinatario</dt>
              <dd>{preview.recipient}</dd>
            </div>
            <div>
              <dt>Total · {preview.currency}</dt>
              <dd className="technical-number">
                {formatMoney(preview.total_price_gross, preview.currency)}
              </dd>
            </div>
            <div>
              <dt>Vigencia comercial</dt>
              <dd>{formatDate(preview.valid_until)}</dd>
            </div>
            <div>
              <dt>Fecha del documento</dt>
              <dd>{formatDateTime(preview.document_date)}</dd>
            </div>
          </dl>
          <p className="quotation-consequence">
            Se sellará {formatRevision(preview.revision_code)} y se enviará a {preview.recipient}.
            {previousRevision
              ? ` La ${formatRevision(previousRevision)} quedará reemplazada y conservará su documento.`
              : " El enlace del PDF se activará al emitir."}
          </p>
          <p>
            {preview.production_allowed
              ? "El motor verificó evidencia completa para autorizar fabricación."
              : "Se emitirá una cotización; la fabricación requiere completar y confirmar los antecedentes de producción."}
          </p>
          <details>
            <summary>Huella del documento y detalles técnicos</summary>
            <p>
              Huella de la BOM · <code>{preview.bom_hash}</code>
            </p>
            <p>
              PDF · <code>{preview.file_sha256}</code>
            </p>
            <p>
              Revisión del PDF válida hasta {formatDateTime(preview.expires_at)}. Si cambia la obra,
              el sistema exige otra vista.
            </p>
          </details>
          {expired ? (
            <p role="alert">La revisión del PDF venció. Prepara una vista previa nueva.</p>
          ) : null}
          <label className="quotation-confirm">
            <input
              type="checkbox"
              checked={confirmed}
              disabled={!loaded || busy || expired}
              onChange={(event) => onConfirmed(event.target.checked)}
            />
            Revisé este PDF, el destinatario y las condiciones de emisión
          </label>
          <button
            type="button"
            className="primary-action"
            disabled={!loaded || !confirmed || busy || expired}
            onClick={onIssue}
          >
            Emitir y enviar al cliente
          </button>
          <p>
            El envío se registra al sellar. Su entrega se puede seguir en el historial de correo.
          </p>
        </>
      )}
    </aside>
  );
}

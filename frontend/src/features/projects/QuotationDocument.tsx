import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError, apiFetchBlob } from "../../api/apiMutator";
import {
  getQuotationDraftPreviewUrl,
  organizationBrandingGet,
  organizationBrandingSave,
  quotationLayoutGet,
  quotationLayoutSave,
} from "../../api/generated/dekopen";
import type {
  DocumentPreferences,
  QuotationBlockEnum,
  QuotationLayout,
  QuotationTemplateEnum,
} from "../../api/generated/models";
import { Button, Field, Icon, Loading, SegmentedControl, Switch } from "../../ui";
import type { ButtonProps } from "../../ui";
import { actionErrorDetail } from "../errors";
import { QUOTATION_LAYOUT_EVENT } from "../assistant/DocumentLayoutStep";
import "./quotation-document.css";

/** Mirrors documents/quotation.py: the backend resolves the same layout. */
const DEFAULT_ORDER: Record<QuotationTemplateEnum, QuotationBlockEnum[]> = {
  ESENCIAL: [
    "intro",
    "client",
    "positions",
    "commercial",
    "terms",
    "services",
    "acceptance",
    "closing",
  ],
  PROYECTO: [
    "intro",
    "client",
    "hero",
    "summary",
    "positions",
    "commercial",
    "terms",
    "services",
    "acceptance",
    "closing",
  ],
  ALTERNATIVAS: [
    "intro",
    "client",
    "alternatives",
    "positions",
    "commercial",
    "terms",
    "services",
    "acceptance",
    "closing",
  ],
};
const REQUIRED: QuotationBlockEnum[] = ["positions", "commercial"];

const TEMPLATES: { value: QuotationTemplateEnum; label: string; detail: string }[] = [
  {
    value: "ESENCIAL",
    label: "Esencial",
    detail:
      "Breve y directa: fichas compactas en dos columnas. Para pocas ventanas o clientes particulares.",
  },
  {
    value: "PROYECTO",
    label: "Proyecto",
    detail:
      "Para obras grandes: imagen de la obra, resumen por ventana y fichas con dibujos grandes agrupadas por piso y recinto.",
  },
  {
    value: "ALTERNATIVAS",
    label: "Alternativas",
    detail:
      "Compara esta propuesta con alternativas ya preparadas; el cliente elige una. Las alternativas se eligen en las condiciones de la cotización.",
  },
];

const BLOCK_LABEL: Record<QuotationBlockEnum, string> = {
  intro: "Presentación",
  client: "Cliente y propuesta",
  hero: "Imagen de la obra",
  summary: "Resumen de ventanas",
  positions: "Ventanas y puertas",
  alternatives: "Opciones",
  commercial: "Resumen comercial",
  terms: "Condiciones",
  services: "Servicios",
  acceptance: "Aceptación o consulta en línea",
  closing: "Cierre",
};

type Texts = { intro: string; closing: string; notes: string };

function effectiveTemplate(
  layout: QuotationLayout,
  company: DocumentPreferences | null,
): QuotationTemplateEnum {
  return (
    layout.template ??
    company?.quotation_layout?.template ??
    company?.quotation_template ??
    "ESENCIAL"
  );
}

function mergedLayout(
  layout: QuotationLayout,
  company: DocumentPreferences | null,
): QuotationLayout {
  return { ...(company?.quotation_layout ?? {}), ...layout };
}

function blockOrder(
  layout: QuotationLayout,
  template: QuotationTemplateEnum,
): QuotationBlockEnum[] {
  const defaults = DEFAULT_ORDER[template];
  const chosen = (layout.order ?? []).filter((block) => defaults.includes(block));
  return [...chosen, ...defaults.filter((block) => !chosen.includes(block))];
}

function sameLayout(left: QuotationLayout, right: QuotationLayout): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

/** The real quotation early: this work's draft rendered with the sealed
 * renderer, «Borrador», without consuming the commercial number. Edits are
 * composition only (design, blocks, texts); numbers come from the price. */
export function QuotationDocument({
  projectId,
  orgId,
  canWrite,
  isOwner,
}: {
  projectId: string;
  orgId: string;
  canWrite: boolean;
  isOwner: boolean;
}): JSX.Element {
  const headers = useMemo(() => ({ "X-Organization-ID": orgId }), [orgId]);
  const [company, setCompany] = useState<DocumentPreferences | null>(null);
  const [companyVersion, setCompanyVersion] = useState<string>();
  const [saved, setSaved] = useState<QuotationLayout | null>(null);
  const [prepared, setPrepared] = useState(false);
  const [history, setHistory] = useState<QuotationLayout[]>([]);
  const [cursor, setCursor] = useState(0);
  const [texts, setTexts] = useState<Texts>({ intro: "", closing: "", notes: "" });
  const [preview, setPreview] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const request = useRef(0);

  const layout = history[cursor] ?? {};
  const merged = mergedLayout(layout, company);
  const template = effectiveTemplate(layout, company);
  const order = blockOrder(merged, template);
  const hidden = new Set(merged.hidden ?? []);
  const dirty = saved !== null && !sameLayout(layout, saved);

  const [reload, setReload] = useState(0);
  useEffect(() => {
    // The assistant edits this same composition: reload when it saves one.
    function changed(event: Event): void {
      if ((event as CustomEvent<{ projectId?: string }>).detail?.projectId === projectId)
        setReload((value) => value + 1);
    }
    window.addEventListener(QUOTATION_LAYOUT_EVENT, changed);
    return () => window.removeEventListener(QUOTATION_LAYOUT_EVENT, changed);
  }, [projectId]);

  useEffect(() => {
    let live = true;
    void Promise.all([
      quotationLayoutGet(projectId, { headers }),
      organizationBrandingGet({ headers }).catch(() => null),
    ])
      .then(([local, branding]) => {
        if (!live) return;
        if (local.status === 200) {
          setSaved(local.data.layout);
          setPrepared(local.data.prepared);
          setHistory([local.data.layout]);
          setCursor(0);
        }
        if (branding?.status === 200) {
          setCompany(branding.data.document_preferences);
          setCompanyVersion(branding.data.updated_at);
        }
      })
      .catch(() => {
        if (live) setStatus("No se pudo cargar el diseño de la cotización. Vuelve a intentar.");
      });
    return () => {
      live = false;
    };
  }, [projectId, headers, reload]);

  useEffect(() => {
    setTexts({
      intro: merged.texts?.intro ?? "",
      closing: merged.texts?.closing ?? "",
      notes: merged.texts?.notes ?? "",
    });
    // Texts follow the selected history entry, not every keystroke.
  }, [cursor, history, company]);

  const render = useCallback(
    async (current: QuotationLayout) => {
      const ticket = ++request.current;
      setRendering(true);
      try {
        const { blob } = await apiFetchBlob(getQuotationDraftPreviewUrl(projectId), {
          method: "POST",
          headers: { ...headers, "Content-Type": "application/json" },
          body: JSON.stringify(current),
        });
        if (ticket !== request.current) return;
        setPreview((previous) => {
          if (previous) URL.revokeObjectURL(previous);
          return URL.createObjectURL(blob);
        });
        setPreviewError(null);
      } catch (error) {
        if (ticket !== request.current) return;
        setPreviewError(
          error instanceof ApiError
            ? actionErrorDetail(
                error,
                "La vista previa aparece cuando la obra tiene precio aplicado y condiciones guardadas.",
              )
            : "No se pudo preparar la vista previa. Revisa tu conexión.",
        );
      } finally {
        if (ticket === request.current) setRendering(false);
      }
    },
    [projectId, headers],
  );

  useEffect(() => {
    if (saved === null) return;
    const timer = window.setTimeout(() => void render(layout), 650);
    return () => window.clearTimeout(timer);
    // The serialized layout is the dependency: a new object with the same
    // content must not render again.
  }, [JSON.stringify(layout), saved === null, render]);

  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );

  function change(next: QuotationLayout): void {
    if (sameLayout(next, layout)) return;
    setHistory((items) => [...items.slice(0, cursor + 1), next].slice(-60));
    setCursor((value) => Math.min(value + 1, 59));
  }

  function patch(values: Partial<QuotationLayout>): void {
    change({ ...layout, ...values });
  }

  function move(block: QuotationBlockEnum, step: -1 | 1): void {
    const next = [...order];
    const index = next.indexOf(block);
    const target = index + step;
    if (target < 0 || target >= next.length) return;
    const [current, swapped] = [next[index], next[target]];
    if (current === undefined || swapped === undefined) return;
    next[index] = swapped;
    next[target] = current;
    patch({ order: next });
  }

  function toggle(block: QuotationBlockEnum): void {
    const next = new Set(hidden);
    if (next.has(block)) next.delete(block);
    else next.add(block);
    patch({ hidden: [...next] });
  }

  function commitTexts(): void {
    const current = merged.texts ?? {};
    if (
      (current.intro ?? "") === texts.intro &&
      (current.closing ?? "") === texts.closing &&
      (current.notes ?? "") === texts.notes
    )
      return;
    patch({ texts: { ...texts } });
  }

  async function save(): Promise<void> {
    setBusy(true);
    setStatus("");
    try {
      const response = await quotationLayoutSave(projectId, layout, { headers });
      if (response.status !== 200) throw new Error("save");
      setSaved(response.data.layout);
      setPrepared(true);
      setStatus("Diseño guardado en esta obra. Se usa en la próxima versión para emitir.");
    } catch (error) {
      setStatus(actionErrorDetail(error, "No se pudo guardar el diseño. Vuelve a intentar."));
    } finally {
      setBusy(false);
    }
  }

  async function saveForCompany(): Promise<void> {
    if (!companyVersion) return;
    setBusy(true);
    setStatus("");
    const { template: chosen, ...rest } = merged;
    try {
      const response = await organizationBrandingSave(
        {
          document_preferences: {
            quotation_template: chosen ?? template,
            quotation_layout: { ...rest, template: chosen ?? template },
          },
          expected_updated_at: companyVersion,
        },
        { headers },
      );
      if (response.status !== 200) throw new Error("save");
      setCompany(response.data.document_preferences);
      setCompanyVersion(response.data.updated_at);
      setStatus("Diseño guardado para las nuevas cotizaciones de la empresa.");
    } catch (error) {
      setStatus(
        actionErrorDetail(error, "No se pudo guardar el diseño de la empresa. Vuelve a intentar."),
      );
    } finally {
      setBusy(false);
    }
  }

  if (saved === null) {
    return (
      <section className="quotation-document" aria-label="Documento de la cotización">
        {status ? <p role="alert">{status}</p> : <Loading label="Cargando el documento" />}
      </section>
    );
  }

  const editable = canWrite && !busy;
  const selected = TEMPLATES.find((item) => item.value === template);
  return (
    <section className="quotation-document" aria-label="Documento de la cotización">
      <header className="quotation-document__head">
        <div>
          <h2>Documento</h2>
          <p>Así lo verá su cliente. El borrador no consume número de cotización.</p>
        </div>
        <div className="quotation-document__actions">
          <Tool
            label="Deshacer"
            disabled={!editable || cursor === 0}
            onClick={() => setCursor((value) => Math.max(0, value - 1))}
          >
            <Icon name="undo" />
          </Tool>
          <Tool
            label="Rehacer"
            disabled={!editable || cursor >= history.length - 1}
            onClick={() => setCursor((value) => Math.min(history.length - 1, value + 1))}
          >
            <Icon name="redo" />
          </Tool>
          {preview ? (
            <a className="ui-button" href={preview} download="cotizacion-borrador.pdf">
              <Icon name="download" size={16} /> Descargar borrador
            </a>
          ) : null}
          {canWrite ? (
            <Button
              variant="primary"
              disabled={!dirty || busy}
              loading={busy}
              disabledReason={dirty ? undefined : "No hay cambios sin guardar"}
              onClick={() => void save()}
              title="Solo esta obra: las demás cotizaciones y los documentos emitidos no cambian"
            >
              Guardar diseño · solo esta obra
            </Button>
          ) : null}
        </div>
      </header>
      {status ? (
        <p className="quotation-document__status" role="status">
          {status}
        </p>
      ) : null}
      <div className="quotation-document__body">
        <div className="quotation-document__sheet" aria-busy={rendering}>
          {preview ? (
            <iframe
              title="Vista previa del borrador de la cotización"
              src={`${preview}#view=FitH`}
            />
          ) : previewError ? (
            <div className="quotation-document__empty">
              <Icon name="document" size={24} />
              <p>{previewError}</p>
            </div>
          ) : (
            <Loading label="Preparando la vista previa" />
          )}
          {preview && previewError ? (
            <p className="quotation-document__stale" role="alert">
              {previewError}
            </p>
          ) : null}
          {rendering && preview ? (
            <span className="quotation-document__refresh">Actualizando…</span>
          ) : null}
        </div>
        <aside className="quotation-document__inspector" aria-label="Diseño del documento">
          <fieldset disabled={!editable}>
            <legend>Diseño</legend>
            <div className="quotation-document__templates" role="radiogroup" aria-label="Diseño">
              {TEMPLATES.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  role="radio"
                  aria-checked={item.value === template}
                  className="quotation-document__template"
                  onClick={() => patch({ template: item.value, order: undefined })}
                >
                  <TemplateGlyph template={item.value} />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
            <p className="quotation-document__hint">{selected?.detail}</p>
          </fieldset>
          <fieldset disabled={!editable}>
            <legend>Bloques</legend>
            <ol className="quotation-document__blocks">
              {order.map((block, index) => {
                const locked = REQUIRED.includes(block);
                const off = hidden.has(block);
                return (
                  <li key={block} data-off={off || undefined}>
                    <span>{BLOCK_LABEL[block]}</span>
                    <Tool
                      label={`Subir ${BLOCK_LABEL[block]}`}
                      disabled={index === 0}
                      onClick={() => move(block, -1)}
                    >
                      <Icon name="chevronUp" size={16} />
                    </Tool>
                    <Tool
                      label={`Bajar ${BLOCK_LABEL[block]}`}
                      disabled={index === order.length - 1}
                      onClick={() => move(block, 1)}
                    >
                      <Icon name="chevronDown" size={16} />
                    </Tool>
                    <Tool
                      label={
                        locked
                          ? `${BLOCK_LABEL[block]} siempre visible`
                          : off
                            ? `Mostrar ${BLOCK_LABEL[block]}`
                            : `Ocultar ${BLOCK_LABEL[block]}`
                      }
                      disabled={locked}
                      onClick={() => toggle(block)}
                    >
                      <Icon name={off ? "eyeOff" : "eye"} size={16} />
                    </Tool>
                  </li>
                );
              })}
            </ol>
          </fieldset>
          <fieldset disabled={!editable}>
            <legend>Textos</legend>
            {(
              [
                ["intro", "Presentación", "Ej.: Gracias por considerarnos para su obra."],
                ["notes", "Notas en condiciones", "Información adicional para el cliente."],
                ["closing", "Cierre", "Ej.: Quedamos atentos a sus comentarios."],
              ] as const
            ).map(([key, label, placeholder]) => (
              <Field key={key} label={label} htmlFor={`quotation-text-${key}`}>
                <textarea
                  id={`quotation-text-${key}`}
                  className="ui-field__input"
                  rows={3}
                  maxLength={2000}
                  value={texts[key]}
                  placeholder={placeholder}
                  onChange={(event) =>
                    setTexts((value) => ({ ...value, [key]: event.target.value }))
                  }
                  onBlur={commitTexts}
                />
              </Field>
            ))}
          </fieldset>
          <fieldset disabled={!editable}>
            <legend>Presentación</legend>
            <SegmentedControl
              label="Tamaño de los dibujos"
              value={merged.drawing_size ?? "M"}
              options={[
                { value: "S", label: "Pequeño" },
                { value: "M", label: "Medio" },
                { value: "L", label: "Grande" },
              ]}
              onValueChange={(value) => patch({ drawing_size: value as "S" | "M" | "L" })}
            />
            <Switch
              label="Mostrar precio unitario"
              checked={merged.unit_prices !== false}
              onCheckedChange={(checked) => patch({ unit_prices: checked })}
            />
          </fieldset>
          <div className="quotation-document__more">
            <p className="quotation-document__hint">
              Ámbito: «Guardar diseño» afecta solo a esta obra. El diseño de la empresa es el
              predeterminado de las nuevas cotizaciones y no cambia documentos emitidos ni obras con
              su propio diseño.
            </p>
            <Button
              variant="ghost"
              disabled={!editable || sameLayout(layout, {})}
              onClick={() => change({})}
            >
              Usar el diseño de la empresa
            </Button>
            {isOwner ? (
              <Button
                variant="ghost"
                disabled={busy || !companyVersion}
                onClick={() => void saveForCompany()}
              >
                Guardar como predeterminado de la empresa
              </Button>
            ) : null}
          </div>
          {!prepared ? (
            <p className="quotation-document__hint">
              Guarda las condiciones de la cotización para poder guardar su diseño.
            </p>
          ) : null}
        </aside>
      </div>
    </section>
  );
}

/** Compact icon action with its name as the accessible label and tooltip. */
function Tool({
  label,
  children,
  ...props
}: Omit<ButtonProps, "aria-label" | "title"> & { label: string }): JSX.Element {
  return (
    <Button
      {...props}
      variant="ghost"
      size="compact"
      className="ui-icon-button"
      aria-label={label}
      title={label}
    >
      {children}
    </Button>
  );
}

/** Small schematic of each composition, drawn with tokens. */
function TemplateGlyph({ template }: { template: QuotationTemplateEnum }): JSX.Element {
  return (
    <svg className="quotation-document__glyph" viewBox="0 0 40 52" aria-hidden="true">
      <rect x="1" y="1" width="38" height="50" rx="2" className="glyph-sheet" />
      <rect x="5" y="5" width="14" height="3" className="glyph-ink" />
      <rect x="27" y="5" width="8" height="3" className="glyph-ink" />
      {template === "PROYECTO" ? (
        <>
          <rect x="5" y="12" width="14" height="12" className="glyph-fill" />
          <rect x="22" y="14" width="13" height="2" className="glyph-ink" />
          <rect x="22" y="19" width="10" height="2" className="glyph-ink" />
          <rect x="5" y="28" width="30" height="2" className="glyph-ink" />
          <rect x="5" y="33" width="30" height="2" className="glyph-ink" />
          <rect x="5" y="38" width="30" height="2" className="glyph-ink" />
          <rect x="5" y="43" width="30" height="2" className="glyph-ink" />
        </>
      ) : template === "ALTERNATIVAS" ? (
        <>
          <rect x="5" y="12" width="14" height="16" className="glyph-fill" />
          <rect x="21" y="12" width="14" height="16" className="glyph-line" />
          <rect x="5" y="32" width="30" height="2" className="glyph-ink" />
          <rect x="5" y="37" width="30" height="2" className="glyph-ink" />
          <rect x="5" y="42" width="20" height="2" className="glyph-ink" />
        </>
      ) : (
        <>
          {[12, 22, 32, 42].map((y) => (
            <g key={y}>
              <rect x="5" y={y} width="7" height="7" className="glyph-fill" />
              <rect x="15" y={y + 1} width="20" height="2" className="glyph-ink" />
              <rect x="15" y={y + 4} width="14" height="2" className="glyph-ink" />
            </g>
          ))}
        </>
      )}
    </svg>
  );
}

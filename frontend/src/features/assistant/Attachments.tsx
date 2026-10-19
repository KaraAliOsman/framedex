import { useEffect, useRef, useState } from "react";

import { aiAttachmentGet, aiAttachmentsUpload } from "../../api/generated/dekopen";
import type { AiAttachmentDetail } from "../../api/generated/models/aiAttachmentDetail";
import { Icon } from "../../ui/Icon";
import { supabase } from "../../auth/supabaseClient";

/** Files attached from the copilot composer (dirección final 05 · 3.1).
 *
 * Common to every AI plan: PDF, PNG/JPEG/WebP, XLSX/CSV, DOCX, TXT/Markdown.
 * Each file uploads as soon as it is added (upload, preview and reopening
 * never call the model) and can be removed before sending. Sent files stay
 * attached to their turn with their hash and coverage; reopening a citation
 * streams the private file again, so an expired link never breaks it. */

export const ACCEPT = ".pdf,.png,.jpg,.jpeg,.webp,.xlsx,.xlsm,.csv,.docx,.txt,.md,.markdown";
const MAX_FILES = 6;
const MAX_BYTES = 40 * 1024 * 1024;

export type ComposerAttachment = {
  key: string;
  name: string;
  size: number;
  state: "uploading" | "ready" | "error";
  id?: string;
  kind?: string;
  status?: string;
  coverage?: string;
  error?: string;
  /** Local object URL for an image thumbnail (never persisted). */
  preview?: string;
};

const KIND_LABEL: Record<string, string> = {
  PDF: "PDF",
  IMAGE: "Imagen",
  XLSX: "Planilla",
  CSV: "CSV",
  DOCX: "Documento",
  TEXT: "Texto",
};

function kindLabel(kind: string | undefined): string {
  return (kind && KIND_LABEL[kind]) || "Archivo";
}

const MEGABYTES = new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 });

function itemClass(item: ComposerAttachment): string {
  return `copilot-attach__item is-${item.state === "ready" ? "ready" : item.state === "error" ? "error" : "uploading"}`;
}

function sizeLabel(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${MEGABYTES.format(bytes / (1024 * 1024))} MB`;
}

const PLURAL: Record<string, string> = {
  página: "páginas",
  línea: "líneas",
  fila: "filas",
  elemento: "elementos",
  imagen: "imágenes",
};

function unitPlural(unit: string, total: number): string {
  if (!unit) return "partes";
  return total === 1 ? unit : (PLURAL[unit] ?? unit);
}

function coverageText(coverage: {
  unit: string;
  total: number;
  processed: number;
  unprocessed_count: number;
  visual_count: number;
}): string {
  const parts: string[] = [];
  if (coverage.total)
    parts.push(
      `${coverage.processed} de ${coverage.total} ${unitPlural(coverage.unit, coverage.total)}`,
    );
  if (coverage.visual_count) parts.push(`${coverage.visual_count} con lectura visual`);
  if (coverage.unprocessed_count) parts.push(`${coverage.unprocessed_count} sin procesar`);
  return parts.join(" · ");
}

function errorText(payload: unknown): string {
  const detail = (payload as { error?: { detail?: unknown } } | null)?.error?.detail;
  return typeof detail === "string" ? detail : "No se pudo subir el archivo.";
}

export function AttachmentTray({
  organizationId,
  threadId,
  items,
  onChange,
}: {
  organizationId: string;
  threadId: string | null;
  items: ComposerAttachment[];
  onChange: (
    next: ComposerAttachment[] | ((previous: ComposerAttachment[]) => ComposerAttachment[]),
  ) => void;
}): JSX.Element {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(
    () => () => {
      for (const item of items) if (item.preview) URL.revokeObjectURL(item.preview);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- revoke on unmount only
    [],
  );

  function add(files: File[]): void {
    setNotice("");
    const room = MAX_FILES - items.length;
    if (room <= 0) {
      setNotice(`Puedes adjuntar hasta ${MAX_FILES} archivos por mensaje.`);
      return;
    }
    for (const file of files.slice(0, room)) {
      const key = `${file.name}:${file.size}:${crypto.randomUUID()}`;
      if (file.size > MAX_BYTES) {
        onChange((previous) => [
          ...previous,
          { key, name: file.name, size: file.size, state: "error", error: "Supera 40 MB." },
        ]);
        continue;
      }
      const preview = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
      onChange((previous) => [
        ...previous,
        { key, name: file.name, size: file.size, state: "uploading", preview },
      ]);
      void aiAttachmentsUpload(
        { file, ...(threadId ? { thread_id: threadId } : {}) },
        { headers: { "X-Organization-ID": organizationId } },
      )
        .then((response) => {
          onChange((previous) =>
            previous.map((item) => {
              if (item.key !== key) return item;
              if (response.status !== 201)
                return { ...item, state: "error", error: errorText(response.data) };
              const data = response.data;
              if (data.status === "UNREADABLE")
                return {
                  ...item,
                  state: "error",
                  id: data.id,
                  error: "No se pudo leer el archivo. Quítalo para continuar.",
                };
              return {
                ...item,
                state: "ready",
                id: data.id,
                kind: data.kind,
                status: data.status,
                coverage: coverageText(data.coverage),
              };
            }),
          );
        })
        .catch(() => {
          onChange((previous) =>
            previous.map((item) =>
              item.key === key
                ? { ...item, state: "error", error: "No se pudo subir el archivo." }
                : item,
            ),
          );
        });
    }
    if (files.length > room) setNotice(`Solo se agregaron ${room}; el máximo es ${MAX_FILES}.`);
  }

  function remove(key: string): void {
    onChange((previous) => {
      const found = previous.find((item) => item.key === key);
      if (found?.preview) URL.revokeObjectURL(found.preview);
      return previous.filter((item) => item.key !== key);
    });
  }

  return (
    <div
      className={`copilot-attach${dragging ? " is-dragging" : ""}`}
      onDragOver={(event) => {
        if (!event.dataTransfer.types.includes("Files")) return;
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        if (!event.dataTransfer.files.length) return;
        event.preventDefault();
        setDragging(false);
        add([...event.dataTransfer.files]);
      }}
      onPaste={(event) => {
        const files = [...event.clipboardData.files].filter((file) =>
          file.type.startsWith("image/"),
        );
        if (files.length) {
          event.preventDefault();
          add(files);
        }
      }}
    >
      {items.length ? (
        <ul className="copilot-attach__list" aria-label="Archivos adjuntos">
          {items.map((item) => (
            <li key={item.key} className={itemClass(item)}>
              {item.preview ? (
                <img className="copilot-attach__thumb" src={item.preview} alt="" />
              ) : (
                <Icon name="document" size={16} />
              )}
              <span className="copilot-attach__text">
                <strong>{item.name}</strong>
                <span>
                  {item.state === "uploading"
                    ? "Subiendo…"
                    : item.state === "error"
                      ? item.error
                      : `${kindLabel(item.kind)} · ${sizeLabel(item.size)}${item.coverage ? ` · ${item.coverage}` : ""}${
                          item.status === "PARTIAL" ? " · lectura parcial" : ""
                        }`}
                </span>
              </span>
              <button
                type="button"
                className="ui-icon-button copilot__icon"
                aria-label={`Quitar ${item.name}`}
                onClick={() => remove(item.key)}
              >
                <Icon name="close" size={16} />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="copilot-attach__bar">
        <button
          type="button"
          className="ui-button ui-button--ghost ui-button--compact"
          onClick={() => input.current?.click()}
          disabled={items.length >= MAX_FILES}
          title="PDF (texto o escaneado), PNG, JPEG, WebP, XLSX, CSV, DOCX, TXT o Markdown"
        >
          <Icon name="paperclip" size={16} />
          Adjuntar
        </button>
        <span className="copilot-attach__limits">Hasta {MAX_FILES} · 40 MB c/u</span>
        <input
          ref={input}
          type="file"
          multiple
          hidden
          accept={ACCEPT}
          onChange={(event) => {
            const files = [...(event.target.files ?? [])];
            event.target.value = "";
            if (files.length) add(files);
          }}
        />
      </div>
      {notice ? (
        <p className="copilot-attach__notice" role="status">
          {notice}
        </p>
      ) : null}
    </div>
  );
}

/** Sent files on a turn: each opens its citation viewer. */
export function SentAttachments({
  organizationId,
  items,
}: {
  organizationId: string;
  items: { id: string; file_name: string; kind: string }[];
}): JSX.Element {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="copilot-sent">
      <ul className="copilot-sent__list">
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className="copilot-sent__chip"
              aria-expanded={open === item.id}
              onClick={() => setOpen((current) => (current === item.id ? null : item.id))}
            >
              <Icon name="document" size={16} />
              {item.file_name}
            </button>
          </li>
        ))}
      </ul>
      {open ? <AttachmentViewer organizationId={organizationId} attachmentId={open} /> : null}
    </div>
  );
}

function AttachmentViewer({
  organizationId,
  attachmentId,
}: {
  organizationId: string;
  attachmentId: string;
}): JSX.Element {
  const [detail, setDetail] = useState<AiAttachmentDetail | null>(null);
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setFailed(false);
    void aiAttachmentGet(attachmentId, { headers: { "X-Organization-ID": organizationId } })
      .then((response) => {
        if (cancelled) return;
        if (response.status === 200) setDetail(response.data);
        else setFailed(true);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [attachmentId, organizationId]);

  async function openOriginal(): Promise<void> {
    // The private file is streamed by the API with the session token — the
    // link never expires inside a conversation.
    setBusy(true);
    try {
      const session = supabase ? (await supabase.auth.getSession()).data.session : null;
      const response = await fetch(`/api/v1/ai/attachments/${attachmentId}/content/`, {
        headers: {
          Authorization: `Bearer ${session?.access_token ?? ""}`,
          "X-Organization-ID": organizationId,
        },
      });
      if (!response.ok) throw new Error("content");
      const url = URL.createObjectURL(await response.blob());
      window.open(url, "_blank", "noopener");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  if (failed)
    return <p className="copilot-viewer copilot-viewer--error">No pudimos abrir el archivo.</p>;
  if (!detail) return <p className="copilot-viewer">Cargando archivo…</p>;
  return (
    <div className="copilot-viewer">
      <p className="copilot-viewer__head">
        <strong>{detail.file_name}</strong>
        <span>
          {kindLabel(detail.kind)} · {coverageText(detail.coverage)} · SHA-256{" "}
          {detail.file_sha256.slice(0, 12)}
        </span>
      </p>
      {detail.unprocessed.length ? (
        <p className="copilot-viewer__warn">
          Sin procesar: {detail.unprocessed.slice(0, 12).join(", ")}
        </p>
      ) : null}
      {detail.parts.length ? (
        <ol className="copilot-viewer__parts">
          {detail.parts.slice(0, 40).map((part, index) => (
            <li key={`${part.ref}-${index}`}>
              <span className="copilot-viewer__ref">{part.ref}</span>
              <span>{part.text.slice(0, 400)}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p>Lectura visual: el contenido se interpreta como imagen.</p>
      )}
      <button
        type="button"
        className="ui-button ui-button--ghost ui-button--compact"
        disabled={busy}
        onClick={() => void openOriginal()}
      >
        Abrir original
      </button>
    </div>
  );
}

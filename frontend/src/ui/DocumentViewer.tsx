import { lazy, Suspense, useEffect, useState } from "react";
import { Dialog } from "./Dialog";
import "./DocumentViewer.css";

const PdfPreview = lazy(() => import("./PdfPreview"));

/** Private bytes stay in a local object URL, revoked when the viewer closes. */
export function DocumentViewer({
  blob,
  filename,
  title,
  page,
  onClose,
}: {
  blob: Blob;
  filename: string;
  title: string;
  page?: number;
  onClose(): void;
}): JSX.Element {
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const pdf = blob.type.includes("pdf") || /\.pdf$/i.test(filename);
  const image = /^image\/(png|jpeg|webp)$/.test(blob.type);
  useEffect(() => {
    const local = URL.createObjectURL(blob);
    setUrl(local);
    let active = true;
    if (blob.type.startsWith("text/") && blob.size < 2_000_000) {
      void blob.text().then((value) => {
        if (active) setText(value);
      });
    }
    return () => {
      active = false;
      URL.revokeObjectURL(local);
    };
  }, [blob]);
  return (
    <Dialog
      title={title}
      width="l"
      onClose={onClose}
      footer={
        <>
          <a className="ui-button ui-button--primary" href={url || undefined} download={filename}>
            Descargar archivo
          </a>
          <button type="button" className="ui-button" onClick={onClose}>
            Cerrar
          </button>
        </>
      }
    >
      <div className="document-viewer">
        {url && pdf ? (
          <Suspense fallback={<p role="status">Abriendo PDF…</p>}>
            <PdfPreview blob={blob} title={title} page={page} />
          </Suspense>
        ) : url && image ? (
          <img alt={title} src={url} />
        ) : text ? (
          <pre>{text}</pre>
        ) : (
          <p>El archivo está listo para descargar y abrir en su aplicación.</p>
        )}
      </div>
    </Dialog>
  );
}

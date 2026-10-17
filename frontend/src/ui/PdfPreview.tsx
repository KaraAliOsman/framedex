import { useEffect, useRef, useState } from "react";
import {
  getDocument,
  GlobalWorkerOptions,
  type PDFDocumentLoadingTask,
  type PDFDocumentProxy,
  type RenderTask,
} from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

// Version the module request separately from the asset bytes so a cached
// response from an older server's .mjs MIME mapping cannot strand the viewer.
GlobalWorkerOptions.workerSrc = `${workerUrl}?module=1`;

/** Render private bytes locally, including in browsers without a PDF plugin. */
export default function PdfPreview({
  blob,
  title,
  page = 1,
  onReady,
}: {
  blob: Blob;
  title: string;
  page?: number;
  onReady?(ready: boolean): void;
}): JSX.Element {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [currentPage, setCurrentPage] = useState(page);
  const [zoom, setZoom] = useState(1);
  const [width, setWidth] = useState(0);
  const [rendering, setRendering] = useState(true);
  const [error, setError] = useState("");
  const [text, setText] = useState("");
  const stageRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let active = true;
    let loading: PDFDocumentLoadingTask | undefined;
    setDocument(null);
    setError("");
    onReady?.(false);
    void (async () => {
      const data = new Uint8Array(await blob.arrayBuffer());
      if (!active) return;
      loading = getDocument({ data, enableXfa: false });
      const loaded = await loading.promise;
      if (active) {
        setDocument(loaded);
        setCurrentPage(Math.max(1, Math.min(page, loaded.numPages)));
      }
    })().catch(() => {
      if (active) setError("No pudimos mostrar el PDF. Puedes descargarlo y volver a abrirlo.");
    });
    return () => {
      active = false;
      void loading?.destroy().catch(() => undefined);
    };
  }, [blob, page, onReady]);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const measure = () => setWidth(stage.clientWidth);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(stage);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!document || !width) return;
    let active = true;
    let task: RenderTask | undefined;
    setRendering(true);
    onReady?.(false);
    setText("");
    setError("");
    stageRef.current?.scrollTo(0, 0);
    void (async () => {
      const pdfPage = await document.getPage(currentPage);
      if (!active || !canvasRef.current) return;
      const canvas = canvasRef.current;
      const natural = pdfPage.getViewport({ scale: 1 });
      const viewport = pdfPage.getViewport({
        scale: (Math.max(1, width - 32) / natural.width) * zoom,
      });
      // Bound the backing canvas, while keeping CSS dimensions and zoom intact.
      const ratio = Math.min(
        window.devicePixelRatio || 1,
        2,
        Math.sqrt(16_000_000 / (viewport.width * viewport.height)),
        32_000 / Math.max(viewport.width, viewport.height),
      );
      canvas.width = Math.ceil(viewport.width * ratio);
      canvas.height = Math.ceil(viewport.height * ratio);
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;
      task = pdfPage.render({
        canvas,
        viewport,
        transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
      });
      await task.promise;
      if (!active) return;
      setRendering(false);
      onReady?.(true);
      const content = await pdfPage.getTextContent();
      if (active)
        setText(
          content.items
            .map((item) => ("str" in item ? item.str + (item.hasEOL ? "\n" : " ") : ""))
            .join(""),
        );
    })().catch(() => {
      if (active) {
        setRendering(false);
        onReady?.(false);
        setError("No pudimos mostrar esta página. Puedes descargar el PDF para revisarlo.");
      }
    });
    return () => {
      active = false;
      task?.cancel();
    };
  }, [document, currentPage, width, zoom, onReady]);

  return (
    <section className="pdf-preview" aria-label={title}>
      <div className="pdf-preview__toolbar" role="toolbar" aria-label="Páginas y zoom del PDF">
        <button
          type="button"
          disabled={!document || currentPage <= 1}
          onClick={() => setCurrentPage((value) => value - 1)}
        >
          Anterior
        </button>
        <span aria-live="polite">
          {document ? `Página ${currentPage} de ${document.numPages}` : "Abriendo PDF…"}
        </span>
        <button
          type="button"
          disabled={!document || currentPage >= document.numPages}
          onClick={() => setCurrentPage((value) => value + 1)}
        >
          Siguiente
        </button>
        <label>
          Zoom
          <select value={zoom} onChange={(event) => setZoom(Number(event.target.value))}>
            <option value={1}>Ajustar al ancho</option>
            <option value={0.5}>50 % del ancho</option>
            <option value={0.75}>75 % del ancho</option>
            <option value={1.25}>125 % del ancho</option>
            <option value={1.5}>150 % del ancho</option>
            <option value={2}>200 % del ancho</option>
          </select>
        </label>
      </div>
      <div className="pdf-preview__stage" ref={stageRef} aria-busy={rendering && !error}>
        {error ? <p role="alert">{error}</p> : null}
        {!document && !error ? <p role="status">Preparando la vista del documento…</p> : null}
        <canvas
          ref={canvasRef}
          role="img"
          aria-label={`${title}, página ${currentPage}`}
          hidden={!document || !!error}
        />
      </div>
      {text ? (
        <details className="pdf-preview__text">
          <summary>Texto de esta página</summary>
          <pre>{text}</pre>
        </details>
      ) : null}
    </section>
  );
}

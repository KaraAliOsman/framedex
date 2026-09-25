/** §06-G — manufacturer section drawing import.
 *
 * Upload a DXF/SVG → the backend detects closed outlines → the reviewer
 * picks the right one and CONFIRMS the drawing→mm scale (guessed only from
 * declared units) → the polygon lands in the section editor as
 * DXF_REFERENCE with the stored document as its drawing_ref. Detection is
 * evidence for a human decision — nothing here writes authority by itself.
 */
import { useMemo, useRef, useState } from "react";

import type { SectionImportCandidate, SectionImportResponse } from "../../api/generated/models";
import { t, type TranslationKey } from "../../i18n/es-CL";
import type { catalogApi } from "./catalogModel";

export interface SectionImportPick {
  vertices: { x_mm: string; y_mm: string }[];
  drawingRef: string;
}

function bbox(points: [string, string][]): { minX: number; minY: number; w: number; h: number } {
  const xs = points.map(([x]) => Number(x));
  const ys = points.map(([, y]) => Number(y));
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  return { minX, minY, w: Math.max(...xs) - minX, h: Math.max(...ys) - minY };
}

function CandidatePreview({
  points,
  className,
}: {
  points: [string, string][];
  className?: string;
}): JSX.Element {
  const box = bbox(points);
  const pad = Math.max(box.w, box.h) * 0.05 || 1;
  const path = points.map(([x, y], index) => `${index === 0 ? "M" : "L"}${x} ${y}`).join(" ");
  return (
    <svg
      className={className}
      viewBox={`${box.minX - pad} ${box.minY - pad} ${box.w + 2 * pad} ${box.h + 2 * pad}`}
      aria-hidden="true"
    >
      <path
        d={`${path} Z`}
        fill="none"
        stroke="currentColor"
        strokeWidth={Math.max(box.w, box.h) / 120}
      />
    </svg>
  );
}

export function SectionImportPanel({
  api,
  onApply,
  onClose,
}: {
  api: ReturnType<typeof catalogApi>;
  onApply: (pick: SectionImportPick) => void;
  onClose: () => void;
}): JSX.Element {
  const ct = (key: string) => t(`catalog.sectionImport.${key}` as TranslationKey);
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SectionImportResponse | null>(null);
  const [pickedIndex, setPickedIndex] = useState<number | null>(null);
  const [scale, setScale] = useState("");

  const picked: SectionImportCandidate | null =
    result && pickedIndex !== null
      ? (result.candidates.find((candidate) => candidate.index === pickedIndex) ?? null)
      : null;

  const scaleValue = useMemo(() => {
    const value = Number(scale.replace(",", "."));
    return Number.isFinite(value) && value > 0 ? value : null;
  }, [scale]);

  const scaledPoints = useMemo(() => {
    if (!picked || scaleValue === null) return null;
    return picked.points.map(([x, y]) => ({
      x_mm: (Number(x) * scaleValue).toFixed(3),
      y_mm: (Number(y) * scaleValue).toFixed(3),
    }));
  }, [picked, scaleValue]);

  const scaledBox = useMemo(() => {
    if (!scaledPoints) return null;
    return bbox(scaledPoints.map((point) => [point.x_mm, point.y_mm]));
  }, [scaledPoints]);

  async function upload(file: File) {
    setBusy(true);
    setError("");
    setResult(null);
    setPickedIndex(null);
    setScale("");
    try {
      const data = await api.sectionImport(file);
      setResult(data);
      setScale(data.mm_per_unit ?? "");
      if (data.candidates.length === 1) setPickedIndex(data.candidates[0]!.index);
    } catch (cause) {
      const code = cause instanceof Error ? cause.message : "";
      setError(code.startsWith("section_") ? ct(`error.${code}`) : ct("error.failed"));
    } finally {
      setBusy(false);
    }
  }

  function confirm() {
    if (!result || !picked || !scaledPoints) return;
    onApply({ vertices: scaledPoints, drawingRef: result.document_path });
  }

  return (
    <section className="section-import" aria-label={ct("title")}>
      <header className="catalog-toolbar">
        <h4>{ct("title")}</h4>
        <button type="button" onClick={onClose}>
          {ct("close")}
        </button>
      </header>
      <p>{ct("help")}</p>

      <input
        ref={inputRef}
        type="file"
        accept=".dxf,.svg,image/svg+xml"
        disabled={busy}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void upload(file);
          event.target.value = "";
        }}
      />
      {busy && <p role="status">{ct("uploading")}</p>}
      {error && <p role="alert">{error}</p>}

      {result && (
        <>
          {result.warnings.length > 0 && (
            <ul className="section-import-warnings">
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
          <p>{ct("pick")}</p>
          <ul className="section-import-candidates">
            {result.candidates.map((candidate) => (
              <li key={candidate.tag}>
                <button
                  type="button"
                  aria-pressed={pickedIndex === candidate.index}
                  className="section-import-candidate"
                  onClick={() => setPickedIndex(candidate.index)}
                >
                  <CandidatePreview points={candidate.points as [string, string][]} />
                  <span>{candidate.tag}</span>
                </button>
              </li>
            ))}
          </ul>

          {picked && (
            <div className="section-import-confirm">
              <label htmlFor="section-import-scale">
                <span>{ct("scale")}</span>
                <input
                  id="section-import-scale"
                  type="text"
                  required
                  inputMode="decimal"
                  pattern="[0-9]+([.,][0-9]+)?"
                  value={scale}
                  onChange={(event) => setScale(event.target.value)}
                />
              </label>
              <small>{ct("scaleHelp")}</small>
              {scaledPoints && scaledBox && (
                <div className="section-import-preview">
                  <CandidatePreview
                    points={scaledPoints.map((point) => [point.x_mm, point.y_mm])}
                    className="section-import-preview-figure"
                  />
                  <p>
                    {ct("preview")}: {scaledBox.w.toFixed(1)} × {scaledBox.h.toFixed(1)} mm
                  </p>
                </div>
              )}
              <button type="button" className="primary" disabled={!scaledPoints} onClick={confirm}>
                {ct("apply")}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

import { useEffect, useRef, useState } from "react";
import { ValidatedForm } from "../../ui";

type Detector = { detect: (source: HTMLVideoElement) => Promise<{ rawValue: string }[]> };
type DetectorConstructor = new (options: { formats: string[] }) => Detector;

export function PieceScanner({
  value,
  onChange,
  onScan,
  busy,
}: {
  value: string;
  onChange: (value: string) => void;
  onScan: (value: string) => void;
  busy: boolean;
}) {
  const [camera, setCamera] = useState(false);
  const [error, setError] = useState("");
  const video = useRef<HTMLVideoElement>(null);
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;
  const Detector = (window as Window & { BarcodeDetector?: DetectorConstructor }).BarcodeDetector;
  const available = !!Detector && !!navigator.mediaDevices?.getUserMedia;
  useEffect(() => {
    if (!camera || !Detector) return;
    let active = true,
      stream: MediaStream | undefined,
      timer: ReturnType<typeof setTimeout>;
    void navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(async (media) => {
        if (!active) {
          media.getTracks().forEach((track) => track.stop());
          return;
        }
        stream = media;
        if (!video.current) return;
        video.current.srcObject = media;
        await video.current.play();
        const detector = new Detector({ formats: ["qr_code"] });
        const scan = async () => {
          if (!active || !video.current) return;
          try {
            const hits = await detector.detect(video.current);
            if (!active) return;
            if (hits[0]?.rawValue) {
              onScanRef.current(hits[0].rawValue);
              setCamera(false);
              return;
            }
            timer = setTimeout(() => void scan(), 250);
          } catch {
            if (active) {
              setError("No se pudo leer la cámara. Ingresa el código de la etiqueta.");
              setCamera(false);
            }
          }
        };
        await scan();
      })
      .catch(() => {
        if (active) {
          setError(
            "La cámara no está disponible. Ingresa el código de la etiqueta o usa un lector USB.",
          );
          setCamera(false);
        }
      });
    return () => {
      active = false;
      clearTimeout(timer);
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, [camera, Detector]);
  return (
    <div className="production-piece-scanner">
      <ValidatedForm
        onSubmit={(event) => {
          event.preventDefault();
          onScan(value);
        }}
      >
        <label>
          Escanea la etiqueta o ingresa su código
          <input
            autoFocus
            aria-label="Código de etiqueta"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="P01-U02-M03"
          />
        </label>
        <button type="submit" disabled={busy || !value.trim()}>
          {busy ? "Buscando pieza…" : "Abrir pieza"}
        </button>
        {available ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setError("");
              setCamera(!camera);
            }}
          >
            {camera ? "Cerrar cámara" : "Escanear con cámara"}
          </button>
        ) : null}
      </ValidatedForm>
      {camera ? <video ref={video} muted playsInline aria-label="Lector de etiquetas QR" /> : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}

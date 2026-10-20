import { useEffect, useRef, useState } from "react";
import { ValidatedForm } from "../../ui";
import { Icon } from "../../ui/Icon";
import jsQR from "jsqr";

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
  const available = !!navigator.mediaDevices?.getUserMedia;
  useEffect(() => {
    if (!camera) return;
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
        const detector = Detector ? new Detector({ formats: ["qr_code"] }) : null;
        const frame = document.createElement("canvas");
        const pixels = frame.getContext("2d", { willReadFrequently: true });
        const scan = async () => {
          if (!active || !video.current) return;
          try {
            let hits: { rawValue: string }[] = [];
            if (detector) hits = await detector.detect(video.current);
            else if (pixels && video.current.videoWidth) {
              frame.width = video.current.videoWidth;
              frame.height = video.current.videoHeight;
              pixels.drawImage(video.current, 0, 0);
              const data = pixels.getImageData(0, 0, frame.width, frame.height);
              const result = jsQR(data.data, data.width, data.height);
              if (result) hits = [{ rawValue: result.data }];
            }
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
        <label className="production-scan-field">
          <Icon name="hash" size={16} />
          <input
            autoFocus
            aria-label="Código de etiqueta"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Escanea la etiqueta o escribe su código · P01-U02-M03"
          />
          {value.trim() ? (
            <button type="submit" className="production-scan-open" disabled={busy}>
              {busy ? "Buscando…" : "Abrir pieza"}
            </button>
          ) : null}
        </label>
        {available ? (
          <button
            type="button"
            className="production-scan-camera"
            aria-pressed={camera}
            disabled={busy}
            onClick={() => {
              setError("");
              setCamera(!camera);
            }}
          >
            <Icon name={camera ? "close" : "image"} size={16} />
            {camera ? "Cerrar cámara" : "Cámara"}
          </button>
        ) : null}
      </ValidatedForm>
      {camera ? <video ref={video} muted playsInline aria-label="Lector de etiquetas QR" /> : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}

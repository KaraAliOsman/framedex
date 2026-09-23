import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

import { t } from "../../i18n/es-CL";

export type SignaturePadHandle = {
  dataURL: () => string | null;
  clear: () => void;
};

const WIDTH = 480;
const HEIGHT = 160;

/** A drawn-signature capture: pointer strokes on a canvas, exported as PNG. */
const SignaturePad = forwardRef<SignaturePadHandle, { onDraw?: (hasDrawing: boolean) => void }>(
  function SignaturePad({ onDraw }, ref) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const drawing = useRef(false);
    const strokes = useRef(0);
    const [empty, setEmpty] = useState(true);

    useImperativeHandle(ref, () => ({
      dataURL: () =>
        strokes.current > 0 && canvasRef.current ? canvasRef.current.toDataURL("image/png") : null,
      clear: () => {
        const ctx = canvasRef.current?.getContext("2d");
        ctx?.clearRect(0, 0, WIDTH, HEIGHT);
        strokes.current = 0;
        setEmpty(true);
        onDraw?.(false);
      },
    }));

    useEffect(() => {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext("2d");
      if (!canvas || !ctx) return;
      ctx.strokeStyle = "#1a1f24";
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      const point = (event: PointerEvent) => {
        const rect = canvas.getBoundingClientRect();
        return {
          x: ((event.clientX - rect.left) / rect.width) * WIDTH,
          y: ((event.clientY - rect.top) / rect.height) * HEIGHT,
        };
      };
      const down = (event: PointerEvent) => {
        event.preventDefault();
        canvas.setPointerCapture(event.pointerId);
        drawing.current = true;
        const { x, y } = point(event);
        ctx.beginPath();
        ctx.moveTo(x, y);
      };
      const move = (event: PointerEvent) => {
        if (!drawing.current) return;
        const { x, y } = point(event);
        ctx.lineTo(x, y);
        ctx.stroke();
      };
      const up = (event: PointerEvent) => {
        if (!drawing.current) return;
        drawing.current = false;
        if (canvas.hasPointerCapture(event.pointerId)) {
          canvas.releasePointerCapture(event.pointerId);
        }
        strokes.current += 1;
        if (strokes.current === 1) {
          setEmpty(false);
          onDraw?.(true);
        }
      };
      canvas.addEventListener("pointerdown", down);
      canvas.addEventListener("pointermove", move);
      canvas.addEventListener("pointerup", up);
      canvas.addEventListener("pointercancel", up);
      return () => {
        canvas.removeEventListener("pointerdown", down);
        canvas.removeEventListener("pointermove", move);
        canvas.removeEventListener("pointerup", up);
        canvas.removeEventListener("pointercancel", up);
      };
    }, [onDraw]);

    return (
      <div className="signature-pad">
        <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} className="signature-pad-canvas" />
        {empty ? (
          <span className="signature-pad-hint">{t("production.deliverySignatureHint")}</span>
        ) : null}
      </div>
    );
  },
);

export default SignaturePad;

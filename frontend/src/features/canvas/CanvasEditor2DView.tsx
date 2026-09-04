import { useLayoutEffect } from "react";
import { useParams } from "react-router-dom";

import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import { CADViewportSvg } from "./CADViewportSvg";
import { useCanvasStore } from "./canvasStore";
import { CanvasTechnicalResults } from "./CanvasTechnicalResults";
import { useEngineCalculation } from "./useEngineCalculation";
import "./canvas.css";

export function CanvasEditor2DView(): JSX.Element {
  const auth = useAuthSession();
  const { id, posId } = useParams();
  const organizationId = auth.me?.active_organization?.id ?? "";
  const inputs = useCanvasStore((state) => state.inputs);
  const snapEnabled = useCanvasStore((state) => state.snapEnabled);
  const toggleSnap = useCanvasStore((state) => state.toggleSnap);
  const controller = useEngineCalculation(organizationId);

  useLayoutEffect(() => {
    const pending = controller.pendingPaint;
    if (
      pending === null ||
      controller.result === null ||
      inputs.nominalWidthMm !== pending.nominalWidthMm ||
      inputs.nominalHeightMm !== pending.nominalHeightMm
    ) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      controller.completePaint(pending.sequence, performance.now());
    });
    return () => window.cancelAnimationFrame(frame);
  }, [
    controller.completePaint,
    controller.pendingPaint,
    controller.result,
    inputs.nominalHeightMm,
    inputs.nominalWidthMm,
  ]);

  if (id !== "demo" || posId !== "g1") {
    return <p role="alert">demo_route_unavailable</p>;
  }
  if (organizationId.length === 0) return <p role="alert">active_organization_unavailable</p>;
  if (controller.fatalErrorCode !== null) {
    return <p role="alert">{controller.fatalErrorCode}</p>;
  }
  if (controller.result === null || controller.isInitialLoading) {
    return <p role="status">{t("canvas.loading")}</p>;
  }

  return (
    <div
      className="canvas-editor"
      data-testid="canvas-editor"
      data-system-id={controller.demoSystem?.id}
      data-result-width-mm={inputs.nominalWidthMm}
      data-result-height-mm={inputs.nominalHeightMm}
      data-last-commit-sequence={controller.lastMeasurement?.sequence ?? 0}
      data-last-commit-ms={controller.lastMeasurement?.durationMs.toFixed(3) ?? ""}
      aria-busy={controller.phase === "submitting" || controller.phase === "painting"}
    >
      <div className="canvas-toolbar" aria-label="Herramientas de presentación">
        <button
          type="button"
          className={snapEnabled ? "is-active" : undefined}
          aria-pressed={snapEnabled}
          onClick={toggleSnap}
        >
          Snap {snapEnabled ? "ON" : "OFF"}
        </button>
        <span>{controller.demoSystem?.name}</span>
      </div>
      {controller.commitErrorCode !== null ? (
        <p className="canvas-error" role="alert">
          {t("canvas.calculationRejected")}: {controller.commitErrorCode}
        </p>
      ) : null}
      {controller.phase === "submitting" ? (
        <p className="canvas-progress" role="status">
          {t("canvas.calculating")}
        </p>
      ) : null}
      <div className="canvas-layout">
        <CADViewportSvg
          inputs={inputs}
          response={controller.result}
          disabled={controller.phase === "submitting" || controller.phase === "painting"}
          onCommit={controller.commitDimension}
          onEditStart={controller.clearCommitError}
        />
        <CanvasTechnicalResults response={controller.result} />
      </div>
    </div>
  );
}

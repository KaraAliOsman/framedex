import { useState } from "react";
import { measurementConfirm } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { fmtMm, formatMoney } from "../../format";
import type { PositionResponse } from "../../api/generated/models";
import { actionErrorDetail } from "../errors";
import type { AxisDerivation, MeasurementRecord, MountingEvidence } from "./mountingModel";
import "./mounting.css";

export function AxisBreakdown({ axis, label }: { axis: AxisDerivation; label: string }) {
  return (
    <p className="mounting-number">
      {label}: vano {fmtMm(axis.opening_mm)}
      {[axis.first, axis.second].map((side, i) => (
        <span key={i}>
          {" "}
          − holgura {fmtMm(side.clearance_mm)} − marco {fmtMm(side.frame_mm)} − ensanche{" "}
          {fmtMm(side.extension_mm)} + traslape {fmtMm(side.overlap_mm)}
        </span>
      ))}
      {" = "}
      {fmtMm(axis.derived_mm)} mm
      {axis.fabrication_mm !== axis.derived_mm && <> · fijada: {fmtMm(axis.fabrication_mm)} mm</>}
    </p>
  );
}
export function MountingChip({ evidence }: { evidence: MountingEvidence }) {
  return (
    <p className="mounting-chip">
      <span>
        Vano{" "}
        <span className="mounting-number">
          {fmtMm(evidence.result.width.opening_mm)} × {fmtMm(evidence.result.height.opening_mm)} mm
        </span>
      </span>
      <span>
        Fabricación{" "}
        <span className="mounting-number">
          {fmtMm(evidence.result.width.fabrication_mm)} ×{" "}
          {fmtMm(evidence.result.height.fabrication_mm)} mm
        </span>
      </span>
      <span>
        {evidence.rule.name} · holguras{" "}
        <span className="mounting-number">
          {[evidence.rule.left, evidence.rule.right, evidence.rule.bottom, evidence.rule.top]
            .map((s) => fmtMm(s.clearance_mm))
            .join(" / ")}{" "}
          mm
        </span>{" "}
        (izq. / der. / abajo / arriba)
      </span>
    </p>
  );
}

export function MeasurementPanel({
  position,
  orgId,
  canConfirm,
  closed = false,
  dirty = false,
  onSaved,
}: {
  position: PositionResponse;
  orgId: string;
  canConfirm: boolean;
  closed?: boolean;
  dirty?: boolean;
  onSaved(): void;
}) {
  const record = position.measurements as MeasurementRecord | null | undefined;
  const [ack, setAck] = useState(false),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function confirm() {
    if (!record) return;
    setBusy(true);
    setError("");
    try {
      const r = await measurementConfirm(
        position.id,
        {
          expected_updated_at: position.updated_at,
          expected_generation: record.generation,
          confirmed: true,
          acknowledge_warnings: ack,
          reason,
        },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (r.status !== 200) throw new ApiError(r.status, r.data);
      onSaved();
    } catch (cause) {
      setError(actionErrorDetail(cause, "No pudimos confirmar. Recarga las medidas."));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="measurement-panel" aria-label="Estado de medidas">
      <h4>Medidas para producción</h4>
      {!record ? (
        <p>
          Sin dato: registra el vano y el montaje en el editor. La producción requiere medidas
          confirmadas.
        </p>
      ) : (
        <>
          <p role="status">
            {dirty || !record.current
              ? "Cambios pendientes: guarda y recalcula las medidas."
              : record.state === "CONFIRMED"
                ? "Confirmada para producción"
                : record.state === "SITE"
                  ? "Rectificada en obra · falta confirmar"
                  : "Cotizada con medidas del cliente · falta confirmar"}
          </p>
          {record.measurements.map((item, i) => (
            <div key={i}>
              <MountingChip evidence={item} />
              {item.result.warnings.map((w) => (
                <p className="mounting-warning" key={w}>
                  {w}
                </p>
              ))}
            </div>
          ))}
          {record.price_change?.delta_net != null && (
            <p className="mounting-number">
              Rectificación: venta neta{" "}
              {formatMoney(record.price_change.before_net!, record.price_change.currency!)} →{" "}
              {formatMoney(record.price_change.after_net!, record.price_change.currency!)} · Δ{" "}
              {formatMoney(record.price_change.delta_net, record.price_change.currency!)}
            </p>
          )}
          {closed ? (
            <p>
              La revisión emitida conserva estas medidas. Rectificar abre una nueva revisión y
              compara su precio.
            </p>
          ) : canConfirm === false ? (
            <p>
              El estimador, dueño o encargado confirma las medidas antes de emitir para producción.
            </p>
          ) : (
            record.state !== "CONFIRMED" && (
              <fieldset disabled={busy || dirty || !record.current}>
                {record.measurements.some((item) => item.result.warnings.length > 0) && (
                  <label className="mounting-check">
                    <input
                      type="checkbox"
                      checked={ack}
                      onChange={(e) => setAck(e.target.checked)}
                    />
                    Revisé los avisos de dispersión y fijación
                  </label>
                )}
                <label>
                  Responsabilidad de la confirmación
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Quién verificó la medida y en qué antecedente se apoya"
                  />
                </label>
                <button
                  disabled={
                    !reason.trim() ||
                    (record.measurements.some((item) => item.result.warnings.length > 0) && !ack)
                  }
                  onClick={() => void confirm()}
                >
                  Confirmar medidas para producción
                </button>
              </fieldset>
            )
          )}
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

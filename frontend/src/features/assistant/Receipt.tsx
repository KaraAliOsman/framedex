import type { AiReceipt } from "../../api/generated/models/aiReceipt";
import { Companion, type CompanionState } from "./Companion";

/** Final receipt of a copilot run (dirección final 05 · 5). The outcome is
 * decided server-side by typed postconditions over saved objects: Completo
 * only when every change was re-read; Parcial names the checkpoint; a
 * proposal never says «Aplicado». Tool details and checks stay folded. */

const OUTCOME: Record<string, { label: string; pose: CompanionState }> = {
  complete: { label: "Completo", pose: "success" },
  partial: { label: "Parcial", pose: "waiting" },
  proposal: { label: "Propuesta", pose: "approval" },
  blocked: { label: "Bloqueado", pose: "error" },
  answer: { label: "Respuesta", pose: "idle" },
};

const STATUS: Record<string, string> = {
  applied: "Aplicado",
  proposed: "Propuesto",
  pending: "Pendiente",
  blocked: "Bloqueado",
  undone: "Deshecho",
};

function outcomeOf(value: string): { label: string; pose: CompanionState } {
  return OUTCOME[value] ?? { label: "Resultado", pose: "idle" };
}

function statusClass(value: string): string {
  return value in STATUS ? `is-${value}` : "is-pending";
}

function statusLabel(value: string): string {
  return STATUS[value] ?? "Pendiente";
}

export function Receipt({
  receipt,
  onOpen,
}: {
  receipt: AiReceipt;
  onOpen: (path: string) => void;
}): JSX.Element | null {
  if (receipt.outcome === "answer" && !receipt.objects.length) return null;
  const outcome = outcomeOf(receipt.outcome);
  return (
    <section className={`copilot-receipt is-${receipt.outcome}`} aria-label="Recibo del trabajo">
      <header className="copilot-receipt__head">
        <Companion state={outcome.pose} size={20} />
        <strong>{outcome.label}</strong>
        <span>{receipt.summary}</span>
      </header>
      {receipt.objects.length ? (
        <ul className="copilot-receipt__objects">
          {receipt.objects.map((item) => (
            <li key={`${item.kind}-${item.id}`} className={statusClass(item.status)}>
              <span className="copilot-receipt__status">{statusLabel(item.status)}</span>
              <span className="copilot-receipt__label">
                {item.label}
                {item.cause ? <em>{item.cause}</em> : null}
              </span>
              {item.url ? (
                <button
                  type="button"
                  className="ask-dock__meta-link"
                  onClick={() => onOpen(item.url as string)}
                >
                  Abrir resultado
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {receipt.checkpoint ? (
        <p className="copilot-receipt__checkpoint">{receipt.checkpoint}</p>
      ) : null}
      {receipt.checks.length || receipt.credits !== null ? (
        <details className="ui-tech">
          <summary>Verificación y consumo</summary>
          <ul>
            {receipt.checks.map((check) => (
              <li key={check.name}>
                {check.passed ? "Verificado" : "Sin verificar"} · {check.label}
                {check.detail ? ` — ${check.detail}` : ""}
              </li>
            ))}
            {receipt.credits !== null ? <li>Consumo medido: {receipt.credits} créditos</li> : null}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

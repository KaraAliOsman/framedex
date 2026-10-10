import type { CommercialTerms } from "../../api/generated/models";
import type { DueEventEnum } from "../../api/generated/models";
import { parseDecimal, multiplyDecimal, divideByInt, formatDecimal } from "./decimal";

export function CommercialTermsEditor({
  value,
  onChange,
  disabled = false,
  idPrefix,
  required = false,
}: {
  value: CommercialTerms;
  onChange: (value: CommercialTerms) => void;
  disabled?: boolean;
  idPrefix?: string;
  required?: boolean;
}): JSX.Element {
  const schedule = value.payment_schedule ?? [];
  return (
    <fieldset disabled={disabled} className="commercial-terms-editor">
      <legend>Condiciones comerciales</legend>
      <p>
        Los montos del calendario se calculan sobre el total sellado. Revisa los hitos antes de
        emitir.
      </p>
      <div className="commercial-milestones">
        {schedule.map((milestone, index) => {
          const share = parseDecimal(milestone.share);
          const percent = share
            ? formatDecimal(multiplyDecimal(share, { numerator: 100n, denominator: 1n })).replace(
                ".",
                ",",
              )
            : milestone.share;
          const update = (change: Partial<typeof milestone>) =>
            onChange({
              ...value,
              payment_schedule: schedule.map((item, at) =>
                at === index ? { ...item, ...change } : item,
              ),
            });
          return (
            <div className="commercial-milestone" key={index}>
              <label>
                Hito {index + 1}
                <input
                  id={idPrefix ? `${idPrefix}-payment_schedule-${index}` : undefined}
                  value={milestone.label}
                  maxLength={120}
                  required
                  onChange={(event) => update({ label: event.target.value })}
                />
              </label>
              <label>
                Porcentaje (%)
                <input
                  className="technical-number"
                  inputMode="decimal"
                  required
                  value={percent}
                  onChange={(event) => {
                    const number = parseDecimal(event.target.value.replace(",", "."));
                    update({
                      share: number ? formatDecimal(divideByInt(number, 100)) : event.target.value,
                    });
                  }}
                />
              </label>
              <label>
                Vencimiento
                <select
                  value={milestone.due_event ?? ""}
                  onChange={(event) =>
                    update({ due_event: (event.target.value || null) as DueEventEnum | null })
                  }
                >
                  <option value="">Fecha declarada o sin dato</option>
                  <option value="APPROVAL">Al aprobar</option>
                  <option value="DELIVERY">Contra entrega completa</option>
                </select>
              </label>
              <label>
                Fecha acordada (opcional)
                <input
                  type="date"
                  value={milestone.due_on ?? ""}
                  onChange={(event) => update({ due_on: event.target.value || null })}
                />
              </label>
              <button
                type="button"
                className="secondary-action"
                aria-label={`Quitar hito ${index + 1}`}
                onClick={() =>
                  onChange({ ...value, payment_schedule: schedule.filter((_, at) => at !== index) })
                }
              >
                Quitar
              </button>
            </div>
          );
        })}
      </div>
      {schedule.length === 0 && (
        <p>Sin calendario de montos. Agrega los hitos acordados para imprimirlos.</p>
      )}
      {schedule.length < 12 && (
        <button
          type="button"
          className="secondary-action"
          onClick={() =>
            onChange({ ...value, payment_schedule: [...schedule, { label: "", share: "" }] })
          }
        >
          Agregar hito
        </button>
      )}
      <details>
        <summary>Plazo, instalación y condiciones legales</summary>
        {(
          [
            ["delivery_text", "Plazo de entrega", 1000],
            ["installation_text", "Instalación", 1000],
            ["exclusions", "Exclusiones", 4000],
            ["warranty", "Garantía", 4000],
            ["jurisdiction", "Jurisdicción", 1000],
          ] as const
        ).map(([field, label, length]) => (
          <label key={field}>
            {label}
            <textarea
              id={idPrefix ? `${idPrefix}-${field}` : undefined}
              required={required && field !== "jurisdiction"}
              value={value[field] ?? ""}
              maxLength={length}
              onChange={(event) => onChange({ ...value, [field]: event.target.value })}
            />
          </label>
        ))}
        <p>
          {required
            ? "Completa plazo, instalación, exclusiones y garantía antes de revisar el PDF. La jurisdicción es opcional."
            : "Una condición vacía se omite del documento. Declara los plazos y alcances acordados, sin valores supuestos."}
        </p>
      </details>
    </fieldset>
  );
}

export function validCommercialTerms(value: CommercialTerms): boolean {
  const schedule = value.payment_schedule ?? [];
  if (schedule.length === 0) return true;
  let numerator = 0n,
    denominator = 1n;
  for (const item of schedule) {
    const part = parseDecimal(item.share);
    if (!item.label.trim() || !part || part.numerator <= 0n || part.numerator > part.denominator)
      return false;
    numerator = numerator * part.denominator + part.numerator * denominator;
    denominator *= part.denominator;
  }
  return numerator === denominator;
}

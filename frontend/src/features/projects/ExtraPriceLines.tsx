import { fmtMm, formatMoney } from "../../format";
import { extraLines, extraQuantity, extraTariff, extraUnit, hasRounding } from "./extraModel";
import "./extras.css";

/** Read the commercial allocation supplied by the engine; never reprice it. */
export function ExtraPriceLines({
  lines,
  currency,
  title = "Extras incluidos",
}: {
  lines: unknown;
  currency: string;
  title?: string;
}): JSX.Element | null {
  const records = extraLines(lines);
  if (!records.length) return null;
  return (
    <table className="extra-price-lines">
      <caption>{title}</caption>
      <thead>
        <tr>
          <th>Extra</th>
          <th>Cantidad</th>
          <th>Tarifa</th>
          <th>Neto</th>
        </tr>
      </thead>
      <tbody>
        {records.map((line, index) => (
          <tr key={index}>
            <td>
              {line.name}
              {line.synthetic && " · DEMO"}
              {line.width_mm && line.height_mm && (
                <small className="extra-equation">
                  {fmtMm(line.width_mm)} × {fmtMm(line.height_mm)} mm
                </small>
              )}
              <details>
                <summary>Regla y fuente</summary>
                <p>{line.source ?? "Sin dato: revisa la autoridad de esta revisión."}</p>
              </details>
              {hasRounding(line.rounding) && (
                <small>
                  Ajuste incluido:{" "}
                  <span className="extra-equation">
                    {extraQuantity(line.rounding!)} {currency}
                  </span>
                </small>
              )}
            </td>
            <td className="extra-equation">
              {extraQuantity(line.quantity)} {extraUnit(line.unit)}
            </td>
            <td className="extra-equation">
              {extraTariff(line.unit_price ?? line.selling_rate, currency)}
            </td>
            <td className="extra-equation">{formatMoney(line.net ?? line.amount, currency)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

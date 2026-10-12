import { formatDecimal } from "../../format";
import { UnknownValue } from "../../ui";

export function AiCost({
  value,
  cause = "No hay una tarifa declarada para estas llamadas",
}: {
  value: string | null;
  cause?: string;
}): JSX.Element {
  if (value === null) return <UnknownValue cause={cause} />;
  const precision = Math.max(2, value.split(".")[1]?.replace(/0+$/, "").length ?? 0);
  return <span className="ai-number">USD {formatDecimal(value, precision)}</span>;
}

import { decimalInputValue } from "../../decimal";

/** Exact input/display conversion of a policy fraction; no numeric calculation. */
export function policyPercentInput(value: string): string {
  const [whole = "0", fraction = ""] = value.split(".");
  const digits = fraction.padEnd(2, "0");
  return decimalInputValue(
    `${BigInt(whole) * 100n + BigInt(digits.slice(0, 2))}.${digits.slice(2) || "0"}`,
  ).replace(".", ",");
}

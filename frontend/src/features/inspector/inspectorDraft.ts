import type { AnnotationRequest, InspectorDiff } from "../../api/generated/models";

function decimalIdentity(value: string): string {
  if (!/^\d+(?:\.\d+)?$/.test(value)) throw new Error("invalid_decimal");
  const [whole = "0", fraction = ""] = value.split(".");
  const trimmed = fraction.replace(/0+$/, "");
  return `${whole.replace(/^0+(?=\d)/, "")}${trimmed ? `.${trimmed}` : ""}`;
}

function sameValues(a: string[] | null | undefined, b: string[]): boolean {
  return (
    a !== null &&
    a !== undefined &&
    a.length === b.length &&
    a.every((value, index) => decimalIdentity(value) === decimalIdentity(b[index] ?? ""))
  );
}

export function previewDrainDraft(
  annotations: AnnotationRequest[],
  diff: InspectorDiff,
  widthMm: string,
): AnnotationRequest[] {
  const operation = diff.operations[0];
  if (
    diff.operations.length !== 1 ||
    operation?.kind !== "ADD_BOTTOM_DRAIN_HOLE" ||
    diff.rule_id !== "R07" ||
    decimalIdentity(diff.preconditions.opening_width_mm) !== decimalIdentity(widthMm) ||
    operation.target.bay_id !== diff.target.bay_id ||
    operation.target.leaf_id !== diff.target.leaf_id
  ) {
    throw new Error("stale_diff");
  }
  const matches = annotations.filter(
    (item) => item.bay_id === diff.target.bay_id && (item.leaf_id ?? null) === diff.target.leaf_id,
  );
  const original = matches[0];
  if (
    matches.length !== 1 ||
    original === undefined ||
    !sameValues(original.bottom_drain_holes_mm, diff.preconditions.bottom_drain_holes_mm) ||
    !sameValues(original.bottom_drain_holes_mm, operation.old_value) ||
    operation.new_value.length !== operation.old_value.length + 1 ||
    new Set(operation.new_value.map(decimalIdentity)).size !== operation.new_value.length ||
    !operation.old_value.every((value) =>
      operation.new_value.some(
        (candidate) => decimalIdentity(candidate) === decimalIdentity(value),
      ),
    )
  ) {
    throw new Error("stale_diff");
  }
  return annotations.map((item) =>
    item === original ? { ...item, bottom_drain_holes_mm: [...operation.new_value] } : { ...item },
  );
}

export function workshopReadiness(
  inspectorAllowed: boolean | undefined,
  optimizationOk: boolean,
  current: boolean,
): boolean {
  return inspectorAllowed === true && optimizationOk && current;
}

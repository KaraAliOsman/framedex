import type { CouplerChoice } from "../../api/generated/models";

export function compatibleCouplers(choices: CouplerChoice[], angle: string): CouplerChoice[] {
  const value = Math.abs(Number(angle));
  return choices.filter(
    (choice) =>
      choice.coupling_rule &&
      Number(choice.coupling_rule.min_angle_deg) <= value &&
      value <= Number(choice.coupling_rule.max_angle_deg),
  );
}

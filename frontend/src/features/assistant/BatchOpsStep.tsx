import type { AiAgentStep, DesignOperation } from "../../api/generated/models";
import { ProjectOpsStep, operationIntent } from "./ProjectOpsStep";

/** A batch uses the project's atomic preview/apply/undo transaction. */
export function BatchOpsStep({
  step,
  organizationId,
  projectId,
  settled,
  onSettled,
}: {
  step: AiAgentStep;
  organizationId: string;
  projectId: string;
  settled: boolean;
  onSettled(action: "applied" | "declined" | "apply_failed", ops: { op?: string }[]): void;
}): JSX.Element {
  const ops = (step.items ?? []).flatMap((raw) => {
    const item = raw as { position_id?: string; ops?: Record<string, unknown>[] };
    return item.position_id && item.ops?.length
      ? [
          {
            op: "apply_to_positions",
            filter: { position_ids: [item.position_id] },
            ops: item.ops.map(operationIntent),
          } as unknown as DesignOperation,
        ]
      : [];
  });
  return (
    <ProjectOpsStep
      step={{ kind: "project_ops", label: step.label, ops }}
      organizationId={organizationId}
      projectId={projectId}
      onSettled={(action, intents) => {
        if (!settled || action === "apply_failed") onSettled(action, intents);
      }}
    />
  );
}

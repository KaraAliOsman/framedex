import { useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { aiJobRetrieve } from "../../api/generated/dekopen";
import type { AiAgentStep } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { Icon } from "../../ui/Icon";
import "./operations.css";

type Child = { job_id: string; label: string; goal: string };

const SETTLED = new Set([
  "SUCCEEDED",
  "FAILED",
  "CANCELED",
  "WAITING_FOR_USER",
  "WAITING_FOR_APPROVAL",
]);
const STATE: Record<string, string> = {
  QUEUED: "En cola",
  PLANNING: "Trabajando",
  RUNNING: "Trabajando",
  WAITING_FOR_USER: "Te pregunta algo",
  WAITING_FOR_APPROVAL: "Espera tu aprobación",
  SUCCEEDED: "Listo",
  FAILED_RETRYABLE: "Se detuvo; puedes reintentar",
  FAILED: "No terminó",
  CANCELED: "Cancelado",
};

/** Independent tasks the assistant split into parallel sub-assistants. Each
 * child is its own job with its own receipt and undo, under the same
 * permissions; a child never splits again. */
export function DelegateStep({
  step,
  organizationId,
}: {
  step: AiAgentStep;
  organizationId: string;
}): JSX.Element {
  const tasks = (step.tasks ?? []) as { goal?: string; label?: string }[];
  const children = ((step.applied as { children?: Child[] } | undefined)?.children ??
    []) as Child[];
  const headers = { headers: { "X-Organization-ID": organizationId } };
  const states = useQueries({
    queries: children.map((child) => ({
      queryKey: ["ai-job-child", organizationId, child.job_id],
      queryFn: async ({ signal }: { signal: AbortSignal }) => {
        const response = await aiJobRetrieve(child.job_id, { ...headers, signal });
        if (response.status !== 200) throw new ApiError(response.status, response.data);
        return response.data.state;
      },
      refetchInterval: (query: { state: { data?: string } }) =>
        query.state.data && SETTLED.has(query.state.data) ? false : 3000,
      retry: false,
    })),
  });

  return (
    <section
      className="ask-dock__ops operation-project"
      data-state={children.length ? "applied" : "proposed"}
      aria-label={
        children.length ? "Asistentes en paralelo" : "Propuesta de asistentes en paralelo"
      }
    >
      <p className="operation-project__label">
        <Icon name={children.length ? "check" : "list"} size={16} />
        {step.label}
      </p>
      {children.length ? (
        <ul className="operation-project__changes delegate-step__children">
          {children.map((child, index) => {
            const state = states[index]?.data;
            return (
              <li key={child.job_id}>
                <Link to={`/assistant?job=${child.job_id}`}>{child.label}</Link>
                <span className="delegate-step__state" data-state={state ?? "QUEUED"}>
                  {STATE[state ?? "QUEUED"] ?? "Trabajando"}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <>
          <ul className="operation-project__changes">
            {tasks.map((task, index) => (
              <li key={index}>{task.label || task.goal}</li>
            ))}
          </ul>
          <p>Al aprobar, cada tarea corre en su propio asistente con tus mismos permisos.</p>
        </>
      )}
      {step.apply_error ? <p role="alert">{step.apply_error}</p> : null}
    </section>
  );
}

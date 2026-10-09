import { useQuery } from "@tanstack/react-query";
import { aiPresenceGet } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { AiJob, AiPresence } from "../../api/generated/models";
import type { QueryClient } from "@tanstack/react-query";
import { stableRefs, type AssistantContextValue } from "./assistantContext";
import { orbStateFor, type OrbState } from "./Orb";

export type PresenceContext = AssistantContextValue & {
  organizationId: string | null;
  userId?: string | null;
};

export function presenceKey(context: PresenceContext): readonly unknown[] {
  const refs = Object.fromEntries(
    Object.entries(stableRefs(context.refs)).sort(([a], [b]) => a.localeCompare(b)),
  );
  return [
    "ai",
    "presence",
    context.organizationId,
    context.userId ?? null,
    context.surface,
    JSON.stringify(refs),
  ];
}

/** Worker progress commits independently of the provider's transaction. */
export function presenceState(job?: Pick<AiJob, "state" | "live"> | null): OrbState {
  if (job && ["QUEUED", "PLANNING", "RUNNING"].includes(job.state)) {
    if (job.live?.state === "RUNNING") {
      return ["queued", "context", "CONSULTING_PROJECT", "CALCULATING_ENGINE"].includes(
        String(job.live.phase),
      )
        ? "thinking"
        : "working";
    }
  }
  return orbStateFor(job?.state);
}

export function useAssistantPresence(context: PresenceContext) {
  const query = useQuery<AiPresence>({
    queryKey: presenceKey(context),
    enabled: Boolean(context.organizationId),
    staleTime: 1500,
    refetchInterval: (result) =>
      result.state.data?.job &&
      ["QUEUED", "PLANNING", "RUNNING"].includes(result.state.data.job.state)
        ? 1500
        : 15000,
    queryFn: async ({ signal }) => {
      const response = await aiPresenceGet(
        { surface: context.surface, refs: JSON.stringify(stableRefs(context.refs)) },
        { signal, headers: { "X-Organization-ID": context.organizationId ?? "" } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  return { ...query, job: query.data?.job ?? null, orbState: presenceState(query.data?.job) };
}

/** Every local lifecycle read updates the same contextual indicator immediately. */
export function publishAssistantJob(
  client: QueryClient,
  context: PresenceContext,
  job: AiJob,
): void {
  client.setQueryData<AiPresence>(presenceKey(context), (previous) => ({
    context_label: previous?.context_label ?? "Contexto del trabajo",
    context_url: previous?.context_url ?? null,
    job,
  }));
}

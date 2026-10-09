import { useEffect } from "react";
import type { AiJob } from "../../api/generated/models";
import { useAssistantContext } from "./assistantContext";
import { useAssistantPresence } from "./useAssistantPresence";
import { Orb } from "./Orb";

export function AiPresence({
  organizationId,
  userId,
  size = 28,
  onActiveJob,
}: {
  organizationId: string | null;
  userId?: string | null;
  size?: number;
  onActiveJob?: (job: AiJob | null) => void;
}): JSX.Element {
  const context = useAssistantContext();
  const presence = useAssistantPresence({ ...context, organizationId, userId });
  useEffect(() => {
    onActiveJob?.(presence.job);
  }, [presence.job, onActiveJob]);
  return <Orb state={presence.orbState} size={size} title="Asistente del contexto actual" />;
}

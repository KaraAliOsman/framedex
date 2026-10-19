import { useSyncExternalStore } from "react";

import type { CompanionState } from "./Companion";

/** The copilot's current task state, shared by the popup and the shell's
 * «Asistente» button. It follows the conversation's real job — never the
 * route — and is a pure local signal: reading it calls nothing. */
type Status = { state: CompanionState; working: boolean };

let current: Status = { state: "idle", working: false };
const listeners = new Set<() => void>();

export function publishCopilotStatus(next: Status): void {
  if (next.state === current.state && next.working === current.working) return;
  current = next;
  for (const listener of listeners) listener();
}

export function useCopilotStatus(): Status {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => current,
    () => current,
  );
}

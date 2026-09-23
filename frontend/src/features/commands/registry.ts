import { useEffect, useSyncExternalStore } from "react";

import type { CommandSurface } from "./types";

/** One registered command surface at a time (the editor contributes its
 * commands while mounted). Listeners fire on register/unregister so an open
 * palette always reflects the live surface. */
let current: CommandSurface | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Register the surface's commands while the surface is mounted. Pass a
 * memoized `CommandSurface` — the palette reads it directly. */
export function useRegisterCommands(surface: CommandSurface | null): void {
  useEffect(() => {
    if (!surface) return;
    current = surface;
    emit();
    return () => {
      if (current === surface) {
        current = null;
        emit();
      }
    };
  }, [surface]);
}

export function useCommandSurface(): CommandSurface | null {
  return useSyncExternalStore(
    subscribe,
    () => current,
    () => null,
  );
}

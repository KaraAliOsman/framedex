const names = new Map<string, string>();
const listeners = new Set<() => void>();

export function projectNameCached(orgId: string, id: string): string | null {
  return names.get(`${orgId}:${id}`) ?? null;
}

export function projectNameWrite(orgId: string, id: string, name: string): void {
  names.set(`${orgId}:${id}`, name);
  listeners.forEach((listener) => {
    listener();
  });
}

/** Renames must reach already-mounted subscribers (e.g. the shell crumb)
 * — the map alone is invisible to React state. */
export function projectNameSubscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

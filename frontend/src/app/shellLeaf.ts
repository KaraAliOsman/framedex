import { createContext, useContext, useEffect } from "react";

/** The last breadcrumb is owned by the page, not the router — a position
 * editor publishes its tag («Dormitorio»), a work order could publish its
 * code. Cleared on unmount so a stale leaf never lingers on the next page. */
export const ShellLeafContext = createContext<{
  leaf: string | null;
  setLeaf(label: string | null): void;
}>({ leaf: null, setLeaf: () => undefined });

export function useShellLeaf(label: string | null): void {
  const { setLeaf } = useContext(ShellLeafContext);
  useEffect(() => {
    setLeaf(label);
    return () => setLeaf(null);
  }, [label, setLeaf]);
}

import { useEffect, useLayoutEffect, useRef } from "react";

const floatingLayers = new Set<() => void>();
/** Opening a new operational layer dismisses the previous one. */
export function useFloatingLayer(open: boolean, onClose: () => void): void {
  const close = useRef(onClose);
  useLayoutEffect(() => {
    close.current = onClose;
  });
  useEffect(() => {
    if (!open) return;
    const dismiss = () => close.current();
    for (const previous of floatingLayers) previous();
    floatingLayers.add(dismiss);
    return () => {
      floatingLayers.delete(dismiss);
    };
  }, [open]);
}

// Authentication must erase a loaded editor synchronously without downloading
// the editor in public proposals. An unloaded store starts with empty state.
let resetLoadedCanvas: (() => void) | undefined;

export function registerCanvasReset(reset: () => void): void {
  resetLoadedCanvas = reset;
}

export function resetCanvasSession(): void {
  resetLoadedCanvas?.();
}

import { useEffect, useState } from "react";
import { Dialog } from "../ui";
import { formatShortcut, useCommandSurface } from "../features/commands/registry";

export function ShortcutHelp(): JSX.Element {
  const [open, setOpen] = useState(false);
  const surface = useCommandSurface();
  useEffect(() => {
    const show = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (
        event.key !== "?" ||
        event.ctrlKey ||
        event.metaKey ||
        event.altKey ||
        target?.closest("input, textarea, select, [contenteditable=true]")
      )
        return;
      event.preventDefault();
      window.dispatchEvent(new Event("dekopen:shell-overlay"));
      setOpen(true);
    };
    window.addEventListener("keydown", show);
    const dismiss = () => setOpen(false);
    window.addEventListener("dekopen:shell-overlay", dismiss);
    return () => {
      window.removeEventListener("keydown", show);
      window.removeEventListener("dekopen:shell-overlay", dismiss);
    };
  }, []);
  return (
    <>
      <button
        type="button"
        className="topbar-button topbar-button--icon"
        aria-label="Ayuda de atajos"
        title="Ayuda de atajos · ?"
        onClick={() => {
          window.dispatchEvent(new Event("dekopen:shell-overlay"));
          setOpen(true);
        }}
      >
        ?
      </button>
      {open && (
        <Dialog onClose={() => setOpen(false)} title="Atajos de teclado">
          <dl className="shell-shortcuts">
            <div>
              <dt>Buscar entidades o ejecutar un comando</dt>
              <dd>
                <kbd>Ctrl K</kbd> · <kbd>/</kbd>
              </dd>
            </div>
            <div>
              <dt>Recorrer resultados</dt>
              <dd>
                <kbd>↑</kbd> <kbd>↓</kbd>
              </dd>
            </div>
            <div>
              <dt>Elegir el resultado</dt>
              <dd>
                <kbd>Intro</kbd>
              </dd>
            </div>
            <div>
              <dt>Cerrar el panel</dt>
              <dd>
                <kbd>Esc</kbd>
              </dd>
            </div>
            {(surface?.commands ?? [])
              .filter((command) => command.shortcut)
              .map((command) => (
                <div key={command.id}>
                  <dt>{command.title}</dt>
                  <dd>
                    <kbd>{formatShortcut(command.shortcut!)}</kbd>
                  </dd>
                </div>
              ))}
          </dl>
          <p>
            Los comandos de diseño usan el mismo registro de operaciones del editor y del asistente.
          </p>
        </Dialog>
      )}
    </>
  );
}

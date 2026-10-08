import { useEffect, useRef, type ReactNode } from "react";
import { useFloatingLayer } from "../../ui/floatingLayer";

/** Non-modal CAD panel: fields leave the drawing available; Escape returns
 * focus to the control that opened it. Only one operational layer is open. */
export function EditorFlyout({
  title,
  onClose,
  children,
  className = "",
  id,
}: {
  title: string;
  onClose(): void;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  const panel = useRef<HTMLDivElement>(null);
  const source = useRef(document.activeElement);
  const close = useRef(onClose);
  close.current = onClose;
  useFloatingLayer(true, onClose);
  useEffect(() => {
    const dismiss = (event: PointerEvent) => {
      const target = event.target as Element;
      if (
        !panel.current?.contains(target) &&
        !target.closest(".position-strip, .assembly-tools, .editor-bottom")
      )
        close.current();
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close.current();
        if (source.current instanceof HTMLElement) source.current.focus();
      }
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", escape);
    };
  }, []);
  return (
    <div
      id={id}
      ref={panel}
      className={`editor-flyout ${className}`}
      role="region"
      aria-label={title}
    >
      <header>
        <h3>{title}</h3>
        <button type="button" aria-label={`Cerrar ${title}`} onClick={onClose}>
          ×
        </button>
      </header>
      {children}
    </div>
  );
}

import {
  cloneElement,
  type ReactElement,
  type ReactNode,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Dialog } from "./Dialog";
import { useFloatingLayer } from "./floatingLayer";

function FloatingSurface({
  anchor,
  children,
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { anchor: React.RefObject<HTMLElement> }): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const [point, setPoint] = useState({ left: 8, top: 8 });
  useLayoutEffect(() => {
    function place(): void {
      const source = anchor.current?.getBoundingClientRect();
      const target = ref.current?.getBoundingClientRect();
      if (!source || !target) return;
      const left = Math.max(8, Math.min(source.left, innerWidth - target.width - 8));
      const below = source.bottom + 4;
      const top = Math.max(
        8,
        below + target.height <= innerHeight - 8 ? below : source.top - target.height - 4,
      );
      setPoint({ left, top });
    }
    place();
    const observer = new ResizeObserver(place);
    if (ref.current) observer.observe(ref.current);
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [anchor]);
  return createPortal(
    <div
      {...props}
      ref={ref}
      className={className}
      style={{ ...point, position: "fixed" }}
      data-density={anchor.current?.closest<HTMLElement>("[data-density]")?.dataset.density}
      data-theme={anchor.current?.closest<HTMLElement>("[data-theme]")?.dataset.theme}
    >
      {children}
    </div>,
    document.body,
  );
}

export function Popover({
  trigger,
  label,
  children,
}: {
  trigger: ReactElement<{ onClick?: React.MouseEventHandler }>;
  label: string;
  children: ReactNode;
}): JSX.Element {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLSpanElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const id = useId();
  useFloatingLayer(open, () => setOpen(false));
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => {
      if (
        !container.current?.contains(event.target as Node) &&
        !panel.current?.contains(event.target as Node)
      )
        setOpen(false);
    };
    const key = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        setOpen(false);
        container.current?.querySelector<HTMLButtonElement>("button")?.focus();
      }
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", key);
    };
  }, [open]);
  return (
    <span
      ref={container}
      className="ui-popover-anchor"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          setOpen(false);
          container.current?.querySelector<HTMLButtonElement>("button")?.focus();
        }
      }}
    >
      {cloneElement(trigger, {
        onClick: (event: React.MouseEvent) => {
          trigger.props.onClick?.(event);
          setOpen((value) => !value);
        },
        ...{ "aria-expanded": open, "aria-controls": open ? id : undefined },
      })}
      {open ? (
        <FloatingSurface
          anchor={container}
          className="ui-popover"
          id={id}
          role="region"
          aria-label={label}
        >
          <div ref={panel}>{children}</div>
        </FloatingSurface>
      ) : null}
    </span>
  );
}

export function Tooltip({ text, children }: { text: string; children: ReactElement }): JSX.Element {
  const [open, setOpen] = useState(false);
  const anchor = useRef<HTMLSpanElement>(null);
  const id = useId();
  return (
    <span
      ref={anchor}
      className="ui-tooltip-anchor"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") setOpen(false);
      }}
    >
      {cloneElement(children, { "aria-describedby": open ? id : undefined })}
      {open ? (
        <FloatingSurface anchor={anchor} className="ui-tooltip" role="tooltip" id={id}>
          {text}
        </FloatingSurface>
      ) : null}
    </span>
  );
}

export type MenuItem = {
  id: string;
  label: string;
  shortcut?: string;
  danger?: boolean;
  disabledReason?: string;
} & ({ onSelect: () => void; href?: never } | { href: string; onSelect?: never });
function MenuList({
  items,
  close,
  label,
}: {
  items: readonly MenuItem[];
  close: () => void;
  label: string;
}): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.querySelector<HTMLElement>("[role='menuitem']:not([disabled])")?.focus();
  }, []);
  return (
    <div
      role="menu"
      aria-label={label}
      className="ui-menu"
      ref={ref}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          close();
        }
        if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const options = Array.from(
          ref.current?.querySelectorAll<HTMLElement>("[role='menuitem']:not([disabled])") ?? [],
        );
        const index = options.indexOf(document.activeElement as HTMLElement);
        const next =
          event.key === "Home"
            ? 0
            : event.key === "End"
              ? options.length - 1
              : (index + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
        options[next]?.focus();
      }}
    >
      {items.map((item) =>
        item.href ? (
          <a
            className="ui-menu__item"
            key={item.id}
            role="menuitem"
            href={item.href}
            onClick={close}
          >
            {item.label}
            {item.shortcut ? <kbd>{item.shortcut}</kbd> : null}
          </a>
        ) : (
          <button
            className={`ui-menu__item ${item.danger ? "is-danger" : ""}`}
            type="button"
            key={item.id}
            role="menuitem"
            disabled={Boolean(item.disabledReason)}
            title={item.disabledReason}
            onClick={() => {
              item.onSelect?.();
              close();
            }}
          >
            {item.label}
            {item.shortcut ? <kbd>{item.shortcut}</kbd> : null}
          </button>
        ),
      )}
    </div>
  );
}

export function Menu({ label, items }: { label: string; items: readonly MenuItem[] }): JSX.Element {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  useFloatingLayer(open, () => setOpen(false));
  function close(): void {
    setOpen(false);
    ref.current?.querySelector<HTMLButtonElement>("button")?.focus();
  }
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => {
      if (
        !ref.current?.contains(event.target as Node) &&
        !panel.current?.contains(event.target as Node)
      )
        setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);
  return (
    <span className="ui-popover-anchor" ref={ref}>
      <button
        type="button"
        className="ui-button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {label}
      </button>
      {open ? (
        <FloatingSurface anchor={ref} className="ui-popover">
          <div ref={panel}>
            <MenuList label={label} items={items} close={close} />
          </div>
        </FloatingSurface>
      ) : null}
    </span>
  );
}

export function ContextMenu({
  label,
  items,
  children,
}: {
  label: string;
  items: readonly MenuItem[];
  children: ReactNode;
}): JSX.Element {
  const [point, setPoint] = useState<{ x: number; y: number } | null>(null);
  const anchor = useRef<HTMLDivElement>(null);
  useFloatingLayer(point !== null, () => setPoint(null));
  useEffect(() => {
    if (!point) return;
    const dismiss = (event: PointerEvent) => {
      if (!(event.target as Element).closest(".ui-context-menu")) setPoint(null);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [point]);
  function close(): void {
    setPoint(null);
    anchor.current?.focus();
  }
  return (
    <div
      ref={anchor}
      tabIndex={0}
      aria-label={label}
      className="ui-context-anchor"
      onContextMenu={(event) => {
        event.preventDefault();
        setPoint({
          x: Math.min(event.clientX, innerWidth - 260),
          y: Math.min(event.clientY, innerHeight - items.length * 44 - 16),
        });
      }}
      onKeyDown={(event) => {
        if (event.shiftKey && event.key === "F10") {
          event.preventDefault();
          const box = anchor.current!.getBoundingClientRect();
          setPoint({ x: box.left, y: box.bottom });
        }
      }}
    >
      {children}
      {point
        ? createPortal(
            <div
              className="ui-context-menu"
              style={{ left: Math.max(8, point.x), top: Math.max(8, point.y) }}
            >
              <MenuList label={label} items={items} close={close} />
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}

export function Drawer({
  title,
  onClose,
  children,
  footer,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}): JSX.Element {
  return (
    <Dialog title={title} onClose={onClose} footer={footer} surface="drawer">
      {children}
    </Dialog>
  );
}

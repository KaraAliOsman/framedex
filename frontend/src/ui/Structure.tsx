import { type HTMLAttributes, type ReactNode, useEffect, useId, useRef } from "react";
import { Button, type ButtonProps } from "./Controls";
import { Tooltip } from "./Overlays";

export function IconButton({
  label,
  shortcut,
  icon,
  ...props
}: Omit<ButtonProps, "children" | "icon" | "aria-label" | "title"> & {
  label: string;
  shortcut: string;
  icon: ReactNode;
}): JSX.Element {
  return (
    <Tooltip text={`${label} — ${shortcut}`}>
      <Button
        {...props}
        className={`ui-icon-button ${props.className ?? ""}`}
        aria-label={label}
        title={`${label} — ${shortcut}`}
      >
        {icon}
      </Button>
    </Tooltip>
  );
}
export function ButtonGroup({
  region,
  children,
}: {
  region: string;
  children: ReactNode;
}): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!import.meta.env.DEV) return;
    const check = () => {
      const buttons = ref.current?.querySelectorAll<HTMLButtonElement>(".ui-button--primary");
      if (
        buttons &&
        Array.from(buttons).filter((button) => !button.hidden && !button.closest("[hidden]"))
          .length > 1
      )
        console.warn(`DEKOPEN: más de una acción principal en ${region}`);
    };
    check();
    const observer = new MutationObserver(check);
    if (ref.current)
      observer.observe(ref.current, { childList: true, subtree: true, attributes: true });
    return () => observer.disconnect();
  }, [region]);
  return (
    <div
      ref={ref}
      className="ui-button-group"
      data-region={region}
      role="group"
      aria-label={region}
    >
      {children}
    </div>
  );
}
export function Panel({
  title,
  children,
  action,
  className = "",
  ...props
}: Omit<HTMLAttributes<HTMLElement>, "title"> & {
  title: string;
  action?: ReactNode;
}): JSX.Element {
  const id = useId();
  return (
    <section
      {...props}
      className={`ui-panel ${className}`}
      aria-labelledby={id}
      data-region={props["id"] ?? id}
    >
      <header className="ui-panel__header">
        <h2 id={id}>{title}</h2>
        {action}
      </header>
      {children}
    </section>
  );
}
export const Section = Panel;
export type InspectorGroup = {
  id: string;
  title: string;
  content: ReactNode;
  advanced?: boolean;
  open?: boolean;
};
export function Inspector({
  title = "Propiedades",
  groups,
}: {
  title?: string;
  groups: readonly InspectorGroup[];
}): JSX.Element {
  return (
    <aside className="ui-inspector" aria-label={title} data-region="inspector">
      <h2>{title}</h2>
      {groups
        .filter((group) => !group.advanced)
        .map((group) => (
          <details key={group.id} open={group.open ?? true}>
            <summary>{group.title}</summary>
            {group.content}
          </details>
        ))}
      {groups.some((group) => group.advanced) ? (
        <details>
          <summary>Avanzado</summary>
          {groups
            .filter((group) => group.advanced)
            .map((group) => (
              <section key={group.id}>
                <h3>{group.title}</h3>
                {group.content}
              </section>
            ))}
        </details>
      ) : null}
    </aside>
  );
}
export function KeyValue({ label, children }: { label: string; children: ReactNode }): JSX.Element {
  return (
    <div className="ui-key-value">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
export function Stepper({
  steps,
  current,
  completed = false,
}: {
  steps: readonly { id: string; label: string; onSelect?: () => void; disabledReason?: string }[];
  current: string;
  completed?: boolean;
}): JSX.Element {
  const index = steps.findIndex((step) => step.id === current);
  return (
    <ol className="ui-stepper" aria-label="Ciclo de vida">
      {steps.map((step, position) => (
        <li
          key={step.id}
          aria-current={!completed && step.id === current ? "step" : undefined}
          data-complete={completed || position < index || undefined}
        >
          {step.onSelect ? (
            <Button
              variant="ghost"
              onClick={step.onSelect}
              disabled={Boolean(step.disabledReason)}
              disabledReason={step.disabledReason}
            >
              {step.label}
            </Button>
          ) : (
            <span>{step.label}</span>
          )}
        </li>
      ))}
    </ol>
  );
}
export function Stat({
  label,
  value,
  decision,
}: {
  label: string;
  value: ReactNode;
  decision: { label: string; onClick: () => void } | null;
}): JSX.Element | null {
  if (!decision) return null;
  return (
    <div className="ui-stat">
      <span className="ui-spec-label">{label}</span>
      <strong className="ui-value">{value}</strong>
      <Button variant="ghost" onClick={decision.onClick}>
        {decision.label}
      </Button>
    </div>
  );
}

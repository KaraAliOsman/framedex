import { type InputHTMLAttributes, type ReactNode, useId, useRef, useState } from "react";
import { type SelectOption } from "./Controls";
import { useFloatingLayer } from "./floatingLayer";

export function Checkbox({
  label,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: ReactNode }): JSX.Element {
  return (
    <label className="ui-check">
      <input {...props} type="checkbox" />
      <span>{label}</span>
    </label>
  );
}
export function Radio({
  label,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: ReactNode }): JSX.Element {
  return (
    <label className="ui-check">
      <input {...props} type="radio" />
      <span>{label}</span>
    </label>
  );
}
export function Switch({
  label,
  checked,
  onCheckedChange,
  disabled = false,
}: {
  label: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
}): JSX.Element {
  return (
    <label className="ui-switch">
      <input
        type="checkbox"
        role="switch"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onCheckedChange(event.target.checked)}
      />
      <span className="ui-switch__track" aria-hidden />
      <span>{label}</span>
    </label>
  );
}

export function SegmentedControl({
  label,
  value,
  options,
  onValueChange,
  disabled = false,
}: {
  label: string;
  value: string;
  options: readonly SelectOption[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
}): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const selected = Math.max(
    0,
    options.findIndex((option) => option.value === value),
  );
  return (
    <div
      ref={ref}
      className="ui-segmented"
      role="radiogroup"
      aria-label={label}
      onKeyDown={(event) => {
        if (
          !["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp", "Home", "End"].includes(event.key) ||
          disabled
        )
          return;
        event.preventDefault();
        const choices = options.filter((option) => !option.disabled);
        const current = choices.findIndex((option) => option.value === value);
        const index =
          event.key === "Home"
            ? 0
            : event.key === "End"
              ? choices.length - 1
              : (current +
                  (["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1) +
                  choices.length) %
                choices.length;
        const next = choices[index];
        if (next) {
          onValueChange(next.value);
          ref.current
            ?.querySelector<HTMLButtonElement>(`[data-value="${CSS.escape(next.value)}"]`)
            ?.focus();
        }
      }}
    >
      {options.map((option, index) => (
        <button
          className="ui-button"
          data-value={option.value}
          role="radio"
          aria-checked={value === option.value}
          disabled={disabled || option.disabled}
          tabIndex={index === selected ? 0 : -1}
          key={option.value}
          type="button"
          onClick={() => onValueChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Combobox({
  label,
  value,
  options,
  onValueChange,
  disabled = false,
  error,
  placeholder = "Buscar…",
}: {
  label: string;
  value: string;
  options: readonly SelectOption[];
  onValueChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
  placeholder?: string;
}): JSX.Element {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  useFloatingLayer(open, () => {
    setOpen(false);
    setQuery("");
  });
  const [active, setActive] = useState(0);
  const id = useId();
  const normalize = (text: string) =>
    text
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("es-CL");
  const filtered = options.filter((option) => normalize(option.label).includes(normalize(query)));
  const selectable = filtered.filter((option) => !option.disabled);
  const selected = options.find((option) => option.value === value);
  const current = selectable[Math.min(active, selectable.length - 1)];
  function choose(next: string): void {
    onValueChange(next);
    setQuery("");
    setOpen(false);
  }
  return (
    <label className="ui-field ui-combobox">
      <span className="ui-field__label">{label}</span>
      <input
        className="ui-field__input"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={open ? `${id}-list` : undefined}
        aria-activedescendant={open && current ? `${id}-${options.indexOf(current)}` : undefined}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        disabled={disabled}
        placeholder={placeholder}
        value={open ? query : (selected?.label ?? "")}
        onFocus={() => {
          setOpen(true);
          setQuery("");
          setActive(0);
        }}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          setActive(0);
        }}
        onBlur={() => {
          setOpen(false);
          setQuery("");
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            setOpen(false);
            setQuery("");
          }
          if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            setOpen(true);
            setActive(
              (previous) =>
                (previous + (event.key === "ArrowDown" ? 1 : -1) + selectable.length) %
                (selectable.length || 1),
            );
          }
          if (event.key === "Enter" && open) {
            event.preventDefault();
            if (current) choose(current.value);
          }
        }}
      />
      {open ? (
        <span className="ui-combobox__list" id={`${id}-list`} role="listbox" aria-label={label}>
          {filtered.length ? (
            filtered.map((option) => (
              <span
                className="ui-combobox__option"
                key={option.value}
                id={`${id}-${options.indexOf(option)}`}
                role="option"
                aria-selected={value === option.value}
                aria-disabled={option.disabled}
                data-active={current?.value === option.value || undefined}
                onPointerDown={(event) => {
                  event.preventDefault();
                  if (!option.disabled) choose(option.value);
                }}
              >
                {option.label}
              </span>
            ))
          ) : (
            <span role="status">Sin opciones compatibles</span>
          )}
        </span>
      ) : null}
      {error ? (
        <span id={`${id}-error`} role="alert" className="ui-field__error">
          {error}
        </span>
      ) : null}
    </label>
  );
}

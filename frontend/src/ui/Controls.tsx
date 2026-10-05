import {
  forwardRef,
  createContext,
  useContext,
  useId,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";

import { t } from "../i18n/es-CL";
import { formatDecimal, parseDecimalInput } from "../decimal";
import { DimLoader } from "./Signature";

/* ---------- Button ---------- */

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export type ButtonSize = "default" | "compact" | "sm" | "md" | "touch";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Busy state: shows a spinner, disables re-submission, keeps width stable. */
  loading?: boolean;
  /** Optional leading icon (svg/span). Decorative — keep labels textual. */
  icon?: ReactNode;
  /** Why the action is unavailable; rendered as title so a disabled control
   * still explains the missing condition. */
  disabledReason?: string;
};

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "ui-button--primary",
  secondary: "",
  danger: "ui-button--danger",
  ghost: "ui-button--ghost",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "secondary",
    size = "default",
    loading = false,
    icon,
    disabledReason,
    className,
    children,
    disabled,
    type = "button",
    ...rest
  },
  ref,
): JSX.Element {
  const classes = [
    "ui-button",
    VARIANT_CLASS[variant],
    size === "compact" || size === "sm" ? "ui-button--compact" : null,
    size === "touch" ? "ui-button--touch" : null,
    loading ? "is-loading" : null,
    className ?? null,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      aria-busy={loading || undefined}
      data-variant={variant}
      data-primary={variant === "primary" || undefined}
      className={classes}
      disabled={disabled || loading}
      ref={ref}
      type={type}
      {...rest}
      title={disabled ? (disabledReason ?? rest.title) : rest.title}
    >
      {loading ? <DimLoader label="Procesando la acción" /> : null}
      {!loading && icon ? <span className="ui-button__icon">{icon}</span> : null}
      {/* The label stays mounted while loading so width doesn't collapse. */}
      <span className="ui-button__label">{children}</span>
    </button>
  );
});

/* ---------- Field ---------- */

export type FieldProps = {
  /** Persistent label — never swapped for a placeholder. */
  label: string;
  htmlFor?: string;
  help?: string;
  /** Associated error; announced via aria-describedby + role=alert. */
  error?: string | null;
  required?: boolean;
  children: ReactNode;
};
const FieldContext = createContext<{
  id: string;
  describedBy?: string;
  invalid: boolean;
  required?: boolean;
} | null>(null);

export function Field({
  label,
  htmlFor,
  help,
  error,
  required,
  children,
}: FieldProps): JSX.Element {
  const autoId = useId();
  const fieldId = htmlFor ?? autoId;
  const helpId = `${fieldId}-help`;
  const errorId = `${fieldId}-error`;
  return (
    <div className={`ui-field${error ? " ui-field--invalid" : ""}`}>
      <label className="ui-field__label" htmlFor={fieldId}>
        {label}
        {required ? (
          <span aria-hidden className="ui-field__required">
            {" "}
            *
          </span>
        ) : null}
      </label>
      {/* Canonical controls inherit the label, help and error identifiers. */}
      <FieldContext.Provider
        value={{
          id: fieldId,
          describedBy:
            [help ? helpId : "", error ? errorId : ""].filter(Boolean).join(" ") || undefined,
          invalid: Boolean(error),
          required,
        }}
      >
        {children}
      </FieldContext.Provider>
      {help ? (
        <p className="ui-field__help" id={helpId}>
          {help}
        </p>
      ) : null}
      {error ? (
        <p className="ui-field__error" id={errorId} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/* ---------- inputs ---------- */

export type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  /** Trailing unit/prefix shown inside the control box (mm, %, $, UF…). */
  suffix?: string;
  prefix?: string;
  invalid?: boolean;
};

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(function TextInput(
  { suffix, prefix, invalid, className, ...rest },
  ref,
): JSX.Element {
  const field = useContext(FieldContext);
  const attributes = {
    id: field?.id,
    "aria-describedby": field?.describedBy,
    required: field?.required,
    ...rest,
  };
  const isInvalid = invalid ?? field?.invalid;
  if (suffix || prefix) {
    return (
      <span className={`ui-input-affix${isInvalid ? " is-invalid" : ""}`}>
        {prefix ? <span className="ui-input-affix__part">{prefix}</span> : null}
        <input
          aria-invalid={isInvalid || undefined}
          className={`ui-field__input ui-field__input--bare ${className ?? ""}`}
          ref={ref}
          {...attributes}
        />
        {suffix ? <span className="ui-input-affix__part">{suffix}</span> : null}
      </span>
    );
  }
  return (
    <input
      aria-invalid={isInvalid || undefined}
      className={`ui-field__input ${className ?? ""}`}
      ref={ref}
      {...attributes}
    />
  );
});

/**
 * Numeric/money/dimension input: keeps the caller's string value verbatim,
 * applies optional presentation formatting only on blur, and treats empty,
 * zero and "unknown" as distinct states (empty stays empty; zero is a real
 * number; an unavailable value stays explicitly unknown at the domain edge).
 */
export type NumberFieldProps = Omit<TextInputProps, "value" | "onChange" | "type"> & {
  value: string;
  onValueChange: (value: string) => void;
  /** Decimal places applied on blur (e.g. 0 for CLP, 1–2 for mm). The stored
   * value is untouched while typing. */
  decimals?: number;
  /** Rendered when the value is empty and the field is not focused. */
  emptyPlaceholder?: string;
};

export function NumberField({
  value,
  onValueChange,
  decimals = 2,
  suffix,
  emptyPlaceholder,
  onBlur,
  ...rest
}: NumberFieldProps): JSX.Element {
  const [focused, setFocused] = useState(false);
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState<string | null>(null);
  const errorId = useId();
  const displayed = focused ? draft : value === "" ? "" : formatDecimal(value, decimals, ".");
  return (
    <span className="ui-number-field">
      <TextInput
        {...rest}
        data-precision={decimals}
        aria-describedby={
          [rest["aria-describedby"], error ? errorId : ""].filter(Boolean).join(" ") || undefined
        }
        invalid={Boolean(error) || rest.invalid}
        inputMode="decimal"
        onBlur={(event) => {
          const parsed = parseDecimalInput(draft, decimals);
          if (draft && parsed === null) {
            setError(`Escribe un número con hasta ${decimals} decimales.`);
          } else {
            setError(null);
            setFocused(false);
          }
          onBlur?.(event);
        }}
        onChange={(event) => {
          const next = event.target.value;
          setDraft(next);
          const parsed = parseDecimalInput(next, decimals);
          if (next === "" || parsed !== null) {
            onValueChange(parsed ?? "");
            setError(null);
          }
        }}
        onFocus={(event) => {
          setDraft(value.replace(".", ","));
          setFocused(true);
          rest.onFocus?.(event);
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            setDraft(value);
            setError(null);
            setFocused(false);
          }
          if (event.key === "Enter" && draft && parseDecimalInput(draft, decimals) === null) {
            event.preventDefault();
            setError(`Escribe un número con hasta ${decimals} decimales.`);
          }
          rest.onKeyDown?.(event);
        }}
        placeholder={emptyPlaceholder}
        suffix={suffix}
        type="text"
        value={displayed}
      />
      {error ? (
        <span className="ui-field__error" id={errorId} role="alert">
          {error}
        </span>
      ) : null}
    </span>
  );
}

/* ---------- Select / combobox ---------- */

export type SelectOption = { value: string; label: string; disabled?: boolean };

export type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & {
  options: SelectOption[];
  /** Shown as a disabled first option — real hint, not a fake selection. */
  placeholder?: string;
  /** Message when the list carries no compatible option. */
  emptyMessage?: string;
  invalid?: boolean;
};

export const SelectField = forwardRef<HTMLSelectElement, SelectFieldProps>(function SelectField(
  { options, placeholder, emptyMessage, invalid, className, ...rest },
  ref,
) {
  const field = useContext(FieldContext);
  if (options.length === 0 && emptyMessage) {
    return (
      <span className="ui-field__input ui-select-empty" role="note">
        {emptyMessage}
      </span>
    );
  }
  return (
    <span className={`ui-select-wrap${invalid ? " is-invalid" : ""}`}>
      <select
        aria-invalid={invalid || field?.invalid || undefined}
        aria-describedby={field?.describedBy}
        id={field?.id}
        required={field?.required}
        className={`ui-field__input ui-select ${className ?? ""}`}
        ref={ref}
        {...rest}
      >
        {placeholder ? (
          <option disabled value="">
            {placeholder}
          </option>
        ) : null}
        {options.map((option) => (
          <option disabled={option.disabled} key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <svg aria-hidden className="ui-select__chevron" height="10" viewBox="0 0 10 6" width="10">
        <path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    </span>
  );
});

/* ---------- misc ---------- */

export function Spinner({ label }: { label?: string }): JSX.Element {
  return <DimLoader label={label ?? t("ui.loading")} />;
}

export const TextField = TextInput;
export const Select = SelectField;
export function MoneyField({
  currency = "CLP",
  ...props
}: NumberFieldProps & { currency?: "CLP" | "USD" | "UF" }): JSX.Element {
  return (
    <NumberField
      {...props}
      prefix={currency === "CLP" ? "$" : currency === "USD" ? "US$" : "UF"}
      decimals={currency === "CLP" ? 0 : currency === "USD" ? 2 : 4}
    />
  );
}

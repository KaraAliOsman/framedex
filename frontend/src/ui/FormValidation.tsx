import {
  type FormEvent,
  type FormHTMLAttributes,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { isValidEmail, isValidRut } from "../format";
import { compareDecimal, parseDecimalInput } from "../decimal";

export type Validator = (value: string) => string | null;
export const validators = {
  required: (value: string): string | null => (value.trim() ? null : "Completa este campo."),
  email: (value: string): string | null =>
    isValidEmail(value) ? null : "Revisa el correo, por ejemplo nombre@empresa.cl.",
  rut: (value: string): string | null =>
    isValidRut(value) ? null : "Revisa el RUT y su dígito verificador.",
  decimal:
    (precision = 2): Validator =>
    (value) =>
      !value.trim() || parseDecimalInput(value, precision) !== null
        ? null
        : `Escribe un número con hasta ${precision} decimales.`,
};
export type FormErrors = {
  id: string;
  label: string;
  message: string;
  control: HTMLElement;
  originalAriaLabel: string | null;
}[];

export function useSpanishValidation(schema: Readonly<Record<string, Validator>> = {}): {
  errors: FormErrors;
  validate: (form: HTMLFormElement) => boolean;
  clear: (control?: EventTarget | null) => void;
} {
  const [errors, setErrors] = useState<FormErrors>([]);
  const prefix = useId();
  const pendingFocus = useRef<HTMLElement | null>(null);
  useLayoutEffect(() => {
    for (const error of errors) {
      error.control.setAttribute("aria-invalid", "true");
      // Keep the control's name stable when its visible error is inside a legacy label.
      if (
        error.originalAriaLabel === null &&
        !error.control.closest(".ui-field") &&
        !error.control.hasAttribute("aria-labelledby")
      )
        error.control.setAttribute("aria-label", error.label);
      const description = error.control.getAttribute("aria-describedby") ?? "";
      error.control.setAttribute("aria-describedby", `${description} ${error.id}-error`.trim());
    }
    if (pendingFocus.current) {
      const control = pendingFocus.current;
      pendingFocus.current = null;
      control.focus();
      const target = control.closest(".ui-field") ?? control.closest("label") ?? control;
      target.scrollIntoView?.({ block: "center", behavior: "instant" });
    }
    return () => {
      for (const error of errors) {
        error.control.removeAttribute("aria-invalid");
        if (error.originalAriaLabel === null) error.control.removeAttribute("aria-label");
        const ids = (error.control.getAttribute("aria-describedby") ?? "")
          .split(/\s/)
          .filter((id) => id !== `${error.id}-error`);
        if (ids.filter(Boolean).length)
          error.control.setAttribute("aria-describedby", ids.filter(Boolean).join(" "));
        else error.control.removeAttribute("aria-describedby");
      }
    };
  }, [errors]);
  function validate(form: HTMLFormElement): boolean {
    const found: FormErrors = [];
    const controls = Array.from(form.elements).filter(
      (element): element is HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement =>
        element instanceof HTMLInputElement ||
        element instanceof HTMLSelectElement ||
        element instanceof HTMLTextAreaElement,
    );
    controls.forEach((control, index) => {
      if (control.disabled || control.type === "hidden" || control.type === "submit") return;
      const value = control.value;
      const labelNode = control.labels?.[0]?.cloneNode(true) as HTMLElement | undefined;
      labelNode
        ?.querySelectorAll("[data-validation-error], [aria-hidden=true]")
        .forEach((node) => node.remove());
      const label =
        labelNode?.textContent?.trim().replace(/\s+/g, " ") ??
        control.getAttribute("aria-label") ??
        "Campo";
      let message: string | null = null;
      const input = control instanceof HTMLInputElement ? control : null;
      const missingChoice =
        input?.type === "checkbox"
          ? !input.checked
          : input?.type === "radio"
            ? !controls.some(
                (other) =>
                  other instanceof HTMLInputElement &&
                  other.type === "radio" &&
                  other.name === input.name &&
                  other.checked,
              )
            : input?.type === "file"
              ? !input.files?.length
              : !value.trim();
      if (control.required && missingChoice) message = validators.required("");
      if (!message && value && input?.type === "email") message = validators.email(value);
      if (!message && value && /rut|tax_id/i.test(control.name || control.id))
        message = validators.rut(value);
      if (!message && schema[control.name]) message = schema[control.name]!(value);
      if (!message && input?.dataset.validation && value) {
        if (!new RegExp(`^(?:${input.dataset.validation})$`).test(value))
          message = input.dataset.validationMessage ?? "Revisa el formato de este campo.";
      }
      if (!message && input && (input.type === "number" || input.dataset.precision)) {
        const precision = Number(input.dataset.precision ?? "12");
        const decimal = parseDecimalInput(value, precision);
        if (value && decimal === null) message = validators.decimal(precision)(value);
        if (decimal !== null && input.min && compareDecimal(decimal, input.min) < 0)
          message = `El mínimo permitido es ${input.min}.`;
        if (decimal !== null && input.max && compareDecimal(decimal, input.max) > 0)
          message = `El máximo permitido es ${input.max}.`;
      }
      if (!message && input?.maxLength && input.maxLength > 0 && value.length > input.maxLength)
        message = `Usa hasta ${input.maxLength} caracteres.`;
      if (message) {
        if (!control.id) control.id = `${prefix}-${index}`;
        const previous = errors.find((error) => error.control === control);
        found.push({
          id: control.id,
          label,
          message,
          control,
          originalAriaLabel: previous
            ? previous.originalAriaLabel
            : control.getAttribute("aria-label"),
        });
      }
    });
    setErrors(found);
    pendingFocus.current = found[0]?.control ?? null;
    return found.length === 0;
  }
  return {
    errors,
    validate,
    clear: (control) =>
      setErrors((current) => (control ? current.filter((error) => error.control !== control) : [])),
  };
}

/** All native forms enter through this edge; browser-language validation stays disabled. */
export function ValidatedForm({
  children,
  onSubmit,
  onInput,
  validators: schema,
  ...props
}: FormHTMLAttributes<HTMLFormElement> & {
  validators?: Readonly<Record<string, Validator>>;
}): JSX.Element {
  const { errors, validate, clear } = useSpanishValidation(schema);
  function submit(event: FormEvent<HTMLFormElement>): void {
    if (!validate(event.currentTarget)) {
      event.preventDefault();
      return;
    }
    onSubmit?.(event);
  }
  return (
    <form
      {...props}
      noValidate
      onSubmit={submit}
      onInput={(event) => {
        clear(event.target);
        onInput?.(event);
      }}
    >
      {children}
      {errors.map((error) => {
        const host =
          error.control.closest(".ui-field") ??
          error.control.closest("label") ??
          error.control.parentElement;
        return host
          ? createPortal(
              <span
                className="ui-field__error"
                id={`${error.id}-error`}
                data-validation-error
                aria-hidden="true"
              >
                {error.message}
              </span>,
              host,
              error.id,
            )
          : null;
      })}
      {errors.length ? (
        <div className="ui-form-errors" role="alert">
          <p>Revisa los campos indicados.</p>
          <ul>
            {errors.map((error) => (
              <li key={error.id}>
                <button type="button" onClick={() => error.control.focus()}>
                  {error.label}: {error.message}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </form>
  );
}

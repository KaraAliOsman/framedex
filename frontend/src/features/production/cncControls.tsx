import { Children, isValidElement, type ReactNode, type SelectHTMLAttributes } from "react";
import { SelectField } from "../../ui/Controls";
import { ApiError } from "../../api/apiMutator";

export function CncSelect({ children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  const options = Children.toArray(children).flatMap((child) => {
    if (!isValidElement<{ value: string; children: ReactNode }>(child)) return [];
    return [{ value: child.props.value, label: Children.toArray(child.props.children).join("") }];
  });
  return <SelectField {...props} options={options} />;
}
export function actionErrorDetail(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    const detail = (error.payload as { error?: { detail?: string } } | null)?.error?.detail;
    if (detail) return detail;
  }
  return fallback;
}

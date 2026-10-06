import { ApiError } from "../../api/apiMutator";
import { t } from "../../i18n/es-CL";
export function glassError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return t("glass.denied");
    const data = error.payload as { error?: { detail?: string; message?: string } };
    if (data?.error?.detail || data?.error?.message)
      return data.error.detail ?? data.error.message!;
  }
  return t("glass.error");
}

import { ApiError } from "../../api/apiMutator";
import { t, tOptional } from "../../i18n/es-CL";
export function glassError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return t("glass.denied");
    const data = error.payload as { error?: { detail?: string; message?: string } };
    const message = data?.error?.detail ?? data?.error?.message;
    if (message) {
      if (message === "catalogs.errors.validation")
        return "Revisa las medidas y la composición del vidrio antes de volver a evaluar.";
      return tOptional(message) ?? message;
    }
  }
  return t("glass.error");
}

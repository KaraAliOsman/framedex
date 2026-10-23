import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import { projectsCreate } from "../../api/generated/dekopen";

export function draftQuotationName(now = new Date()): string {
  const day = now.toLocaleDateString("es-CL", {
    day: "numeric",
    month: "long",
    timeZone: "America/Santiago",
  });
  return `Cotización del ${day}`;
}

/** The same human click starts a draft from Hoy or Obras. */
export function useNewQuotation(orgId: string) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const lock = useRef(false);
  const scope = useRef({ active: true });
  useEffect(() => {
    const current = { active: true };
    scope.current = current;
    lock.current = false;
    setCreating(false);
    setCreateError("");
    return () => {
      current.active = false;
    };
  }, [orgId]);
  async function startQuotation(): Promise<void> {
    if (lock.current) return;
    lock.current = true;
    setCreating(true);
    setCreateError("");
    const current = scope.current;
    try {
      const response = await projectsCreate(
        { name: draftQuotationName(), client_name: "" },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (!current.active) return;
      if (response.status !== 201) throw new ApiError(response.status, response.data);
      void queryClient.invalidateQueries({ queryKey: ["project-pages"] });
      navigate(`/projects/${encodeURIComponent(response.data.id)}/positions/new`);
    } catch (caught) {
      if (!current.active) return;
      setCreateError(
        caught instanceof ApiError && caught.status === 403
          ? "Tu rol no puede crear cotizaciones. Pide acceso de vendedor al dueño."
          : "No se pudo crear la cotización. Revisa la conexión y vuelve a intentarlo.",
      );
    } finally {
      if (current.active) {
        lock.current = false;
        setCreating(false);
      }
    }
  }
  return { creating, createError, startQuotation };
}

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError } from "../../api/apiMutator";
import { engineAssemblyCalculate } from "../../api/generated/dekopen";
import type {
  EngineAssemblyCalculateRequest,
  EngineAssemblyCalculateResponse,
} from "../../api/generated/models";
import type { CanvasDesignInputs } from "./canvasStore";
import { elevationEnvelopeMm } from "./productEditing";

export function assemblyRequestFromInputs(
  inputs: CanvasDesignInputs,
): EngineAssemblyCalculateRequest {
  if (inputs.systemId === null) throw new Error("Engine system has not been resolved");
  if (inputs.product === null) throw new Error("Product model is not active");
  const envelope = elevationEnvelopeMm(inputs.product);
  return {
    system_id: inputs.systemId,
    nominal_width_mm: envelope.width.toFixed(2),
    nominal_height_mm: envelope.height.toFixed(2),
    color: inputs.color,
    product: inputs.product,
  };
}

export function assemblyCalculationKey(
  organizationId: string,
  inputs: CanvasDesignInputs,
): readonly unknown[] {
  return [
    "engine-assembly-calculation",
    organizationId,
    inputs.systemId,
    inputs.color,
    inputs.product,
  ] as const;
}

function assemblyErrorCode(error: unknown): string {
  if (!(error instanceof ApiError) || typeof error.payload !== "object" || error.payload === null) {
    return "calculation_failed";
  }
  const payload = error.payload as { error?: { code?: unknown } };
  return typeof payload.error?.code === "string" ? payload.error.code : "calculation_failed";
}

/** Evaluate current intent after a short editing pause; previous geometry
 * can remain visible but never authorizes a save for a pending identity. */
export function useAssemblyCalculation(
  organizationId: string,
  inputs: CanvasDesignInputs,
  retainPrevious = true,
): {
  evaluation: EngineAssemblyCalculateResponse | null;
  currentEvaluation: EngineAssemblyCalculateResponse | null;
  isPending: boolean;
  errorCode: string | null;
  retry(): Promise<unknown>;
} {
  const identity = JSON.stringify([organizationId, inputs.systemId, inputs.color, inputs.product]);
  const [settled, setSettled] = useState(identity);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(identity), 250);
    return () => clearTimeout(timer);
  }, [identity]);
  const debouncing = settled !== identity;
  const query = useQuery({
    queryKey: assemblyCalculationKey(organizationId, inputs),
    queryFn: async () => {
      const response = await engineAssemblyCalculate(assemblyRequestFromInputs(inputs));
      if (response.status !== 200) {
        throw new Error("Generated client returned an unexpected status");
      }
      return response.data;
    },
    enabled: !debouncing && inputs.systemId !== null && inputs.product !== null,
    // A fresh product key resets data to undefined mid-fetch; keeping the
    // last valid evaluation stops the plan inset, 3D view and BOM from
    // unmounting on every canvas commit.
    placeholderData: retainPrevious ? (previous) => previous : undefined,
    retry: false,
    staleTime: Number.POSITIVE_INFINITY,
  });
  return {
    evaluation: query.data ?? null,
    currentEvaluation: debouncing || query.isPlaceholderData ? null : (query.data ?? null),
    isPending:
      inputs.systemId !== null && (debouncing || query.isPending || query.isPlaceholderData),
    errorCode: query.isError ? assemblyErrorCode(query.error) : null,
    retry: query.refetch,
  };
}

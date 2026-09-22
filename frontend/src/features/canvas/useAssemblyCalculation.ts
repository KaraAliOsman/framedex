import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../api/apiMutator";
import { engineAssemblyCalculate } from "../../api/generated/dekopen";
import type {
  EngineAssemblyCalculateRequest,
  EngineAssemblyCalculateResponse,
} from "../../api/generated/models";
import type { CanvasDesignInputs } from "./canvasStore";

export function assemblyRequestFromInputs(
  inputs: CanvasDesignInputs,
): EngineAssemblyCalculateRequest {
  if (inputs.systemId === null) throw new Error("Engine system has not been resolved");
  if (inputs.product === null) throw new Error("Product model is not active");
  const widths = inputs.product.assembly.modules.reduce(
    (total, module) => total + Number(module.width_mm),
    0,
  );
  const height = Math.max(
    ...inputs.product.assembly.modules.map((module) => Number(module.height_mm)),
  );
  return {
    system_id: inputs.systemId,
    nominal_width_mm: widths.toFixed(2),
    nominal_height_mm: height.toFixed(2),
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

/** Evaluate the compositional product through the engine (debounced by React Query keys). */
export function useAssemblyCalculation(
  organizationId: string,
  inputs: CanvasDesignInputs,
): {
  evaluation: EngineAssemblyCalculateResponse | null;
  isPending: boolean;
  errorCode: string | null;
} {
  const query = useQuery({
    queryKey: assemblyCalculationKey(organizationId, inputs),
    queryFn: async () => {
      const response = await engineAssemblyCalculate(assemblyRequestFromInputs(inputs));
      if (response.status !== 200) {
        throw new Error("Generated client returned an unexpected status");
      }
      return response.data;
    },
    enabled: inputs.systemId !== null && inputs.product !== null,
    retry: false,
    staleTime: Number.POSITIVE_INFINITY,
  });
  return {
    evaluation: query.data ?? null,
    isPending: query.isPending,
    errorCode: query.isError ? assemblyErrorCode(query.error) : null,
  };
}

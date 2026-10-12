import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { designOperationsSimulate } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { CanvasDesignInputs } from "./canvasStore";

export type EditorPrice = {
  net: string | null;
  unit_net?: string | null;
  delta_net?: string | null;
  currency: string;
  reason?: string | null;
  source?: string;
  modules?: { module_id: string; net: string | null; reason: string | null }[];
  assembly_adjustment_net?: string | null;
  breakdown_source?: string;
};

/** A no-edit simulation reads the same commercial authority as proposals.
 * Quantity multiplication and currency rounding stay in the engine. */
export function useEditorPrice(
  organizationId: string,
  inputs: CanvasDesignInputs,
  quantity: string,
  ready: boolean,
) {
  const identity = JSON.stringify([inputs.systemId, inputs.color, inputs.product, quantity]);
  const [settled, setSettled] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setSettled(identity), 350);
    return () => clearTimeout(timer);
  }, [identity]);
  const query = useQuery({
    queryKey: ["editor-price", organizationId, identity],
    enabled: ready && settled === identity && inputs.product !== null && inputs.systemId !== null,
    retry: false,
    staleTime: 0,
    queryFn: async ({ signal }) => {
      const response = await designOperationsSimulate(
        {
          system_id: inputs.systemId!,
          color: inputs.color,
          product: inputs.product,
          quantity: Number(quantity),
          ops: [],
        },
        { headers: { "X-Organization-ID": organizationId }, signal },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.price as EditorPrice;
    },
  });
  return {
    price: ready && settled === identity && !query.isError ? query.data : undefined,
    calculating: ready && (settled !== identity || query.isFetching),
    error: query.isError,
    retry: query.refetch,
  };
}

import { useQuery } from "@tanstack/react-query";
import { catalogGlassPreview } from "../../api/generated/dekopen";
import type {
  DesignOptions,
  EngineAssemblyCalculateResponse,
  GlassPreviewInputRequest,
  GlassPreviewOutput,
} from "../../api/generated/models";
import type { IntentNode } from "../canvas/intentEditing";
import { intentBays } from "../canvas/intentEditing";
import type { ProductJson } from "../canvas/productEditing";

export type GlassContext = Omit<
  GlassPreviewInputRequest,
  "system_id" | "product" | "processing" | "technical_sku"
>;
export function glassContext(
  node: IntentNode,
  moduleId: string,
  evaluation: EngineAssemblyCalculateResponse | null,
): GlassContext {
  const result = evaluation?.modules.find((item) => item.module_id === moduleId)?.result;
  const piece = result?.glasses.find((item) => item.bay_id === node.id);
  const weight = result?.leaf_weights.find(
    (item) => item.bay_id === node.id && item.leaf_id === piece?.leaf_id,
  );
  return {
    ...(piece ? { width_mm: piece.width_mm, height_mm: piece.height_mm } : {}),
    opening_type: node.opening_type ?? "FIXED",
    opening_use: node.opening_use ?? undefined,
    is_sidelight: node.is_sidelight ?? false,
    sill_height_mm: node.sill_height_mm ?? null,
    hardware_sku: node.hardware_set_sku ?? null,
    leaf_weight_kg: weight?.total_weight_kg ?? null,
    previous_infill_kg: weight?.infill_weight_kg ?? null,
  };
}
export async function requestGlassPreview(
  request: GlassPreviewInputRequest,
  signal?: AbortSignal,
): Promise<GlassPreviewOutput> {
  const response = await catalogGlassPreview(request, { signal });
  if (response.status !== 200) throw new Error("glass_preview_failed");
  return response.data;
}
export function useGlassChecks(
  orgId: string,
  product: ProductJson | null,
  options: DesignOptions | undefined,
  evaluation: EngineAssemblyCalculateResponse | null,
) {
  return useQuery({
    queryKey: [
      "glass-bay-checks",
      orgId,
      product,
      options?.system_id,
      evaluation?.calculation_hash,
    ],
    enabled: !!product && !!options,
    retry: false,
    queryFn: async ({ signal }) => {
      const entries = product!.assembly.modules.flatMap((module) =>
        intentBays(module.tree)
          .filter((node) => node.glass_product)
          .map(
            async (node) =>
              [
                module.id + "/" + node.id,
                await requestGlassPreview(
                  {
                    system_id: options!.system_id,
                    product: node.glass_product,
                    processing: node.glass_processing ?? {},
                    technical_sku: node.glass_article_sku ?? undefined,
                    ...glassContext(node, module.id, evaluation),
                  },
                  signal,
                ),
              ] as const,
          ),
      );
      return Object.fromEntries(await Promise.all(entries)) as Record<string, GlassPreviewOutput>;
    },
  });
}

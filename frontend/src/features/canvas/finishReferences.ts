import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiFetchBlob } from "../../api/apiMutator";
import { finishReferencesList, getFinishReferencesImageUrl } from "../../api/generated/dekopen";
import type { DesignOptions, FinishColor, FinishReference } from "../../api/generated/models";

export type FinishPresentation = {
  tileMm: number;
  grain: "ALONG" | "ACROSS" | "NONE";
  /** The company's own photo: shown as «Referencia del negocio». */
  reference: string;
};
export type PresentedFinishColor = FinishColor & { presentation?: FinishPresentation };

export type ReferenceTexture = FinishPresentation & { url: string; code: string };

/** The company's sample photos as object URLs keyed by the catalog finish
 * they represent. Presentation only: codes, prices and authority unchanged. */
export function useFinishReferenceTextures(orgId: string | null): Map<string, ReferenceTexture> {
  const list = useQuery({
    queryKey: ["finish-references", orgId],
    enabled: Boolean(orgId),
    staleTime: 300_000,
    retry: false,
    queryFn: async () => {
      const response = await finishReferencesList({ headers: { "X-Organization-ID": orgId! } });
      if (response.status !== 200) return [] as FinishReference[];
      return response.data.items;
    },
  });
  const [textures, setTextures] = useState<Map<string, ReferenceTexture>>(new Map());
  const signature = (list.data ?? []).map((item) => `${item.id}:${item.version}`).join("|");
  useEffect(() => {
    let alive = true;
    const created: string[] = [];
    const items = list.data ?? [];
    if (!items.length) {
      setTextures(new Map());
      return;
    }
    void Promise.all(
      items.map(async (item) => {
        try {
          const { blob } = await apiFetchBlob(getFinishReferencesImageUrl(item.id), {
            headers: orgId ? { "X-Organization-ID": orgId } : {},
          });
          const url = URL.createObjectURL(blob);
          created.push(url);
          return {
            url,
            code: item.finish_code,
            tileMm: Number(item.tile_mm),
            grain: item.grain,
            reference: item.name,
          } satisfies ReferenceTexture;
        } catch {
          return null;
        }
      }),
    ).then((loaded) => {
      if (!alive) return;
      setTextures(
        new Map(
          loaded
            .filter((item): item is ReferenceTexture => item !== null)
            .map((item) => [item.code, item]),
        ),
      );
    });
    return () => {
      alive = false;
      for (const url of created) URL.revokeObjectURL(url);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- keyed by the list signature
  }, [signature, orgId]);
  return textures;
}

/** Design options whose finish colours carry the company's photo where one
 * exists. Only presentation fields change. */
export function withFinishReferences(
  options: DesignOptions | undefined,
  textures: Map<string, ReferenceTexture>,
): DesignOptions | undefined {
  if (!options?.finish_authority || textures.size === 0) return options;
  return {
    ...options,
    finish_authority: {
      ...options.finish_authority,
      colors: options.finish_authority.colors.map((color) => {
        const texture = textures.get(color.code);
        if (!texture) return color;
        const presented: PresentedFinishColor = {
          ...color,
          texture_path: texture.url,
          presentation: {
            tileMm: texture.tileMm,
            grain: texture.grain,
            reference: texture.reference,
          },
        };
        return presented;
      }),
    },
  };
}

export function usePresentedOptions(
  orgId: string | null,
  options: DesignOptions | undefined,
): DesignOptions | undefined {
  const textures = useFinishReferenceTextures(orgId);
  return useMemo(() => withFinishReferences(options, textures), [options, textures]);
}

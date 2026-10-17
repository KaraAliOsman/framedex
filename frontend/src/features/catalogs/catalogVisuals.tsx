import { createContext, useContext, useMemo, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { catalogVisualsList } from "../../api/generated/dekopen";
import type { CatalogVisual, FinishColor, ResolvedFinish } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { withFinishMembers, type MemberGeometry } from "../canvas/members";

const NO_VISUALS: CatalogVisual[] = [];
const VisualContext = createContext<CatalogVisual[]>(NO_VISUALS);
export const catalogVisualKey = (org: string, system: string) => ["catalog-visuals", org, system];

/** Private, expiring presentation data. Never copied into a design request or issued snapshot. */
export function useCatalogVisuals(systemId: string, organizationId?: string) {
  const auth = useAuthSession();
  const org = organizationId ?? auth.me?.active_organization?.id ?? "";
  return useQuery({
    queryKey: catalogVisualKey(org, systemId),
    enabled: Boolean(org && systemId),
    staleTime: 5 * 60_000,
    refetchInterval: 10 * 60_000,
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await catalogVisualsList(
        { system_id: systemId },
        { signal, headers: { "X-Organization-ID": org } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
}

export function CatalogVisualProvider({
  systemId,
  organizationId,
  children,
}: {
  systemId: string;
  organizationId: string;
  children: ReactNode;
}) {
  const query = useCatalogVisuals(systemId, organizationId);
  return (
    <VisualContext.Provider value={query.data ?? NO_VISUALS}>{children}</VisualContext.Provider>
  );
}

export function useProfileSample(sku?: string | null): CatalogVisual | undefined {
  return useContext(VisualContext).find(
    (entry) => entry.kind === "PROFILE" && entry.target_code === sku && !entry.cleared,
  );
}

export function useTextureSample(code: string): string | undefined {
  return (
    useContext(VisualContext).find(
      (entry) => entry.kind === "TEXTURE" && entry.target_key === code && !entry.cleared,
    )?.image_url ?? undefined
  );
}

export function usePresentationMembers(base: MemberGeometry): MemberGeometry {
  const entries = useContext(VisualContext);
  return useMemo(() => {
    if (!base.finish) return base;
    const color = (value: FinishColor): FinishColor => {
      const sample = entries.find(
        (entry) => entry.kind === "TEXTURE" && entry.target_key === value.code && !entry.cleared,
      );
      return sample?.image_url
        ? { ...value, texture_path: sample.image_url, approximate: true }
        : value;
    };
    const finish: ResolvedFinish = {
      ...base.finish,
      interior: color(base.finish.interior),
      exterior: color(base.finish.exterior),
      base: base.finish.base ? color(base.finish.base) : base.finish.base,
    };
    return withFinishMembers(base, finish, base.viewFace);
  }, [base, entries]);
}

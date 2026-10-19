import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../api/apiMutator";
import { capabilitiesRetrieve } from "../../api/generated/dekopen";
import type { CapabilitiesResponse } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";

/** The server's single resolution of AI rights, support, permission and
 * availability for the active member. The UI only mirrors it; endpoints and
 * the worker gate again. Cached per organization + person so a tenant switch
 * never adopts the previous organization's answer. Reading it never calls
 * the AI provider. */
export function useCapabilities(): {
  data: CapabilitiesResponse | undefined;
  /** True only once the server confirmed the organization has the AI core. */
  aiEntitled: boolean;
  isPending: boolean;
} {
  const session = useAuthSession();
  const orgId = session.me?.active_organization?.id ?? null;
  const userId = session.me?.user?.id ?? null;
  const query = useQuery({
    queryKey: ["capabilities", orgId, userId],
    enabled: session.status === "ready" && !!orgId,
    staleTime: 60_000,
    queryFn: async ({ signal }) => {
      const response = await capabilitiesRetrieve({
        headers: { "X-Organization-ID": orgId! },
        signal,
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  return {
    data: query.data,
    aiEntitled: Boolean(query.data?.ai_entitlement.granted),
    isPending: query.isPending,
  };
}

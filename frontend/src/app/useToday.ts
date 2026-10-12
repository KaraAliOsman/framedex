import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { analyticsToday } from "../api/generated/dekopen";
import { ApiError } from "../api/apiMutator";
import { useAuthSession } from "../auth/AuthSessionProvider";

export function useToday() {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["today", org?.id, auth.me?.user.id, org?.role],
    enabled: Boolean(org),
    staleTime: 30_000,
    refetchOnWindowFocus: "always",
    queryFn: async ({ signal }) => {
      const result = await analyticsToday({ signal, headers: { "X-Organization-ID": org!.id } });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  useEffect(() => {
    const refresh = () => {
      void client.invalidateQueries({ queryKey: ["today", org?.id] });
    };
    window.addEventListener("dekopen:pricing-changed", refresh);
    return () => window.removeEventListener("dekopen:pricing-changed", refresh);
  }, [client, org?.id]);
  return query;
}

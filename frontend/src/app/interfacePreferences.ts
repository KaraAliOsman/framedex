import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { interfacePreferences, interfacePreferencesSave } from "../api/generated/dekopen";
import type {
  InterfacePreferencesResponse,
  PatchedInterfacePreferencesRequest,
} from "../api/generated/models";
import { ApiError } from "../api/apiMutator";

export const INTERFACE_DEFAULTS: InterfacePreferencesResponse = {
  density: "office",
  text_size: "normal",
  reduce_motion: false,
  project_tab: "positions",
  rail_collapsed: false,
};

export function interfaceQueryKey(orgId: string | undefined): readonly unknown[] {
  return ["interface-preferences", orgId ?? null];
}

/** How the interface looks for the signed-in person in this workshop: kept
 * on the server so it follows them across devices and the assistant can
 * change it (with undo). Presentation only. */
export function useInterfacePreferences(orgId: string | undefined): {
  preferences: InterfacePreferencesResponse;
  loaded: boolean;
  save(changes: PatchedInterfacePreferencesRequest): Promise<boolean>;
} {
  const queryClient = useQueryClient();
  const queryKey = interfaceQueryKey(orgId);
  const query = useQuery({
    queryKey,
    enabled: Boolean(orgId),
    staleTime: 5 * 60_000,
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await interfacePreferences({
        signal,
        headers: { "X-Organization-ID": orgId ?? "" },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  const preferences = query.data ?? INTERFACE_DEFAULTS;

  async function save(changes: PatchedInterfacePreferencesRequest): Promise<boolean> {
    if (!orgId) return false;
    const previous = query.data;
    queryClient.setQueryData(queryKey, { ...preferences, ...changes });
    try {
      const response = await interfacePreferencesSave(changes, {
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      queryClient.setQueryData(queryKey, response.data);
      return true;
    } catch {
      queryClient.setQueryData(queryKey, previous);
      return false;
    }
  }

  return { preferences, loaded: query.isSuccess, save };
}

/** Text size and motion live on the root: every type step is in rem and the
 * motion rule covers the whole document, overlays included. */
export function useApplyInterface(preferences: InterfacePreferencesResponse): void {
  useEffect(() => {
    const root = document.documentElement;
    if (preferences.text_size === "large") root.dataset.textSize = "large";
    else delete root.dataset.textSize;
    if (preferences.reduce_motion) root.dataset.reduceMotion = "";
    else delete root.dataset.reduceMotion;
    return () => {
      delete root.dataset.textSize;
      delete root.dataset.reduceMotion;
    };
  }, [preferences.text_size, preferences.reduce_motion]);
}

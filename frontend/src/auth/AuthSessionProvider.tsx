import type { Session } from "@supabase/supabase-js";
import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ApiError, configureApiAuthContext } from "../api/apiMutator";
import { authMe } from "../api/generated/dekopen";
import type { AuthMeResponse, Membership } from "../api/generated/models";
import { t } from "../i18n/es-CL";
import { telemetry } from "../telemetry/telemetry";
import { supabase } from "./supabaseClient";

export type AuthStatus =
  | "loading"
  | "anonymous"
  | "resolving"
  | "organization_required"
  | "mfa_required"
  | "no_membership"
  | "ready"
  | "error";

export type AuthSessionContextValue = {
  status: AuthStatus;
  session: Session | null;
  me: AuthMeResponse | null;
  memberships: Membership[];
  error: string | null;
  requestMagicLink(email: string): Promise<void>;
  selectOrganization(organizationId: string): Promise<void>;
  refreshContext(): Promise<void>;
  signOut(): Promise<void>;
};

export const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function errorCode(payload: unknown): string | null {
  if (!isRecord(payload) || !isRecord(payload.error)) {
    return null;
  }
  return typeof payload.error.code === "string" ? payload.error.code : null;
}

function membershipsFromError(payload: unknown): Membership[] {
  if (!isRecord(payload) || !Array.isArray(payload.memberships)) {
    return [];
  }
  return payload.memberships.filter(
    (item): item is Membership =>
      isRecord(item) &&
      typeof item.organization_id === "string" &&
      typeof item.organization_name === "string" &&
      typeof item.role === "string",
  );
}

function organizationStorageKey(userId: string): string {
  return `dekopen.active_org.${userId}`;
}

export function AuthSessionProvider({ children }: PropsWithChildren): JSX.Element {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [session, setSession] = useState<Session | null>(null);
  const [me, setMe] = useState<AuthMeResponse | null>(null);
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [error, setError] = useState<string | null>(null);
  const sessionRef = useRef<Session | null>(null);
  const organizationRef = useRef<string | null>(null);
  const requestGeneration = useRef(0);
  const mounted = useRef(true);

  const loadContext = useCallback(async (): Promise<void> => {
    const current = sessionRef.current;
    const generation = ++requestGeneration.current;
    const isCurrent = () =>
      mounted.current &&
      generation === requestGeneration.current &&
      sessionRef.current?.access_token === current?.access_token;
    if (current === null) {
      setStatus("anonymous");
      return;
    }
    setStatus("resolving");
    setMe(null);
    setMemberships([]);
    setError(null);
    // One bounded retry without a revoked/stale persisted selection.
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try {
        const response = await authMe();
        if (!isCurrent()) return;
        if (response.status !== 200) {
          throw new Error("Unexpected generated-client response");
        }
        setMe(response.data);
        setMemberships(response.data.memberships);
        const active = response.data.active_organization;
        if (active !== null) {
          organizationRef.current = active.id;
          window.localStorage.setItem(organizationStorageKey(current.user.id), active.id);
          telemetry.organization(active.id);
        }
        setStatus("ready");
        return;
      } catch (caught) {
        if (!isCurrent()) return;
        const code = caught instanceof ApiError ? errorCode(caught.payload) : null;
        if (
          (code === "organization_access_denied" || code === "invalid_organization_id") &&
          organizationRef.current !== null &&
          attempt === 0
        ) {
          window.localStorage.removeItem(organizationStorageKey(current.user.id));
          organizationRef.current = null;
          continue;
        }
        if (code === "organization_selection_required" && caught instanceof ApiError) {
          setMemberships(membershipsFromError(caught.payload));
          setStatus("organization_required");
        } else if (code === "mfa_required") {
          setStatus("mfa_required");
        } else if (code === "no_active_membership") {
          window.localStorage.removeItem(organizationStorageKey(current.user.id));
          organizationRef.current = null;
          setStatus("no_membership");
        } else {
          setError(t("auth.contextError"));
          setStatus("error");
        }
        return;
      }
    }
  }, []);

  useEffect(
    () =>
      configureApiAuthContext(async () => ({
        accessToken: sessionRef.current?.access_token ?? null,
        organizationId: organizationRef.current,
      })),
    [],
  );

  useEffect(() => {
    const client = supabase;
    mounted.current = true;
    if (client === null) {
      setStatus("anonymous");
      return;
    }

    let active = true;
    let observedEvent = false;
    const scheduled = new Set<number>();
    function applySession(nextSession: Session | null, signedIn: boolean): void {
      if (!active) return;
      ++requestGeneration.current;
      sessionRef.current = nextSession;
      setSession(nextSession);
      if (nextSession === null) {
        organizationRef.current = null;
        setMe(null);
        setMemberships([]);
        setError(null);
        setStatus("anonymous");
        return;
      }
      organizationRef.current = window.localStorage.getItem(
        organizationStorageKey(nextSession.user.id),
      );
      setStatus("resolving");
      // Supabase listeners are synchronous: do not acquire Auth's lock from inside one.
      const timer = window.setTimeout(() => {
        scheduled.delete(timer);
        if (!active || sessionRef.current?.access_token !== nextSession.access_token) return;
        if (signedIn) {
          telemetry.identify(nextSession.user.id);
          void client!.auth.mfa.getAuthenticatorAssuranceLevel().then(({ data: assurance }) => {
            if (active && sessionRef.current?.access_token === nextSession.access_token) {
              telemetry.capture("auth_signed_in", { aal: assurance?.currentLevel ?? "aal1" });
            }
          });
        }
        void loadContext();
      }, 0);
      scheduled.add(timer);
    }
    const { data } = client.auth.onAuthStateChange((event, nextSession) => {
      observedEvent = true;
      applySession(nextSession, event === "SIGNED_IN");
    });
    void client.auth.getSession().then(({ data: initial, error: initialError }) => {
      if (!active || observedEvent) return;
      if (initialError) {
        setError(t("auth.contextError"));
        setStatus("error");
        return;
      }
      applySession(initial.session, false);
    });
    return () => {
      active = false;
      mounted.current = false;
      ++requestGeneration.current;
      for (const timer of scheduled) window.clearTimeout(timer);
      data.subscription.unsubscribe();
    };
  }, [loadContext]);

  const value = useMemo<AuthSessionContextValue>(
    () => ({
      status,
      session,
      me,
      memberships,
      error,
      async requestMagicLink(email: string) {
        if (supabase === null) {
          throw new Error("Supabase browser configuration is missing");
        }
        const { error: signInError } = await supabase.auth.signInWithOtp({
          email,
          options: {
            shouldCreateUser: false,
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });
        if (signInError !== null) throw signInError;
        telemetry.capture("auth_magic_link_requested");
      },
      async selectOrganization(organizationId: string) {
        const current = sessionRef.current;
        if (current === null) return;
        organizationRef.current = organizationId;
        window.localStorage.setItem(organizationStorageKey(current.user.id), organizationId);
        telemetry.organization(organizationId);
        telemetry.capture("organization_selected");
        await loadContext();
      },
      refreshContext: loadContext,
      async signOut() {
        ++requestGeneration.current;
        setStatus("resolving");
        if (supabase !== null) {
          const result = await supabase.auth.signOut();
          if (result.error !== null) {
            setError(t("auth.contextError"));
            setStatus("error");
            return;
          }
        }
        telemetry.reset();
      },
    }),
    [error, loadContext, me, memberships, session, status],
  );

  return <AuthSessionContext.Provider value={value}>{children}</AuthSessionContext.Provider>;
}

export function useAuthSession(): AuthSessionContextValue {
  const context = useContext(AuthSessionContext);
  if (context === null) {
    throw new Error("useAuthSession must be used within AuthSessionProvider");
  }
  return context;
}

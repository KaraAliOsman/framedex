import type { Session } from "@supabase/supabase-js";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/apiMutator";
import { authMe } from "../api/generated/dekopen";
import { telemetry } from "../telemetry/telemetry";
import { AuthSessionProvider, useAuthSession } from "./AuthSessionProvider";

const fake = vi.hoisted(() => ({
  callback: null as ((event: string, session: Session | null) => void) | null,
  getSession: vi.fn(),
  getAssurance: vi.fn(),
  signInWithOtp: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock("./supabaseClient", () => ({
  supabase: {
    auth: {
      getSession: fake.getSession,
      onAuthStateChange: (callback: typeof fake.callback) => {
        fake.callback = callback;
        return { data: { subscription: { unsubscribe: vi.fn() } } };
      },
      signInWithOtp: fake.signInWithOtp,
      signOut: fake.signOut,
      mfa: { getAuthenticatorAssuranceLevel: fake.getAssurance },
    },
  },
}));
vi.mock("../api/generated/dekopen", () => ({ authMe: vi.fn() }));

const session = {
  access_token: "unit-session-only",
  user: { id: "unit-user" },
} as Session;

function result(org: string): Awaited<ReturnType<typeof authMe>> {
  return {
    status: 200,
    headers: new Headers(),
    data: {
      user: { id: "unit-user", email: "" },
      aal: "aal1",
      active_organization: { id: org, name: org, role: "ESTIMATOR" },
      memberships: [],
    },
  };
}

function Probe(): JSX.Element {
  const auth = useAuthSession();
  return (
    <>
      <span data-testid="status">{auth.status}</span>
      <span data-testid="active-org">{auth.me?.active_organization?.id ?? ""}</span>
      <button onClick={() => void auth.selectOrganization("org-B")}>Select B</button>
      <button onClick={() => void auth.requestMagicLink("fixture@example.com")}>Magic link</button>
    </>
  );
}

function mount(): void {
  render(
    <AuthSessionProvider>
      <Probe />
    </AuthSessionProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
  fake.callback = null;
  fake.getSession.mockResolvedValue({ data: { session }, error: null });
  fake.getAssurance.mockResolvedValue({ data: { currentLevel: "aal1" }, error: null });
  fake.signInWithOtp.mockResolvedValue({ data: {}, error: null });
  vi.mocked(authMe).mockReset().mockResolvedValue(result("org-A"));
});

describe("authoritative session and active-organization boundary", () => {
  it("resolves a session without copying its access token into a second store", async () => {
    mount();
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("ready"));
    expect(screen.getByTestId("active-org")).toHaveTextContent("org-A");
    expect(Object.keys(localStorage)).toEqual(["dekopen.active_org.unit-user"]);
    expect(localStorage.getItem("dekopen.active_org.unit-user")).toBe("org-A");
  });

  it("removes a revoked selection and retries only once to request current memberships", async () => {
    localStorage.setItem("dekopen.active_org.unit-user", "revoked-org");
    vi.mocked(authMe)
      .mockRejectedValueOnce(new ApiError(403, { error: { code: "organization_access_denied" } }))
      .mockRejectedValueOnce(
        new ApiError(409, {
          error: { code: "organization_selection_required" },
          memberships: [],
        }),
      );
    mount();
    await waitFor(() =>
      expect(screen.getByTestId("status")).toHaveTextContent("organization_required"),
    );
    expect(authMe).toHaveBeenCalledTimes(2);
    expect(localStorage.getItem("dekopen.active_org.unit-user")).toBeNull();
  });

  it("cannot restore an old authenticated context after SIGNED_OUT", async () => {
    let finish: ((value: Awaited<ReturnType<typeof authMe>>) => void) | undefined;
    vi.mocked(authMe).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    mount();
    await waitFor(() => expect(authMe).toHaveBeenCalledOnce());
    act(() => fake.callback?.("SIGNED_OUT", null));
    await act(async () => {
      finish?.(result("org-A"));
    });
    expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    expect(screen.getByTestId("active-org")).toBeEmptyDOMElement();
  });

  it("cannot overwrite active B with the delayed response for active A", async () => {
    let finishA: ((value: Awaited<ReturnType<typeof authMe>>) => void) | undefined;
    vi.mocked(authMe)
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finishA = resolve;
          }),
      )
      .mockResolvedValueOnce(result("org-B"));
    mount();
    await waitFor(() => expect(authMe).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Select B" }));
    await waitFor(() => expect(screen.getByTestId("active-org")).toHaveTextContent("org-B"));
    await act(async () => {
      finishA?.(result("org-A"));
    });
    expect(screen.getByTestId("active-org")).toHaveTextContent("org-B");
    expect(localStorage.getItem("dekopen.active_org.unit-user")).toBe("org-B");
  });

  it("does not call async Auth methods from inside onAuthStateChange", async () => {
    const capture = vi.spyOn(telemetry, "capture");
    mount();
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("ready"));
    act(() => {
      fake.callback?.("SIGNED_IN", session);
      expect(fake.getAssurance).not.toHaveBeenCalled();
    });
    await waitFor(() => expect(fake.getAssurance).toHaveBeenCalledOnce());
    expect(capture).toHaveBeenCalledWith("auth_signed_in", { aal: "aal1" });
  });

  it("requests the canonical implicit Magic Link and captures only its approved event", async () => {
    const capture = vi.spyOn(telemetry, "capture");
    mount();
    fireEvent.click(screen.getByRole("button", { name: "Magic link" }));
    await waitFor(() => expect(fake.signInWithOtp).toHaveBeenCalledOnce());
    expect(fake.signInWithOtp).toHaveBeenCalledWith({
      email: "fixture@example.com",
      options: {
        shouldCreateUser: false,
        emailRedirectTo: new URL("/auth/callback", window.location.origin).href,
      },
    });
    expect(capture).toHaveBeenCalledWith("auth_magic_link_requested");
  });
});

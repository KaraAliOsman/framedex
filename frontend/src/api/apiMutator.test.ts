import { afterEach, describe, expect, it, vi } from "vitest";

import { apiMutator, configureApiAuthContext } from "./apiMutator";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("generated API client auth mutator", () => {
  it("injects only the verified session token and selected organization", async () => {
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      expect(headers.get("Authorization")).toBe("Bearer access-token");
      expect(headers.get("X-Organization-ID")).toBe("20000000-0000-0000-0000-000000000001");
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const reset = configureApiAuthContext(async () => ({
      accessToken: "access-token",
      organizationId: "20000000-0000-0000-0000-000000000001",
    }));

    const response = await apiMutator<{ data: { ok: boolean }; status: number }>(
      "/api/v1/auth/me/",
      { method: "GET" },
    );

    expect(response.data.ok).toBe(true);
    expect(response.status).toBe(200);
    reset();
  });
});

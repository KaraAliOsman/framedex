import { afterEach, describe, expect, it, vi } from "vitest";

import {
  apiMutator,
  apiFetchBlob,
  configureApiAuthContext,
  configureCatalogChangeReview,
} from "./apiMutator";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("human review of catalog changes", () => {
  const rejected = () =>
    new Response(
      JSON.stringify({
        error: { code: "catalog_reference_changed" },
        golden_review: { review_token: "exact-diff", changes: [] },
      }),
      { status: 409, headers: { "Content-Type": "application/json" } },
    );
  it("waits for a human click, then repeats exactly the original mutation with its token", async () => {
    let click!: (token: string | null) => void;
    const review = vi.fn(
      () =>
        new Promise<string | null>((resolve) => {
          click = resolve;
        }),
    );
    const reset = configureCatalogChangeReview(review);
    const transport = vi
      .fn()
      .mockResolvedValueOnce(rejected())
      .mockResolvedValueOnce(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", transport);
    const body = JSON.stringify({ changes: [{ value: "0.01" }] });
    try {
      const pending = apiMutator("/api/v1/catalogs/series/s/cells/", { method: "PATCH", body });
      await vi.waitFor(() => expect(review).toHaveBeenCalledOnce());
      expect(transport).toHaveBeenCalledOnce();
      click("exact-diff");
      await pending;
      const [url, init] = transport.mock.calls[1]!;
      expect(url).toBe("/api/v1/catalogs/series/s/cells/");
      expect(init.body).toBe(body);
      expect(new Headers(init.headers).get("X-Catalog-Review")).toBe("exact-diff");
    } finally {
      reset();
    }
  });
  it.each([null, "exact-diff"])(
    "cancel or a second rejection never loops or silently accepts a new diff (%s)",
    async (answer) => {
      const review = vi.fn(async () => answer),
        reset = configureCatalogChangeReview(review);
      const transport = vi.fn().mockImplementation(async () => rejected());
      vi.stubGlobal("fetch", transport);
      try {
        await expect(
          apiMutator("/api/v1/catalogs/series/s/cells/", { method: "PATCH", body: "{}" }),
        ).rejects.toMatchObject({ status: 409 });
        expect(review).toHaveBeenCalledOnce();
        expect(transport).toHaveBeenCalledTimes(answer ? 2 : 1);
      } finally {
        reset();
      }
    },
  );
  it("does not replay a pending mutation into a different tenant", async () => {
    let organizationId = "org-a";
    const resetAuth = configureApiAuthContext(async () => ({
      accessToken: "token",
      organizationId,
    }));
    const resetReview = configureCatalogChangeReview(async () => {
      organizationId = "org-b";
      return "exact-diff";
    });
    const transport = vi.fn(async () => rejected());
    vi.stubGlobal("fetch", transport);
    try {
      await expect(
        apiMutator("/api/v1/catalogs/systems/s/", { method: "PATCH", body: "{}" }),
      ).rejects.toMatchObject({ payload: { error: { code: "stale_organization" } } });
      expect(transport).toHaveBeenCalledOnce();
    } finally {
      resetAuth();
      resetReview();
    }
  });
});

describe("generated API client auth mutator", () => {
  it.each([apiMutator, apiFetchBlob])(
    "rejects a request prepared for the previous tenant before transport",
    async (request) => {
      const fetchMock = vi.fn();
      vi.stubGlobal("fetch", fetchMock);
      const reset = configureApiAuthContext(async () => ({
        accessToken: "new-session",
        organizationId: "tenant-b",
      }));
      try {
        await expect(
          request("/api/v1/organization/document-preview/", {
            headers: { "X-Organization-ID": "tenant-a" },
          }),
        ).rejects.toMatchObject({
          status: 409,
          payload: { error: { code: "stale_organization" } },
        });
        expect(fetchMock).not.toHaveBeenCalled();
      } finally {
        reset();
      }
    },
  );
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

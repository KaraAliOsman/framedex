export type ApiAuthContext = {
  accessToken: string | null;
  organizationId: string | null;
};

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, payload: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

let readAuthContext: () => Promise<ApiAuthContext> = async () => ({
  accessToken: null,
  organizationId: null,
});

type CatalogReviewHandler = (payload: unknown) => Promise<string | null>;
let reviewCatalogChange: CatalogReviewHandler | null = null;

export function configureCatalogChangeReview(handler: CatalogReviewHandler): () => void {
  reviewCatalogChange = handler;
  return () => {
    if (reviewCatalogChange === handler) reviewCatalogChange = null;
  };
}

export function configureApiAuthContext(provider: () => Promise<ApiAuthContext>): () => void {
  readAuthContext = provider;
  return () => {
    readAuthContext = async () => ({ accessToken: null, organizationId: null });
  };
}

export async function apiMutator<T>(url: string, options: RequestInit): Promise<T> {
  const context = await readAuthContext();
  const headers = new Headers(options.headers);
  const requestedOrganization = headers.get("X-Organization-ID");
  if (requestedOrganization !== null && requestedOrganization !== context.organizationId) {
    throw new ApiError(409, { error: { code: "stale_organization" } });
  }
  headers.set("Accept", "application/json");
  if (context.accessToken !== null) {
    headers.set("Authorization", `Bearer ${context.accessToken}`);
  }
  if (context.organizationId !== null) {
    headers.set("X-Organization-ID", context.organizationId);
  }

  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  const contentType = response.headers.get("Content-Type") ?? "";
  const payload: unknown =
    text.length === 0 ? null : contentType.includes("application/json") ? JSON.parse(text) : text;
  if (!response.ok) {
    const rejection = payload as { error?: { code?: string }; golden_review?: unknown } | null;
    if (
      response.status === 409 &&
      rejection?.error?.code === "catalog_reference_changed" &&
      rejection.golden_review &&
      reviewCatalogChange &&
      !headers.has("X-Catalog-Review")
    ) {
      const accepted = await reviewCatalogChange(rejection.golden_review);
      if (accepted && !options.signal?.aborted) {
        headers.set("X-Catalog-Review", accepted);
        // Same URL, body and tenant; a second rejection returns to the caller.
        return apiMutator<T>(url, { ...options, headers });
      }
    }
    throw new ApiError(response.status, payload);
  }
  return { data: payload, status: response.status, headers: response.headers } as T;
}

/** Binary download through the same auth context — the generated client
 * stringifies bodies, so PDF/stream endpoints fetch the Blob directly. */
export async function apiFetchBlob(
  url: string,
  options: RequestInit = {},
): Promise<{
  blob: Blob;
  filename: string | null;
}> {
  const context = await readAuthContext();
  const headers = new Headers(options.headers);
  const requestedOrganization = headers.get("X-Organization-ID");
  if (requestedOrganization !== null && requestedOrganization !== context.organizationId) {
    throw new ApiError(409, { error: { code: "stale_organization" } });
  }
  if (context.accessToken !== null) {
    headers.set("Authorization", `Bearer ${context.accessToken}`);
  }
  if (context.organizationId !== null) {
    headers.set("X-Organization-ID", context.organizationId);
  }
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(response.status, payload);
  }
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^";\n]+)"?/.exec(disposition);
  return { blob: await response.blob(), filename: match?.[1] ?? null };
}

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

export function configureApiAuthContext(provider: () => Promise<ApiAuthContext>): () => void {
  readAuthContext = provider;
  return () => {
    readAuthContext = async () => ({ accessToken: null, organizationId: null });
  };
}

export async function apiMutator<T>(url: string, options: RequestInit): Promise<T> {
  const context = await readAuthContext();
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (context.accessToken !== null) {
    headers.set("Authorization", `Bearer ${context.accessToken}`);
  }
  if (context.organizationId !== null) {
    headers.set("X-Organization-ID", context.organizationId);
  }

  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  const payload: unknown = text.length === 0 ? null : JSON.parse(text);
  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }
  return { data: payload, status: response.status, headers: response.headers } as T;
}

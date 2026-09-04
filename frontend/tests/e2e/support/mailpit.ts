type MailpitOptions = {
  baseUrl: string;
  supabaseUrl: string;
  recipient: string;
  excludedMessageIds?: ReadonlySet<string>;
  timeoutMs?: number;
  pollIntervalMs?: number;
  fetchImpl?: typeof fetch;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function hasRecipient(message: Record<string, unknown>, recipient: string): boolean {
  return (
    Array.isArray(message.To) &&
    message.To.some(
      (address: unknown) =>
        isRecord(address) &&
        typeof address.Address === "string" &&
        address.Address.toLowerCase() === recipient.toLowerCase(),
    )
  );
}

export async function requireMailpitHealthy(
  baseUrl: string,
  fetchImpl: typeof fetch = fetch,
): Promise<void> {
  const response = await fetchImpl(`${baseUrl}/readyz`, {
    signal: AbortSignal.timeout(10_000),
  });
  if (response.status !== 200) {
    throw new Error(`Mailpit health failed with HTTP ${response.status}`);
  }
}

export async function waitForMagicLink({
  baseUrl,
  supabaseUrl,
  recipient,
  excludedMessageIds = new Set<string>(),
  timeoutMs = 30_000,
  pollIntervalMs = 250,
  fetchImpl = fetch,
}: MailpitOptions): Promise<{ id: string; link: string }> {
  const deadline = Date.now() + timeoutMs;
  const expectedOrigin = new URL(supabaseUrl).origin;
  while (Date.now() < deadline) {
    const requestTimeout = Math.max(1, Math.min(10_000, deadline - Date.now()));
    const response = await fetchImpl(`${baseUrl}/api/v1/messages`, {
      signal: AbortSignal.timeout(requestTimeout),
    });
    if (response.status !== 200) {
      throw new Error(`Mailpit listing failed with HTTP ${response.status}`);
    }
    const payload: unknown = await response.json();
    if (!isRecord(payload) || !Array.isArray(payload.messages)) {
      throw new Error("Mailpit listing does not satisfy the messages contract");
    }
    for (const message of payload.messages) {
      if (!isRecord(message) || typeof message.ID !== "string" || !message.ID) {
        throw new Error("Mailpit message is missing its server-assigned ID");
      }
      if (!hasRecipient(message, recipient) || excludedMessageIds.has(message.ID)) continue;
      const detail = await fetchImpl(
        `${baseUrl}/api/v1/message/${encodeURIComponent(message.ID)}`,
        { signal: AbortSignal.timeout(requestTimeout) },
      );
      if (detail.status !== 200) {
        throw new Error(`Mailpit body retrieval failed with HTTP ${detail.status}`);
      }
      const body: unknown = await detail.json();
      if (!isRecord(body) || body.ID !== message.ID || !hasRecipient(body, recipient)) {
        throw new Error("Mailpit body identity or recipient does not match the fixture");
      }
      const content = [body.HTML, body.Text]
        .filter((part): part is string => typeof part === "string")
        .join("\n")
        .replaceAll("&amp;", "&");
      if (!content.trim()) throw new Error("Mailpit did not return a real message body");
      const links = content.match(/https?:\/\/[^\s"'<>]+/g) ?? [];
      const link = links.find((candidate) => {
        const url = new URL(candidate);
        return (
          url.origin === expectedOrigin &&
          url.pathname === "/auth/v1/verify" &&
          Boolean(url.searchParams.get("token") || url.searchParams.get("token_hash"))
        );
      });
      if (!link) throw new Error("Magic Link is missing from the matched Mailpit body");
      return { id: message.ID, link };
    }
    await new Promise((resolve) =>
      setTimeout(resolve, Math.min(pollIntervalMs, Math.max(1, deadline - Date.now()))),
    );
  }
  throw new Error("Magic Link did not arrive for this run's unique recipient before timeout");
}

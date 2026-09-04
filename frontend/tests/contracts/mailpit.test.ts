import { describe, expect, it, vi } from "vitest";

import { requireMailpitHealthy, waitForMagicLink } from "../e2e/support/mailpit";

const baseUrl = "http://127.0.0.1:54324";
const supabaseUrl = "http://127.0.0.1:54321";
const recipient = "unit-mailpit-fixture@example.com";
const message = { ID: "unit-message", To: [{ Address: recipient }] };
const link = `${supabaseUrl}/auth/v1/verify?token=unit-fixture-only&type=magiclink`;

function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function wait(fetchImpl: typeof fetch, excludedMessageIds?: ReadonlySet<string>) {
  return waitForMagicLink({
    baseUrl,
    supabaseUrl,
    recipient,
    excludedMessageIds,
    fetchImpl,
    timeoutMs: 20,
    pollIntervalMs: 1,
  });
}

describe("Mailpit helper failure contracts (not a replacement for real E2E)", () => {
  it("requires an actual HTTP 200 health response", async () => {
    const transport = vi.fn<typeof fetch>().mockResolvedValue(new Response("", { status: 503 }));
    await expect(requireMailpitHealthy(baseUrl, transport)).rejects.toThrow("health failed");
    expect(transport.mock.calls[0]?.[0]).toBe(`${baseUrl}/readyz`);
  });

  it("fails when health cannot be reached", async () => {
    const transport = vi.fn<typeof fetch>().mockRejectedValue(new Error("connection refused"));
    await expect(requireMailpitHealthy(baseUrl, transport)).rejects.toThrow("connection refused");
  });

  it("fails at the finite deadline when no email arrives", async () => {
    const transport = vi.fn<typeof fetch>().mockImplementation(async () => json({ messages: [] }));
    await expect(wait(transport)).rejects.toThrow("before timeout");
  });

  it("never consumes another recipient's message", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockImplementation(async () =>
        json({ messages: [{ ...message, To: [{ Address: "another-run@example.com" }] }] }),
      );
    await expect(wait(transport)).rejects.toThrow("unique recipient");
    expect(transport.mock.calls.every(([url]) => url === `${baseUrl}/api/v1/messages`)).toBe(true);
  });

  it("never reuses a message ID already consumed by the run", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockImplementation(async () => json({ messages: [message] }));
    await expect(wait(transport, new Set([message.ID]))).rejects.toThrow("before timeout");
  });

  it("fails closed on incompatible listing responses", async () => {
    const transport = vi.fn<typeof fetch>().mockResolvedValue(json({ mailbox: [] }));
    await expect(wait(transport)).rejects.toThrow("messages contract");
  });

  it("fails if the matched message body cannot be retrieved", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ messages: [message] }))
      .mockResolvedValueOnce(json({}, 404));
    await expect(wait(transport)).rejects.toThrow("body retrieval failed");
  });

  it("revalidates the body recipient", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ messages: [message] }))
      .mockResolvedValueOnce(
        json({ ...message, To: [{ Address: "foreign@example.com" }], HTML: link }),
      );
    await expect(wait(transport)).rejects.toThrow("recipient does not match");
  });

  it("fails if no real body is returned", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ messages: [message] }))
      .mockResolvedValueOnce(json(message));
    await expect(wait(transport)).rejects.toThrow("real message body");
  });

  it("fails if the real body does not contain the Supabase verification link", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ messages: [message] }))
      .mockResolvedValueOnce(json({ ...message, Text: "No verification link" }));
    await expect(wait(transport)).rejects.toThrow("Magic Link is missing");
  });

  it("returns only the link and ID obtained from the matching body", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(json({ messages: [message] }))
      .mockResolvedValueOnce(
        json({ ...message, HTML: `<a href="${link.replaceAll("&", "&amp;")}">Sign in</a>` }),
      );
    await expect(wait(transport)).resolves.toEqual({ id: message.ID, link });
    expect(transport.mock.calls[1]?.[0]).toBe(`${baseUrl}/api/v1/message/${message.ID}`);
  });
});

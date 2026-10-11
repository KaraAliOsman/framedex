import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { configureApiAuthContext } from "../../api/apiMutator";
import { clearActor, discardRejected, enqueue, flush, pending, readCopy, saveCopy } from "./outbox";
import type { Workspace } from "./types";

const scope = { actor: "field-actor", org: "field-org" };
const command = {
  operation_key: "receipt-key",
  kind: "INCIDENT" as const,
  note: "Perfil golpeado",
  photo_b64: "private-photo",
};

beforeEach(async () => {
  await clearActor(scope.actor);
  await clearActor("other-actor");
  configureApiAuthContext(async () => ({ accessToken: "memory-token", organizationId: scope.org }));
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify({ applied: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    ),
  );
  Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
});

describe("durable field commands", () => {
  it("never restores personal evidence when a lost reply arrives after logout", async () => {
    await enqueue(scope, "visit", command);
    vi.mocked(fetch).mockImplementationOnce(async () => {
      await clearActor(scope.actor);
      throw new TypeError("Late lost reply");
    });
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toThrow("Late lost reply");
    expect(await pending(scope)).toEqual([]);
    expect(await readCopy(scope)).toBeUndefined();
  });
  it("allows discarding a definitive rejection, never an uncertain lost response", async () => {
    await enqueue(scope, "visit", command);
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toThrow();
    await expect(discardRejected(scope, `${scope.actor}:${scope.org}:receipt-key`)).rejects.toThrow(
      "aún puede estar aplicado",
    );
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { detail: "Etiqueta de otra unidad" } }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toMatchObject({ status: 422 });
    await discardRejected(scope, `${scope.actor}:${scope.org}:receipt-key`);
    expect(await pending(scope)).toEqual([]);
  });
  it("isolates organization and actor and never persists office choices or access URLs", async () => {
    const workspace = {
      role: "INSTALLER",
      visits: [],
      incidents: [],
      projects: [{ id: "private-office" }],
      assignees: [{ user_id: "private-person" }],
    } as unknown as Workspace;
    await saveCopy(scope, workspace);
    expect((await readCopy(scope))?.workspace).toMatchObject({ projects: [], assignees: [] });
    expect(await readCopy({ ...scope, org: "other-org" })).toBeUndefined();
    await enqueue(scope, "visit", command);
    expect(await pending({ ...scope, actor: "other-actor" })).toEqual([]);
    expect(await pending({ ...scope, org: "other-org" })).toEqual([]);
  });
  it("reopens durable commands after lost reply and double flush sends once at a time", async () => {
    await enqueue(scope, "visit", command);
    vi.mocked(fetch).mockRejectedValueOnce(new Error("reply lost"));
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toThrow("reply lost");
    const saved = await pending(scope);
    expect(saved[0]?.command.operation_key).toBe("receipt-key");
    expect(saved[0]?.failure).toBe("reply lost");
    await Promise.all([
      flush(
        scope,
        () => true,
        async () => {},
      ),
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ]);
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(await pending(scope)).toEqual([]);
  });
  it("does not overwrite earlier evidence, cross tenant headers, or bypass live access", async () => {
    await enqueue(scope, "visit", command);
    await expect(
      enqueue(scope, "visit", { ...command, note: "Different bytes" }),
    ).rejects.toThrow();
    await flush(
      scope,
      () => false,
      async () => {},
    );
    expect(fetch).not.toHaveBeenCalled();
    configureApiAuthContext(async () => ({
      accessToken: "new-org-token",
      organizationId: "new-org",
    }));
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toMatchObject({ status: 409 });
    expect(fetch).not.toHaveBeenCalled();
    expect(await pending(scope)).toHaveLength(1);
  });
  it("keeps causal order after rejection and removes personal evidence on logout", async () => {
    await enqueue(scope, "visit", command);
    await enqueue(scope, "visit", { operation_key: "later-key", kind: "RECEIVE" });
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { detail: "Access revoked" } }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(
      flush(
        scope,
        () => true,
        async () => {},
      ),
    ).rejects.toMatchObject({ status: 403 });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(await pending(scope)).toHaveLength(2);
    await clearActor(scope.actor);
    expect(await pending(scope)).toEqual([]);
    expect(await readCopy(scope)).toBeUndefined();
  });
});

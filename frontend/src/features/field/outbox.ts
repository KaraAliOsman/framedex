/** Local copies and commands carry actor+tenant, never a capability or membership. */
import { fieldCommand } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { Command, Workspace } from "./types";

type Scope = { actor: string; org: string };
export type Pending = Scope & {
  key: string;
  visitId: string;
  command: Command;
  savedAt: number;
  failure?: string;
  failureStatus?: number;
};
type Copy = Scope & { key: string; workspace: Workspace; savedAt: number };
const DATABASE = "dekopen-field-v1";
const locked = new Map<string, Promise<void>>();
const actorGeneration = new Map<string, number>();

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore("copies", { keyPath: "key" });
      request.result.createObjectStore("commands", { keyPath: "key" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(new Error("No se puede abrir la memoria de terreno. Habilita almacenamiento local."));
  });
}
async function run<T>(
  store: "copies" | "commands",
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, mode);
    const request = fn(tx.objectStore(store));
    let result: T;
    request.onsuccess = () => {
      result = request.result;
    };
    // Request success is not a committed durable save.
    tx.oncomplete = () => {
      db.close();
      resolve(result);
    };
    tx.onabort = tx.onerror = () => {
      db.close();
      reject(
        new Error(
          "No se pudo guardar en este teléfono. Libera espacio y reintenta; la acción no está guardada.",
        ),
      );
    };
  });
}
function scopeKey(scope: Scope): string {
  return `${scope.actor}:${scope.org}`;
}
export async function saveCopy(scope: Scope, workspace: Workspace): Promise<void> {
  const generation = actorGeneration.get(scope.actor);
  // Only physical agenda/evidence. Office choice lists are fetched live.
  await run("copies", "readwrite", (store) =>
    generation !== actorGeneration.get(scope.actor)
      ? store.get(scopeKey(scope))
      : store.put({
          ...scope,
          key: scopeKey(scope),
          workspace: { ...workspace, projects: [], assignees: [] },
          savedAt: Date.now(),
        }),
  );
}
export async function readCopy(scope: Scope): Promise<Copy | undefined> {
  return run("copies", "readonly", (store) => store.get(scopeKey(scope)));
}
export async function pending(scope: Scope): Promise<Pending[]> {
  const values = await run<Pending[]>("commands", "readonly", (store) => store.getAll());
  return values
    .filter((p) => p.actor === scope.actor && p.org === scope.org)
    .sort((a, b) => a.savedAt - b.savedAt || a.key.localeCompare(b.key));
}
export async function enqueue(scope: Scope, visitId: string, command: Command): Promise<Pending> {
  const generation = actorGeneration.get(scope.actor);
  const value = {
    ...scope,
    key: `${scopeKey(scope)}:${command.operation_key}`,
    visitId,
    command,
    savedAt: Date.now(),
  };
  // add, never put: an operation key cannot overwrite earlier evidence.
  await run("commands", "readwrite", (store) =>
    generation !== actorGeneration.get(scope.actor) ? store.get(value.key) : store.add(value),
  );
  if (generation !== actorGeneration.get(scope.actor))
    throw new Error("La sesión cambió. Abre tu agenda antes de registrar otro trabajo.");
  return value;
}
export function detail(error: unknown): string {
  if (error instanceof ApiError) {
    const payload = error.payload as { error?: { detail?: string } };
    return (
      payload?.error?.detail ??
      "No se autorizó el registro. Revisa el acceso y los datos del pendiente."
    );
  }
  if (error instanceof TypeError)
    return "No llegó una respuesta del servidor. Conservamos el pendiente; reintenta con la misma operación al recuperar señal.";
  return error instanceof Error
    ? error.message
    : "No se pudo sincronizar. Conservamos el registro pendiente.";
}
export async function clearActor(actor: string): Promise<void> {
  actorGeneration.set(actor, (actorGeneration.get(actor) ?? 0) + 1);
  const db = await open();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(["copies", "commands"], "readwrite");
    for (const name of ["copies", "commands"]) {
      const request = tx.objectStore(name).openCursor();
      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor) return;
        if (cursor.value.actor === actor) cursor.delete();
        cursor.continue();
      };
    }
    tx.oncomplete = () => resolve();
    tx.onabort = () =>
      reject(new Error("No se pudo borrar la copia privada de terreno. Reintenta cerrar sesión."));
  });
  db.close();
}
export async function discardRejected(scope: Scope, key: string): Promise<void> {
  const item = (await pending(scope)).find((p) => p.key === key);
  if (!item?.failureStatus || ![400, 403, 404, 409, 422].includes(item.failureStatus))
    throw new Error("Este registro aún puede estar aplicado. Reintenta con su misma operación.");
  await run("commands", "readwrite", (store) => store.delete(item.key));
}
async function markFailed(item: Pending, error: unknown): Promise<void> {
  const db = await open();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction("commands", "readwrite");
    const store = tx.objectStore("commands");
    const request = store.get(item.key);
    // Logout may already have removed it. Never recreate personal evidence
    // from a response arriving after that deletion.
    request.onsuccess = () => {
      if (request.result)
        store.put({
          ...request.result,
          failure: detail(error),
          failureStatus: error instanceof ApiError ? error.status : undefined,
        });
    };
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(new Error("No se pudo guardar el estado del pendiente."));
  });
  db.close();
}
export async function flush(
  scope: Scope,
  isLive: () => boolean,
  onReceipt: () => Promise<void>,
): Promise<void> {
  const lock = scopeKey(scope);
  if (locked.has(lock)) return locked.get(lock);
  const operation = (async () => {
    for (const item of await pending(scope)) {
      if (!navigator.onLine || !isLive()) return;
      try {
        await fieldCommand(item.visitId, item.command, {
          headers: { "X-Organization-ID": scope.org },
        });
        // Even after a tenant swap a receipt belongs only to its old scope.
        await run("commands", "readwrite", (store) => store.delete(item.key));
        if (isLive()) await onReceipt();
      } catch (error) {
        await markFailed(item, error);
        throw error; // Keep ordered causality: a reception cannot pass failed checks.
      }
    }
  })();
  locked.set(lock, operation);
  try {
    await operation;
  } finally {
    locked.delete(lock);
  }
}

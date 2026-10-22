/** Copilot preferences per person and organization (dirección final 05).
 *
 * Only non-sensitive presentation state is kept: the preferred mode and
 * policy (device storage) and, for this browser session, whether the popup
 * was open and which conversation it showed (ids only). Messages, prices,
 * documents and attachments never touch browser storage. A new sign-in
 * starts closed: session keys are scoped `user:org` and cleared when the
 * identity changes.
 */

export type InteractionMode = "chat" | "work";
export type AutonomyPolicy = "propose" | "approve" | "draft";

export const AUTONOMY_OPTIONS: { value: AutonomyPolicy; label: string; hint: string }[] = [
  { value: "propose", label: "Solo proponer", hint: "Prepara la propuesta; nada se aplica." },
  {
    value: "approve",
    label: "Con aprobación",
    hint: "Prepara el conjunto completo y lo aplicas con una aprobación.",
  },
  {
    value: "draft",
    label: "Omitir todo",
    hint: "Aplica lo reversible de la tarea, verifica y muestra el resumen.",
  },
];

export const DEFAULT_MODE: InteractionMode = "chat";
export const DEFAULT_AUTONOMY: AutonomyPolicy = "approve";

const memory = new Map<string, string>();

function scoped(name: string, userId: string | null, orgId: string | null): string | null {
  if (!userId || !orgId) return null;
  return `dekopen.copilot.v1.${name}.${userId}.${orgId}`;
}

function read(storage: "local" | "session", storageKey: string): string | null {
  try {
    // Working storage is the authority (a cleared key stays cleared);
    // memory only stands in when the storage itself is blocked.
    return (storage === "local" ? window.localStorage : window.sessionStorage).getItem(storageKey);
  } catch {
    return memory.get(`${storage}:${storageKey}`) ?? null;
  }
}

function write(storage: "local" | "session", storageKey: string, value: string | null): void {
  if (value === null) memory.delete(`${storage}:${storageKey}`);
  else memory.set(`${storage}:${storageKey}`, value);
  try {
    const target = storage === "local" ? window.localStorage : window.sessionStorage;
    if (value === null) target.removeItem(storageKey);
    else target.setItem(storageKey, value);
  } catch {
    /* memory keeps it for this session */
  }
}

export function readMode(userId: string | null, orgId: string | null): InteractionMode {
  const storageKey = scoped("mode", userId, orgId);
  const value = storageKey ? read("local", storageKey) : null;
  return value === "work" || value === "chat" ? value : DEFAULT_MODE;
}

export function saveMode(userId: string | null, orgId: string | null, mode: InteractionMode): void {
  const storageKey = scoped("mode", userId, orgId);
  if (storageKey) write("local", storageKey, mode);
}

export function readAutonomy(userId: string | null, orgId: string | null): AutonomyPolicy {
  const storageKey = scoped("autonomy", userId, orgId);
  const value = storageKey ? read("local", storageKey) : null;
  return value === "propose" || value === "approve" || value === "draft" ? value : DEFAULT_AUTONOMY;
}

export function saveAutonomy(
  userId: string | null,
  orgId: string | null,
  autonomy: AutonomyPolicy,
): void {
  const storageKey = scoped("autonomy", userId, orgId);
  if (storageKey) write("local", storageKey, autonomy);
}

export type CopilotSession = { open: boolean; minimized: boolean; threadId: string | null };

export function readSession(userId: string | null, orgId: string | null): CopilotSession {
  const storageKey = scoped("session", userId, orgId);
  try {
    const parsed = JSON.parse(
      (storageKey && read("session", storageKey)) || "null",
    ) as Partial<CopilotSession> | null;
    if (parsed && typeof parsed === "object")
      return {
        open: parsed.open === true,
        minimized: parsed.minimized === true,
        threadId: typeof parsed.threadId === "string" ? parsed.threadId : null,
      };
  } catch {
    /* unreadable session state starts closed */
  }
  return { open: false, minimized: false, threadId: null };
}

export function saveSession(
  userId: string | null,
  orgId: string | null,
  session: CopilotSession,
): void {
  const storageKey = scoped("session", userId, orgId);
  if (storageKey) write("session", storageKey, JSON.stringify(session));
}

/** Identity changed (sign-out, another person or organization): drop the
 * session keys of every previous identity on this tab. */
export function clearOtherSessions(userId: string | null, orgId: string | null): void {
  const keep = scoped("session", userId, orgId);
  try {
    for (let index = window.sessionStorage.length - 1; index >= 0; index -= 1) {
      const storageKey = window.sessionStorage.key(index);
      if (storageKey?.startsWith("dekopen.copilot.v1.session.") && storageKey !== keep)
        window.sessionStorage.removeItem(storageKey);
    }
  } catch {
    /* nothing to clear in blocked storage */
  }
  for (const storageKey of [...memory.keys()]) {
    if (
      storageKey.startsWith("session:dekopen.copilot.v1.session.") &&
      storageKey !== `session:${keep}`
    )
      memory.delete(storageKey);
  }
}

/** Presentation preferences per person and organization (v1 final 01).
 *
 * Boundaries this module owns — and the ones it must never cross:
 * - Work view (Mesa de obra / Estudio) and copilot popup geometry are UI
 *   preferences. They never alter a work, a quotation, a fingerprint or a price.
 * - Nothing private is stored: no messages, prices, documents, server payloads.
 * - Keys are versioned and scoped `user:org`; another person or organization
 *   on the same device never inherits them. Blocked storage degrades to memory.
 */

export type WorkView = "mesa" | "estudio";
export const WORK_VIEWS: readonly WorkView[] = ["mesa", "estudio"];
export const DEFAULT_WORK_VIEW: WorkView = "mesa";

export type PopupGeometry = { x: number; y: number; width: number; height: number };

const VERSION = 1;
const memory = new Map<string, string>();

function key(name: string, userId: string | null, orgId: string | null): string | null {
  if (!userId || !orgId) return null;
  return `dekopen.pref.v${VERSION}.${name}.${userId}.${orgId}`;
}

function readRaw(storageKey: string): string | null {
  try {
    const value = window.localStorage.getItem(storageKey);
    if (value !== null) return value;
  } catch {
    /* blocked storage: fall back to this tab's memory */
  }
  return memory.get(storageKey) ?? null;
}

function writeRaw(storageKey: string, value: string): void {
  memory.set(storageKey, value);
  try {
    window.localStorage.setItem(storageKey, value);
  } catch {
    /* the preference still works in memory for this session */
  }
}

export function isWorkView(value: unknown): value is WorkView {
  return value === "mesa" || value === "estudio";
}

export function readWorkView(userId: string | null, orgId: string | null): WorkView {
  const storageKey = key("work-view", userId, orgId);
  if (!storageKey) return DEFAULT_WORK_VIEW;
  const value = readRaw(storageKey);
  return isWorkView(value) ? value : DEFAULT_WORK_VIEW;
}

export function saveWorkView(userId: string | null, orgId: string | null, view: WorkView): void {
  const storageKey = key("work-view", userId, orgId);
  if (storageKey) writeRaw(storageKey, view);
}

export function readPopupGeometry(
  userId: string | null,
  orgId: string | null,
): PopupGeometry | null {
  const storageKey = key("copilot-geometry", userId, orgId);
  if (!storageKey) return null;
  try {
    const parsed = JSON.parse(readRaw(storageKey) ?? "null") as unknown;
    if (
      parsed &&
      typeof parsed === "object" &&
      ["x", "y", "width", "height"].every(
        (field) => typeof (parsed as Record<string, unknown>)[field] === "number",
      )
    )
      return parsed as PopupGeometry;
  } catch {
    /* an unreadable preference is ignored */
  }
  return null;
}

export function savePopupGeometry(
  userId: string | null,
  orgId: string | null,
  geometry: PopupGeometry,
): void {
  const storageKey = key("copilot-geometry", userId, orgId);
  if (storageKey) writeRaw(storageKey, JSON.stringify(geometry));
}

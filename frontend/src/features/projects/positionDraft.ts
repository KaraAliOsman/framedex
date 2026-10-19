import type { CanvasDesignInputs } from "../canvas/canvasStore";

/** Unsaved-position draft buffer (v2, dirección final 02).
 *
 * A reload used to silently discard the in-flight design: the draft survives
 * in sessionStorage (same-tab lifetime of an accidental refresh) and is
 * offered back as an explicit choice — never applied automatically and never
 * taken as a current calculated result.
 *
 * Identity: format version + person + organization + work + position, or a
 * stable creation id for new windows/copies. Two new windows of different
 * works, or two copies of the same source, never share a draft. The legacy
 * `org:position|copy|new` key is read only when it names an existing position
 * (demonstrable identity); a legacy `new` is never grafted onto another work.
 */

const PREFIX = "dekopen:position-draft:";
const VERSION = 2;

export interface PositionDraft {
  inputs: CanvasDesignInputs;
  location: string;
  quantity: string;
  savedAt: number;
  /** Design identity of the saved baseline the draft started from. */
  baseline?: string | null;
  /** Work revision when the draft was taken. */
  revision?: string | null;
  version?: number;
}

export type DraftIdentity = {
  userId: string;
  orgId: string;
  projectId: string;
  positionId: string | null;
  /** Stable id of a creation (new or copy) — see `creationId`. */
  creationId: string | null;
};

export function positionDraftKey(identity: DraftIdentity): string {
  const target = identity.positionId
    ? `position:${identity.positionId}`
    : `create:${identity.creationId ?? "pending"}`;
  return `${PREFIX}v${VERSION}:${identity.userId}:${identity.orgId}:${identity.projectId}:${target}`;
}

function legacyKey(identity: DraftIdentity): string | null {
  return identity.positionId ? `${PREFIX}${identity.orgId}:${identity.positionId}` : null;
}

function parse(raw: string | null): PositionDraft | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as PositionDraft;
    if (typeof parsed.savedAt !== "number" || typeof parsed.inputs !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

export function readPositionDraft(identity: DraftIdentity): PositionDraft | null {
  try {
    const current = parse(sessionStorage.getItem(positionDraftKey(identity)));
    if (current) return current;
    const legacy = legacyKey(identity);
    return legacy ? parse(sessionStorage.getItem(legacy)) : null;
  } catch {
    return null;
  }
}

export function writePositionDraft(identity: DraftIdentity, draft: PositionDraft): void {
  try {
    sessionStorage.setItem(
      positionDraftKey(identity),
      JSON.stringify({ ...draft, version: VERSION }),
    );
  } catch {
    // Quota/denied storage — the draft is best-effort, never a blocker.
  }
}

export function clearPositionDraft(identity: DraftIdentity): void {
  try {
    sessionStorage.removeItem(positionDraftKey(identity));
    const legacy = legacyKey(identity);
    if (legacy) sessionStorage.removeItem(legacy);
  } catch {
    /* best-effort */
  }
}

/** A creation id that stays stable for one creation in this tab. */
export function newCreationId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

/** Revision codes are storage identifiers ("REV-A"); the UI reads them as
 * document language («Revisión A»). Anything outside the pattern renders
 * unchanged — never invent a friendlier name for an unknown code. */
export function formatRevision(code: string | null | undefined): string {
  if (!code) return "—";
  const match = /^REV-([A-Z]+)$/.exec(code);
  return match ? `Revisión ${match[1]}` : code;
}

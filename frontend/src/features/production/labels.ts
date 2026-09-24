import { t } from "../../i18n/es-CL";

export function cutRoleLabel(role: string | null | undefined): string {
  if (role === null || role === undefined || role === "") return "—";
  const known: ReadonlySet<string> = new Set([
    "FRAME",
    "SASH",
    "MULLION_V",
    "MULLION_H",
    "INVERSOR",
    "GLAZING_BEAD",
    "COUPLER",
    "ADDITIONAL",
    "THRESHOLD",
    "CHANNEL",
    "REINFORCEMENT",
  ]);
  return known.has(role) ? t(`production.role.${role}` as Parameters<typeof t>[0]) : role;
}

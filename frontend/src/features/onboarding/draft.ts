export type ClientFields = { rut: string; email: string; phone: string };
export type Draft = {
  schema?: number;
  step?: number;
  systemId?: string | null;
  clientId?: string | null;
  clientName?: string;
  clientExtra?: ClientFields;
  projectId?: string | null;
  projectName?: string;
};
export const storageKey = (orgId: string): string => `onboarding:${orgId}`;

export function completeFirstPosition(orgId: string, projectId: string): void {
  if (readDraft(orgId).projectId === projectId) sessionStorage.removeItem(storageKey(orgId));
}

export function readDraft(orgId: string): Draft {
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem(storageKey(orgId)) ?? "{}");
    if (!saved || typeof saved !== "object" || Array.isArray(saved)) return {};
    const value = saved as Record<string, unknown>;
    const rawStep = typeof value.step === "number" && Number.isInteger(value.step) ? value.step : 0;
    const step = value.schema === 2 ? rawStep : ([0, 0, 0, 1, 2, 3, 3][rawStep] ?? 0);
    const id = (key: string): string | null =>
      typeof value[key] === "string" &&
      /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value[key])
        ? value[key]
        : null;
    const text = (key: string): string =>
      typeof value[key] === "string" ? value[key].slice(0, 255) : "";
    const extra =
      value.clientExtra && typeof value.clientExtra === "object"
        ? (value.clientExtra as Record<string, unknown>)
        : {};
    const field = (key: string): string =>
      typeof extra[key] === "string" ? extra[key].slice(0, 255) : "";
    return {
      schema: 2,
      step: Math.min(3, Math.max(0, step)),
      systemId: id("systemId"),
      clientId: id("clientId"),
      projectId: id("projectId"),
      clientName: text("clientName"),
      projectName: text("projectName"),
      clientExtra: { rut: field("rut"), email: field("email"), phone: field("phone") },
    };
  } catch {
    return {};
  }
}

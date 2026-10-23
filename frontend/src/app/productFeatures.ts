/** UI composition only. Turning a flag off never changes stored engineering data. */
export function obraVistaUnica(): boolean {
  const configured = import.meta.env.VITE_OBRA_VISTA_UNICA as string | undefined;
  return !["0", "false", "off"].includes(configured?.trim().toLowerCase() ?? "");
}

/** P08: the assistant docks as a right-side panel; `false` restores the
 * floating popup with its own position and size. */
export function agentePanelLateral(): boolean {
  const configured = import.meta.env.VITE_AGENTE_PANEL_LATERAL as string | undefined;
  return !["0", "false", "off"].includes(configured?.trim().toLowerCase() ?? "");
}

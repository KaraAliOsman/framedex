/** UI composition only. Turning a flag off never changes stored engineering data. */
export function obraVistaUnica(): boolean {
  const configured = import.meta.env.VITE_OBRA_VISTA_UNICA as string | undefined;
  return !["0", "false", "off"].includes(configured?.trim().toLowerCase() ?? "");
}

import type { FinishAuthority, FinishColor, ResolvedFinish } from "../../api/generated/models";

export type FinishFace = "interior" | "exterior";

/** Presentation conversion only. Manufacturer channels remain linear in the API. */
export function finishColorCss(color: FinishColor): string {
  const rgb = color.linear_rgb.map((channel) => {
    const value = Number(channel);
    const encoded = value <= 0.0031308 ? value * 12.92 : 1.055 * value ** (1 / 2.4) - 0.055;
    return Math.round(encoded * 255);
  });
  return `color(srgb ${rgb.map((channel) => channel / 255).join(" ")})`;
}

export function chartFinish(
  authority: FinishAuthority | null | undefined,
  code: string,
): ResolvedFinish | null {
  const combination = authority?.combinations.find((item) => item.code === code);
  if (!authority || !combination) return null;
  const interior = authority.colors.find((item) => item.code === combination.interior);
  const exterior = authority.colors.find((item) => item.code === combination.exterior);
  if (!interior || !exterior) return null;
  return {
    combination,
    interior,
    exterior,
    base: authority.colors.find((item) => item.code === combination.base) ?? null,
    profile_skus: {},
    handle_colors: authority.handle_colors ?? [],
  };
}

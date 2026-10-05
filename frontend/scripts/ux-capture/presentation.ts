/** Serializable observations from the rendered DOM; no source-text guesses. */
export type Observation = {
  sample: string;
  fontSize: number;
  radius: number;
  shadow: string;
  allowedShadows: string[];
  backgroundImage: string;
  filter: string;
  backdropFilter: string;
  textColor: string;
  backgroundColor: string;
  hasText: boolean;
  largeText: boolean;
  interactive: boolean;
  disabled: boolean;
  hasEffect: boolean;
  width: number;
  height: number;
  statusDot: boolean;
  primary: boolean;
  region: string;
};
export type PresentationFinding = { kind: string; sample: string };

export function contrastRatio(foreground: string, background: string): number {
  function luminance(color: string): number {
    const channels = color.startsWith("#")
      ? (color.slice(1).match(/.{2}/g) ?? []).map((channel) => parseInt(channel, 16))
      : (color.match(/[\d.]+/g) ?? []).slice(0, 3).map(Number);
    if (channels.length !== 3) return NaN;
    const linear = channels.map((value) => {
      const normalized = value / 255;
      return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
    });
    return linear[0]! * 0.2126 + linear[1]! * 0.7152 + linear[2]! * 0.0722;
  }
  const a = luminance(foreground),
    b = luminance(background);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

export function detectPresentationFindings(
  observations: readonly Observation[],
  workshop: boolean,
): PresentationFinding[] {
  const findings: PresentationFinding[] = [];
  const primaryRegions = new Map<string, number>();
  for (const row of observations) {
    const add = (kind: string) => findings.push({ kind, sample: row.sample });
    if (row.hasText && row.fontSize < 11) add("font-under-11");
    if (row.radius > 4 && !row.statusDot) add("radius-over-4");
    if (row.shadow !== "none" && !row.allowedShadows.includes(row.shadow))
      add("shadow-outside-scale");
    if (/gradient\(/.test(row.backgroundImage)) add("gradient");
    if (/blur\(/.test(`${row.filter} ${row.backdropFilter}`)) add("blur");
    if (
      row.hasText &&
      !row.disabled &&
      contrastRatio(row.textColor, row.backgroundColor) < (row.largeText ? 3 : 4.5)
    )
      add("contrast-under-aa");
    if (workshop && row.interactive && (row.width < 44 || row.height < 44))
      add("touch-target-under-44");
    if (row.interactive && !row.disabled && !row.hasEffect) add("interactive-without-effect");
    if (row.primary && !row.disabled)
      primaryRegions.set(row.region, (primaryRegions.get(row.region) ?? 0) + 1);
  }
  for (const [region, count] of primaryRegions) {
    if (count > 1) findings.push({ kind: "multiple-primary", sample: `${region}: ${count}` });
  }
  return findings;
}

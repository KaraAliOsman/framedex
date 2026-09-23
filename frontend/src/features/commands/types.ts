import type { TranslationKey } from "../../i18n/es-CL";

/** A parameter the palette collects before running a command. Number params
 * accept the engine's decimal-string contract; choice params render as the
 * palette's own filtered list. */
export type CommandParam =
  | {
      kind: "number";
      id: string;
      label: string;
      unit?: string;
      defaultValue?: string;
      /** Normalize or reject the typed value (returns the committed string or
       * null to keep the parameter step open with an invalid hint). */
      validate?(raw: string): string | null;
    }
  | {
      kind: "choice";
      id: string;
      label: string;
      options: { value: string; label: string }[];
    };

export interface CommandDefinition {
  id: string;
  /** es-CL title shown in the palette list. */
  title: string;
  /** Extra searchable terms (synonyms, English, object kinds). */
  keywords?: string[];
  /** Parameters collected sequentially before `run`. */
  params?: CommandParam[];
  /** A short preview of what the command will change (the AI seam's
   * `describeDiff`). Rendered under the list while the command is selected. */
  describe?(args: Record<string, string>): string;
  run(args: Record<string, string>): void;
}

export interface CommandSurface {
  /** Commands valid right now — surfaces build this fresh whenever their
   * underlying state (selection, product) changes, so the palette only ever
   * shows executable entries. */
  commands: CommandDefinition[];
}

export type { TranslationKey };

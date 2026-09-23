import type { TranslationKey } from "../../i18n/es-CL";
import type { Opening } from "./intentEditing";

export const OPENING_OPTIONS: readonly [Opening, TranslationKey][] = [
  ["FIXED", "intent.fixed"],
  ["TURN_LEFT", "intent.turnLeft"],
  ["TURN_RIGHT", "intent.turnRight"],
  ["TILT_TURN_LEFT", "intent.tiltLeft"],
  ["TILT_TURN_RIGHT", "intent.tiltRight"],
  ["AWNING", "intent.awning"],
  ["SLIDING_2L", "intent.sliding"],
  ["DOOR_ENTRY", "intent.door"],
];

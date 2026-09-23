/** Opening types offered by the editors and the command palette. */
export const OPENING_OPTIONS = [
  ["FIXED", "intent.fixed"],
  ["TURN_LEFT", "intent.turnLeft"],
  ["TURN_RIGHT", "intent.turnRight"],
  ["TILT_TURN_LEFT", "intent.tiltLeft"],
  ["TILT_TURN_RIGHT", "intent.tiltRight"],
  ["AWNING", "intent.awning"],
  ["SLIDING_2L", "intent.sliding"],
  ["DOOR_ENTRY", "intent.door"],
] as const;

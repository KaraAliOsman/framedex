import { afterEach, expect, it, vi } from "vitest";
import { obraVistaUnica } from "./productFeatures";

afterEach(() => vi.unstubAllEnvs());

it("enables the unified work by default and keeps explicit rollback values", () => {
  vi.stubEnv("VITE_OBRA_VISTA_UNICA", undefined);
  expect(obraVistaUnica()).toBe(true);
  for (const value of ["1", "true", "on"]) {
    vi.stubEnv("VITE_OBRA_VISTA_UNICA", value);
    expect(obraVistaUnica()).toBe(true);
  }
  for (const value of ["0", "false", "off", " FALSE "]) {
    vi.stubEnv("VITE_OBRA_VISTA_UNICA", value);
    expect(obraVistaUnica()).toBe(false);
  }
});

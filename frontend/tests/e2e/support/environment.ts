/** Read only the test runner's environment; no browser/VITE secret exposure. */
export function environment(name: string): string | undefined {
  const runtime: unknown = Reflect.get(globalThis, "process");
  if (typeof runtime !== "object" || runtime === null || !("env" in runtime)) {
    throw new Error("The real E2E must run in the configured local test runner");
  }
  const variables: unknown = runtime.env;
  if (typeof variables !== "object" || variables === null) {
    throw new Error("The test runner did not provide an environment");
  }
  const value: unknown = Reflect.get(variables, name);
  return typeof value === "string" ? value : undefined;
}

import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App bootstrap contract", () => {
  it("returns the application root element", () => {
    const element = App();

    expect(element.type).toBe("main");
    expect(element.props["className"]).toBe("contents");
    expect(element.props["data-app-root"]).toBe("dekopen");
  });
});

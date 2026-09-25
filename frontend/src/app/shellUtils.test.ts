import { describe, expect, it } from "vitest";

import {
  contextItemActive,
  hasUnsavedWork,
  registerDirtySource,
  type ContextNavItem,
} from "./shellUtils";

const items: ContextNavItem[] = [
  { to: "/production", label: "nav.context.queue" },
  { to: "/production?shortage=1", label: "nav.context.shortage" },
  { to: "/production?dispatch_ready=1", label: "nav.context.dispatch" },
];

describe("contextItemActive", () => {
  it("activates a query item when its params are a subset of composed live filters", () => {
    expect(contextItemActive(items[1]!, items, "/production", "?shortage=1&status=HOLD")).toBe(
      true,
    );
    expect(contextItemActive(items[0]!, items, "/production", "?shortage=1&status=HOLD")).toBe(
      false,
    );
  });

  it("lights only the first matching query item when two filters claim the URL", () => {
    const search = "?shortage=1&dispatch_ready=1";
    expect(contextItemActive(items[1]!, items, "/production", search)).toBe(true);
    expect(contextItemActive(items[2]!, items, "/production", search)).toBe(false);
    expect(contextItemActive(items[0]!, items, "/production", search)).toBe(false);
  });

  it("keeps the plain item active only when no query sibling matches", () => {
    expect(contextItemActive(items[0]!, items, "/production", "?status=HOLD")).toBe(true);
    expect(contextItemActive(items[0]!, items, "/production", "?shortage=1")).toBe(false);
    expect(contextItemActive(items[1]!, items, "/production", "")).toBe(false);
  });
});

describe("dirty registry", () => {
  it("tracks unsaved work while a source is registered", () => {
    expect(hasUnsavedWork()).toBe(false);
    const release = registerDirtySource("editor-1");
    expect(hasUnsavedWork()).toBe(true);
    release();
    expect(hasUnsavedWork()).toBe(false);
  });
});

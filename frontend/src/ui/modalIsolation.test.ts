import { afterEach, expect, it } from "vitest";
import { isolateDialog, isTopDialog } from "./modalIsolation";
afterEach(() => {
  document.body.replaceChildren();
});
it("isolates the background and underlying dialog, restores previous attributes and handles late portals", async () => {
  const page = document.createElement("main"),
    first = document.createElement("div"),
    second = document.createElement("div");
  page.setAttribute("aria-hidden", "false");
  document.body.append(page, first);
  const closeFirst = isolateDialog(first);
  expect(page.inert).toBe(true);
  expect(page.getAttribute("aria-hidden")).toBe("true");
  document.body.append(second);
  await Promise.resolve();
  expect(second.inert).toBe(true);
  const closeSecond = isolateDialog(second);
  expect(first.inert).toBe(true);
  expect(isTopDialog(second)).toBe(true);
  closeSecond();
  expect(isTopDialog(first)).toBe(true);
  expect(first.getAttribute("aria-hidden")).toBeNull();
  closeFirst();
  expect(page.getAttribute("aria-hidden")).toBe("false");
  expect(page.inert).not.toBe(true);
});

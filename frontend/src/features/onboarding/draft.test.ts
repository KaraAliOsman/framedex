import { afterEach, expect, test } from "vitest";
import { completeFirstPosition, readDraft, storageKey } from "./draft";

afterEach(() => sessionStorage.clear());

test("saving the first position clears only the matching organization's onboarding", () => {
  const projectId = "00112233-4455-6677-8899-aabbccddeeff";
  sessionStorage.setItem(storageKey("a"), JSON.stringify({ schema: 2, projectId }));
  sessionStorage.setItem(storageKey("b"), JSON.stringify({ schema: 2, projectId }));
  completeFirstPosition("a", "another-project");
  expect(sessionStorage.getItem(storageKey("a"))).not.toBeNull();
  completeFirstPosition("a", projectId);
  expect(sessionStorage.getItem(storageKey("a"))).toBeNull();
  expect(sessionStorage.getItem(storageKey("b"))).not.toBeNull();
});

test("migrates the seven-step progress without losing saved client and project", () => {
  const project = "00112233-4455-6677-8899-aabbccddeeff";
  for (const [old, expected] of [0, 0, 0, 1, 2, 3, 3].entries()) {
    sessionStorage.setItem(
      storageKey("a"),
      JSON.stringify({ step: old, projectId: project, clientName: "Sur" }),
    );
    expect(readDraft("a")).toMatchObject({
      schema: 2,
      step: expected,
      projectId: project,
      clientName: "Sur",
    });
  }
});

test("a corrupt storage value cannot become a route, a crash or another organization's progress", () => {
  for (const value of [
    "null",
    "[]",
    "7",
    "{",
    '{"schema":2,"step":"2","projectId":"../otro","clientExtra":{"email":7}}',
  ]) {
    sessionStorage.setItem(storageKey("a"), value);
    const draft = readDraft("a");
    expect(draft.step ?? 0).toBe(0);
    expect(draft.projectId ?? null).toBeNull();
    expect(draft.clientExtra?.email ?? "").toBe("");
  }
  sessionStorage.setItem(
    storageKey("a"),
    JSON.stringify({ schema: 2, step: 3, clientName: "Sur" }),
  );
  expect(readDraft("b")).toMatchObject({ step: 0, clientName: "" });
});

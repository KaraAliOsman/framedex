import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { AiJob } from "../../api/generated/models";
import { presenceKey, presenceState, publishAssistantJob } from "./useAssistantPresence";
import { Orb, orbStateFor } from "./Orb";
import { BotFigure } from "./BotFigure";

describe("contextual assistant presence", () => {
  it.each([
    ["QUEUED", "queued"],
    ["PLANNING", "thinking"],
    ["RUNNING", "working"],
    ["WAITING_FOR_USER", "waiting"],
    ["WAITING_FOR_APPROVAL", "approval"],
    ["SUCCEEDED", "success"],
    ["FAILED", "error"],
    ["FAILED_RETRYABLE", "error"],
    ["CANCELED", "canceled"],
    ["FUTURE_STATE", "idle"],
  ])("maps %s to %s", (state, expected) => {
    expect(orbStateFor(state)).toBe(expected);
  });
  it("uses committed worker progress during the provider transaction", () => {
    expect(
      presenceState({
        state: "PLANNING",
        live: { state: "RUNNING", phase: "context" },
      } as unknown as AiJob),
    ).toBe("thinking");
    expect(
      presenceState({
        state: "PLANNING",
        live: { state: "RUNNING", phase: "consulting" },
      } as unknown as AiJob),
    ).toBe("working");
    expect(
      presenceState({
        state: "WAITING_FOR_APPROVAL",
        live: { state: "SUCCEEDED" },
      } as unknown as AiJob),
    ).toBe("approval");
  });
  it("separates organization, user and object, ignoring only volatile selection", () => {
    const context = {
      organizationId: "org-a",
      userId: "user-a",
      surface: "position",
      refs: { project_id: "p", position_id: "pos" },
    };
    expect(presenceKey(context)).toEqual(
      presenceKey({ ...context, refs: { position_id: "pos", selection: "m1", project_id: "p" } }),
    );
    for (const next of [
      { organizationId: "org-b" },
      { userId: "user-b" },
      { refs: { project_id: "p", position_id: "other" } },
      { surface: "project" },
    ])
      expect(presenceKey({ ...context, ...next })).not.toEqual(presenceKey(context));
    const client = new QueryClient();
    publishAssistantJob(client, context, {
      id: "run",
      state: "WAITING_FOR_APPROVAL",
    } as unknown as AiJob);
    expect(client.getQueryData(presenceKey({ ...context, userId: "user-b" }))).toBeUndefined();
    expect(client.getQueryData(presenceKey(context))).toMatchObject({ job: { id: "run" } });
  });
  it("renders three orbs without duplicate SVG ids or unsafe external references", () => {
    const { container } = render(
      <>
        <Orb title="En cola" state="queued" size={16} />
        <Orb title="Trabajando" state="working" size={28} />
        <BotFigure state="approval" size={160} welcome />
      </>,
    );
    const ids = [...container.querySelectorAll("[id]")].map((node) => node.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(container.querySelectorAll("svg")).toHaveLength(3);
    expect(container.querySelector("filter, linearGradient, radialGradient")).toBeNull();
  });
});

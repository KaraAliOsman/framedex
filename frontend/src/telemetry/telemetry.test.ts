import { describe, expect, it, vi } from "vitest";

import {
  APPROVED_EVENTS,
  POSTHOG_PRIVACY_CONFIG,
  sanitizePostHogEvent,
  Telemetry,
  type TelemetryTransport,
} from "./telemetry";

function transport(): TelemetryTransport {
  return {
    capture: vi.fn(),
    identify: vi.fn(),
    group: vi.fn(),
    reset: vi.fn(),
  };
}

describe("PostHog privacy facade", () => {
  it("freezes the exact SHOT-04 event taxonomy", () => {
    expect(APPROVED_EVENTS).toEqual([
      "auth_magic_link_requested",
      "auth_signed_in",
      "organization_selected",
      "mfa_enrollment_started",
      "mfa_verified",
      "shell_route_viewed",
      "theme_changed",
    ]);
  });

  it("captures approved properties and rejects everything else", () => {
    const fake = transport();
    const telemetry = new Telemetry(fake);
    telemetry.capture("shell_route_viewed", { route_name: "/dashboard" });
    expect(fake.capture).toHaveBeenCalledWith("shell_route_viewed", {
      route_name: "/dashboard",
    });
    expect(() =>
      telemetry.capture("shell_route_viewed", { email: "secret@example.com" } as never),
    ).toThrow("PostHog property is not approved");
  });

  it("is a deterministic no-op without a configured key", () => {
    const telemetry = new Telemetry(null);
    expect(() => telemetry.capture("theme_changed", { theme: "dark" })).not.toThrow();
  });

  it("captures every approved base event through the injectable transport", () => {
    const fake = transport();
    const telemetry = new Telemetry(fake);
    for (const event of APPROVED_EVENTS) telemetry.capture(event);
    expect(fake.capture).toHaveBeenCalledTimes(7);
    for (const event of APPROVED_EVENTS) {
      expect(fake.capture).toHaveBeenCalledWith(event, {});
    }
    telemetry.identify("user-id");
    telemetry.organization("org-id");
    expect(fake.identify).toHaveBeenCalledWith("user-id");
    expect(fake.group).toHaveBeenCalledWith("organization", "org-id");
  });

  it("rejects unapproved event names even at runtime", () => {
    expect(() => new Telemetry(transport()).capture("arbitrary_event" as never)).toThrow(
      "PostHog event is not approved",
    );
  });

  it("transport failures cannot break auth or tenancy", () => {
    const broken = () => {
      throw new Error("offline");
    };
    const telemetry = new Telemetry({
      capture: broken,
      identify: broken,
      group: broken,
      reset: broken,
    });
    expect(() => telemetry.capture("auth_signed_in")).not.toThrow();
    expect(() => telemetry.identify("user-id")).not.toThrow();
    expect(() => telemetry.organization("org-id")).not.toThrow();
    expect(() => telemetry.reset()).not.toThrow();
  });

  it("removes SDK-enriched auth URLs, PII and person properties before sending", () => {
    const id = "10000000-0000-0000-0000-000000000001";
    const properties = {
      token: "public-posthog-test-key",
      distinct_id: id,
      aal: "aal1",
      $current_url: "https://app.invalid/auth/callback#access_token=private-token",
      $referrer: "https://auth.invalid/verify?token_hash=private-hash",
      email: "private@example.com",
      refresh_token: "private-refresh",
      totp_secret: "private-totp",
      totp_code: "123456",
      $set: { email: "private@example.com" },
      $set_once: { $initial_current_url: "https://app.invalid/?token_hash=private-hash" },
    };
    for (const event of [...APPROVED_EVENTS, "$identify", "$groupidentify"]) {
      const sanitized = sanitizePostHogEvent({
        uuid: id,
        event,
        properties,
        $set: { email: "private@example.com" },
        $set_once: { email: "private@example.com" },
      });
      expect(sanitized?.properties).toEqual({
        token: "public-posthog-test-key",
        distinct_id: id,
        aal: "aal1",
      });
      expect(sanitized).not.toHaveProperty("$set");
      expect(sanitized).not.toHaveProperty("$set_once");
      expect(JSON.stringify(sanitized)).not.toContain("private");
    }
  });

  it("retains only the approved UUID organization group and static route values", () => {
    const org = "20000000-0000-0000-0000-000000000001";
    const sanitized = sanitizePostHogEvent({
      uuid: org,
      event: "$groupidentify",
      properties: {
        $group_type: "organization",
        $group_key: org,
        $groups: { organization: org, email: "private@example.com" },
        $group_set: { name: "Private workshop" },
        route_name: "/auth/callback?access_token=private-token",
        role: "private@example.com",
      },
    });
    expect(sanitized?.properties).toEqual({
      $group_type: "organization",
      $group_key: org,
      $groups: { organization: org },
    });
    expect(sanitizePostHogEvent({ uuid: org, event: "$pageview", properties: {} })).toBeNull();
    expect(sanitizePostHogEvent(null)).toBeNull();
  });

  it("disables implicit captures and installs the final privacy boundary", () => {
    expect(POSTHOG_PRIVACY_CONFIG).toMatchObject({
      autocapture: false,
      capture_pageview: false,
      capture_pageleave: false,
      capture_performance: false,
      capture_dead_clicks: false,
      capture_exceptions: false,
      disable_session_recording: true,
      disable_capture_url_hashes: true,
      save_referrer: false,
      save_campaign_params: false,
      advanced_disable_flags: true,
      before_send: sanitizePostHogEvent,
    });
  });
});

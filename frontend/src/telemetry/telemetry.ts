import posthog, { type BeforeSendFn, type PostHogConfig } from "posthog-js";

export const APPROVED_EVENTS = [
  "auth_magic_link_requested",
  "auth_signed_in",
  "organization_selected",
  "mfa_enrollment_started",
  "mfa_verified",
  "shell_route_viewed",
  "theme_changed",
] as const;

export type ApprovedEvent = (typeof APPROVED_EVENTS)[number];
export type ApprovedProperty = "role" | "aal" | "route_name" | "theme";
export type ApprovedProperties = Partial<Record<ApprovedProperty, string>>;

export interface TelemetryTransport {
  capture(event: string, properties?: Record<string, string>): void;
  identify(userId: string): void;
  group(groupType: string, groupId: string): void;
  reset(): void;
}

const approvedProperties = new Set<ApprovedProperty>(["role", "aal", "route_name", "theme"]);

const approvedValues: Record<ApprovedProperty, readonly string[]> = {
  role: ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"],
  aal: ["aal1", "aal2"],
  route_name: ["/dashboard", "/projects", "/catalogs/systems", "/settings/general"],
  theme: ["light", "dark"],
};
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// The SDK enriches even manual events with URLs and person properties. Filter at
// the final transport boundary, including identify/group, not just at capture().
export const sanitizePostHogEvent: BeforeSendFn = (event) => {
  if (!event || ![...APPROVED_EVENTS, "$identify", "$groupidentify"].includes(event.event)) {
    return null;
  }
  const source: Record<string, unknown> = event.properties ?? {};
  const properties: Record<string, unknown> = {};
  for (const property of approvedProperties) {
    const value = source[property];
    if (typeof value === "string" && approvedValues[property].includes(value)) {
      properties[property] = value;
    }
  }
  // These are transport identity fields, not additional business properties.
  // `token` here is PostHog's public project key, never a Supabase token.
  if (typeof source.token === "string") properties.token = source.token;
  for (const key of ["distinct_id", "$device_id", "$anon_distinct_id", "$user_id", "$group_key"]) {
    if (typeof source[key] === "string" && uuid.test(source[key])) {
      properties[key] = source[key];
    }
  }
  for (const key of ["$is_identified", "$process_person_profile"]) {
    if (typeof source[key] === "boolean") properties[key] = source[key];
  }
  if (source.$group_type === "organization") properties.$group_type = "organization";
  const groups = source.$groups;
  if (groups && typeof groups === "object" && "organization" in groups) {
    if (typeof groups.organization === "string" && uuid.test(groups.organization)) {
      properties.$groups = { organization: groups.organization };
    }
  }
  return { uuid: event.uuid, event: event.event, timestamp: event.timestamp, properties };
};

export const POSTHOG_PRIVACY_CONFIG: Partial<PostHogConfig> = {
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
  disable_external_dependency_loading: true,
  before_send: sanitizePostHogEvent,
};

export class Telemetry {
  constructor(private readonly transport: TelemetryTransport | null) {}

  capture(event: ApprovedEvent, properties: ApprovedProperties = {}): void {
    for (const key of Object.keys(properties)) {
      if (!approvedProperties.has(key as ApprovedProperty)) {
        throw new Error(`PostHog property is not approved: ${key}`);
      }
    }
    if (!(APPROVED_EVENTS as readonly string[]).includes(event)) {
      throw new Error(`PostHog event is not approved: ${event}`);
    }
    this.bestEffort(() => this.transport?.capture(event, properties as Record<string, string>));
  }

  identify(userId: string): void {
    this.bestEffort(() => this.transport?.identify(userId));
  }

  organization(organizationId: string): void {
    this.bestEffort(() => this.transport?.group("organization", organizationId));
  }

  reset(): void {
    this.bestEffort(() => this.transport?.reset());
  }

  private bestEffort(action: () => void): void {
    try {
      action();
    } catch {
      // Analytics failure cannot change authentication, tenancy or calculation.
    }
  }
}

function configuredTransport(): TelemetryTransport | null {
  const key = import.meta.env.VITE_POSTHOG_KEY;
  if (!key) {
    return null;
  }
  try {
    posthog.init(key, {
      ...POSTHOG_PRIVACY_CONFIG,
      api_host: import.meta.env.VITE_POSTHOG_HOST,
    });
    return posthog;
  } catch {
    return null;
  }
}

export const telemetry = new Telemetry(configuredTransport());

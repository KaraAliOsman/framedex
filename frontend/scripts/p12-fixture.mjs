/** Owned DEMO acceptance transport. Session values stay in memory. */
import { chromium, expect } from "@playwright/test";
import fs from "node:fs/promises";
export { fs, expect };
export const base = "http://127.0.0.1:5173";
const supa = process.env.SUPABASE_URL,
  anon = process.env.SUPABASE_ANON_KEY,
  org = process.env.DEKOPEN_FIXTURE_ORG_ID;
if (!org || !supa || !anon || new URL(supa).port !== "25331")
  throw new Error("Select the owned framedex-cola DEMO fixture explicitly.");
const sessions = new Map();
async function auth(role) {
  if (sessions.has(role)) return sessions.get(role);
  const response = await fetch(`${supa}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: anon, "Content-Type": "application/json" },
    body: JSON.stringify({
      email: `demo-${role}@fixture.dekopen.local`,
      password: "Demo-Fixture-2026!",
    }),
  });
  if (!response.ok) throw new Error(`Fixture login: ${response.status}`);
  const session = await response.json();
  sessions.set(role, session);
  return session;
}
export async function api(path, method = "GET", body, role = "manager") {
  const session = await auth(role);
  const response = await fetch(`http://127.0.0.1:8000/api/v1${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${session.access_token}`,
      "X-Organization-ID": org,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      `Domain fixture ${method} ${path}: ${response.status} ${data.error?.code ?? ""}`,
    );
  return data;
}
export function browser() {
  return chromium.launch();
}
export async function context(browser, role = "manager", width = 1440, theme = "light") {
  const session = await auth(role);
  return browser.newContext({
    viewport: {
      width,
      height: width === 390 ? 844 : width === 1024 ? 768 : width === 1280 ? 800 : 900,
    },
    storageState: {
      cookies: [],
      origins: [
        {
          origin: base,
          localStorage: [
            { name: "sb-127-auth-token", value: JSON.stringify(session) },
            { name: `dekopen.active_org.${session.user.id}`, value: org },
            { name: "dekopen.theme", value: theme },
          ],
        },
      ],
    },
  });
}

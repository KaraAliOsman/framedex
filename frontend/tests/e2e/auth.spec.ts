import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import * as OTPAuth from "otpauth";

import { environment } from "./support/environment";
import { requireMailpitHealthy, waitForMagicLink } from "./support/mailpit";

const supabaseUrl = requiredEnvironment("SUPABASE_URL");
const anonKey = requiredEnvironment("SUPABASE_ANON_KEY");
const serviceRoleKey = requiredEnvironment("SUPABASE_SERVICE_ROLE_KEY");
const mailpitUrl = environment("MAILPIT_URL") ?? "http://127.0.0.1:54324";
const djangoUrl = environment("DJANGO_URL") ?? "http://127.0.0.1:8000";

type FixtureUser = {
  email: string;
  userId: string;
  organizationId: string;
};

const createdFixtures: FixtureUser[] = [];

test.beforeEach(async () => {
  await requireMailpitHealthy(mailpitUrl);
});

test.afterEach(async () => {
  for (const fixture of createdFixtures.splice(0)) {
    const organization = await fetch(
      `${supabaseUrl}/rest/v1/tenancy_organizations?id=eq.${fixture.organizationId}`,
      { method: "DELETE", headers: adminHeaders() },
    );
    expect(organization.status).toBe(204);
    const user = await fetch(`${supabaseUrl}/auth/v1/admin/users/${fixture.userId}`, {
      method: "DELETE",
      headers: adminHeaders(),
    });
    expect(user.status).toBe(200);
  }
});

function requiredEnvironment(name: string): string {
  const value = environment(name);
  if (!value) throw new Error(`${name} is required for the real Supabase E2E`);
  return value;
}

function adminHeaders(): Record<string, string> {
  return {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
    "Content-Type": "application/json",
  };
}

async function setupUser(role: "OWNER" | "ESTIMATOR"): Promise<FixtureUser> {
  const suffix = crypto.randomUUID();
  const email = `shot04-${role.toLowerCase()}-${suffix}@example.com`;
  const userResponse = await fetch(`${supabaseUrl}/auth/v1/admin/users`, {
    method: "POST",
    headers: adminHeaders(),
    body: JSON.stringify({ email, email_confirm: true }),
  });
  expect(userResponse.ok).toBe(true);
  const user = (await userResponse.json()) as { id: string };
  const organizationId = crypto.randomUUID();
  createdFixtures.push({ email, userId: user.id, organizationId });
  const organizationResponse = await fetch(`${supabaseUrl}/rest/v1/tenancy_organizations`, {
    method: "POST",
    headers: { ...adminHeaders(), Prefer: "return=minimal" },
    body: JSON.stringify({
      id: organizationId,
      name: `E2E ${role}`,
      tax_id: `E2E-${suffix}`,
    }),
  });
  expect(organizationResponse.ok).toBe(true);
  const membershipResponse = await fetch(`${supabaseUrl}/rest/v1/tenancy_memberships`, {
    method: "POST",
    headers: { ...adminHeaders(), Prefer: "return=minimal" },
    body: JSON.stringify({
      org_id: organizationId,
      user_id: user.id,
      role,
      is_active: true,
    }),
  });
  expect(membershipResponse.ok).toBe(true);
  return { email, userId: user.id, organizationId };
}

function latestMagicLink(
  email: string,
  previousMessageId: string | null = null,
): Promise<{ id: string; link: string }> {
  return waitForMagicLink({
    baseUrl: mailpitUrl,
    supabaseUrl,
    recipient: email,
    excludedMessageIds: new Set(previousMessageId ? [previousMessageId] : []),
  });
}

async function requestMagicLink(page: Page, email: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Correo").fill(email);
  await page.getByRole("button", { name: "Enviar Magic Link" }).click();
  await expect(page.getByRole("status")).toContainText("Revisa el buzón local");
}

async function accessToken(page: Page): Promise<string> {
  return page.evaluate(() => {
    for (const key of Object.keys(window.localStorage)) {
      if (!key.startsWith("sb-") || !key.endsWith("-auth-token")) continue;
      const raw = window.localStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw) as { access_token?: string };
      if (parsed.access_token) return parsed.access_token;
    }
    throw new Error("Supabase session was not persisted by the SPA");
  });
}

function tokenClaims(token: string): { sub: string; aal: string } {
  const payload = token.split(".")[1];
  if (!payload) throw new Error("Supabase did not issue a JWT access token");
  return JSON.parse(atob(payload.replaceAll("-", "+").replaceAll("_", "/"))) as {
    sub: string;
    aal: string;
  };
}

async function followRealMagicLink(page: Page, link: string): Promise<void> {
  const callback = page.waitForRequest(
    (request) =>
      request.isNavigationRequest() && new URL(request.url()).pathname === "/auth/callback",
  );
  await page.goto(link);
  await callback;
}

async function assertRealIdentity(
  page: Page,
  request: APIRequestContext,
  fixture: FixtureUser,
  aal: "aal1" | "aal2",
): Promise<void> {
  const token = await accessToken(page);
  const claims = tokenClaims(token);
  expect(claims.sub).toBe(fixture.userId);
  expect(claims.aal).toBe(aal);
  const actualUser = await request.get(`${supabaseUrl}/auth/v1/user`, {
    headers: { Authorization: `Bearer ${token}`, apikey: anonKey },
  });
  expect(actualUser.status()).toBe(200);
  expect((await actualUser.json()).id).toBe(fixture.userId);
  const direct = await request.get(`${djangoUrl}/api/v1/auth/me/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Organization-ID": fixture.organizationId,
    },
  });
  expect(direct.status()).toBe(200);
  const me = await direct.json();
  expect(me.user.id).toBe(fixture.userId);
  expect(me.active_organization.id).toBe(fixture.organizationId);
  expect(me.aal).toBe(aal);
}

async function assertOwnerBlockedAtAal1(
  page: Page,
  request: APIRequestContext,
  fixture: FixtureUser,
): Promise<void> {
  const token = await accessToken(page);
  expect(tokenClaims(token).aal).toBe("aal1");
  const rejected = await request.get(`${djangoUrl}/api/v1/auth/me/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Organization-ID": fixture.organizationId,
    },
  });
  expect(rejected.status()).toBe(403);
  expect((await rejected.json()).error).toEqual({
    code: "mfa_required",
    detail: "OWNER requires aal2",
    required_aal: "aal2",
  });
}

test("real Magic Link reaches Mailpit and authenticates Django /auth/me", async ({
  page,
  request,
}) => {
  const fixture = await setupUser("ESTIMATOR");
  await requestMagicLink(page, fixture.email);
  const message = await latestMagicLink(fixture.email);
  const authMeResponse = page.waitForResponse(
    (response) => response.url().includes("/api/v1/auth/me/") && response.status() === 200,
  );
  await followRealMagicLink(page, message.link);
  await expect(page.getByTestId("app-shell")).toBeVisible();
  await authMeResponse;

  await assertRealIdentity(page, request, fixture, "aal1");

  for (const route of ["Proyectos", "Sistemas", "Ajustes", "Panel"]) {
    await page.getByRole("link", { name: route, exact: true }).click();
    await expect(page.getByTestId("app-shell")).toBeVisible();
  }
  const initialTheme = await page.locator("html").getAttribute("data-theme");
  await page.getByRole("button", { name: "Cambiar tema" }).click();
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme",
    initialTheme === "light" ? "dark" : "light",
  );
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute(
    "data-theme",
    initialTheme === "light" ? "dark" : "light",
  );
  await expect(page.getByTestId("app-shell")).toBeVisible();

  // A consumed email link must not create a second authenticated session.
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByTestId("login-page")).toBeVisible();
  await page.goto(message.link);
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByTestId("app-shell")).toHaveCount(0);
  await expect(accessToken(page)).rejects.toThrow("Supabase session was not persisted");
});

test("OWNER must complete real TOTP enrollment and challenge after each Magic Link", async ({
  page,
  request,
}) => {
  const fixture = await setupUser("OWNER");
  await requestMagicLink(page, fixture.email);
  const firstMessage = await latestMagicLink(fixture.email);
  await followRealMagicLink(page, firstMessage.link);
  await expect(page.getByTestId("mfa-page")).toBeVisible();
  await assertOwnerBlockedAtAal1(page, request, fixture);

  await page.getByRole("button", { name: "Configurar autenticador" }).click();
  await expect(page.getByTestId("totp-secret")).toBeVisible();
  const secret = (await page.getByTestId("totp-secret").textContent())?.trim() ?? "";
  const generator = new OTPAuth.TOTP({
    issuer: "Dekopen",
    label: fixture.email,
    algorithm: "SHA1",
    digits: 6,
    period: 30,
    secret: OTPAuth.Secret.fromBase32(secret),
  });
  const firstCode = generator.generate();
  await page.getByLabel("Código de seis dígitos").fill(firstCode);
  await page.getByRole("button", { name: "Verificar" }).click();
  await expect(page.getByTestId("app-shell")).toBeVisible();
  await assertRealIdentity(page, request, fixture, "aal2");

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByTestId("login-page")).toBeVisible();
  await requestMagicLink(page, fixture.email);
  const secondMessage = await latestMagicLink(fixture.email, firstMessage.id);
  expect(secondMessage.id).not.toBe(firstMessage.id);
  expect(secondMessage.link === firstMessage.link).toBe(false);
  await followRealMagicLink(page, secondMessage.link);
  await expect(page.getByTestId("mfa-page")).toBeVisible();
  await expect(page.getByLabel("Código de seis dígitos")).toBeVisible();
  await expect(page.getByTestId("totp-secret")).toHaveCount(0);
  await assertOwnerBlockedAtAal1(page, request, fixture);

  await expect
    .poll(() => generator.generate(), { timeout: 35_000, intervals: [500] })
    .not.toBe(firstCode);
  const secondCode = generator.generate();
  await page.getByLabel("Código de seis dígitos").fill(secondCode);
  await page.getByRole("button", { name: "Verificar" }).click();
  await expect(page.getByTestId("app-shell")).toBeVisible();
  await assertRealIdentity(page, request, fixture, "aal2");
});

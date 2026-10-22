import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as OTPAuth from "otpauth";
import { expect, test as base } from "@playwright/test";

import { environment } from "./environment";
import { requireMailpitHealthy, waitForMagicLink } from "./mailpit";
import type { MembershipRoleEnum } from "../../../src/api/generated/models";

type CatalogFixture = {
  systemId: string;
  stressId: string;
  pasteValues: (string | null)[];
  organizationId: string;
  projects?: { issued: string; draft: string };
  manualImportId?: string;
  manualArticleId?: string;
  manualSku?: string;
};

function required(name: string): string {
  const value = environment(name);
  if (!value) throw new Error(`${name} is required for catalog E2E`);
  return value;
}
function local(name: string): string {
  const url = new URL(required(name));
  if (!["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))
    throw new Error("Catalog fixtures require the isolated local stack");
  return url.origin;
}

export const test = base.extend<{
  catalog: CatalogFixture;
  catalogRole: MembershipRoleEnum;
  catalogProjects: boolean;
  doubleReadManual: boolean;
  lightCatalog: boolean;
  unpricedCatalog: boolean;
}>({
  catalogRole: ["OWNER", { option: true }],
  catalogProjects: [false, { option: true }],
  doubleReadManual: [false, { option: true }],
  lightCatalog: [false, { option: true }],
  unpricedCatalog: [false, { option: true }],
  catalog: [
    async (
      { page, catalogRole, catalogProjects, doubleReadManual, lightCatalog, unpricedCatalog },
      use,
    ) => {
      const supabaseUrl = local("SUPABASE_URL");
      const mailpit = local("MAILPIT_URL");
      const serviceKey = required("SUPABASE_SERVICE_ROLE_KEY");
      const adminHeaders = {
        apikey: serviceKey,
        Authorization: `Bearer ${serviceKey}`,
        "Content-Type": "application/json",
      };
      async function admin(path: string, method: string, body?: unknown) {
        const response = await fetch(`${supabaseUrl}${path}`, {
          method,
          headers: adminHeaders,
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: AbortSignal.timeout(15_000),
        });
        expect(response.ok, `${method} ${path}: ${response.status}`).toBe(true);
        return response;
      }
      const suffix = crypto.randomUUID();
      const organizationId = crypto.randomUUID();
      const email = `dk2-${suffix}@example.com`;
      let userId: string | undefined;
      try {
        await requireMailpitHealthy(mailpit);
        const user = await admin("/auth/v1/admin/users", "POST", {
          email,
          email_confirm: true,
          user_metadata: { full_name: "Juan del taller sintético" },
        });
        userId = ((await user.json()) as { id: string }).id;
        await admin("/rest/v1/tenancy_organizations", "POST", {
          id: organizationId,
          name: `DK2 E2E SYNTHETIC ${suffix}`,
          tax_id: `E2E-DK2-${suffix}`,
          subscription_tier: "STARTER",
        });
        await admin("/rest/v1/tenancy_memberships", "POST", {
          org_id: organizationId,
          user_id: userId,
          role: "OWNER",
          is_active: true,
        });
        // Service credentials and DB access remain in the runner. Only ordinary
        // Magic Link + real TOTP credentials ever enter the browser.
        const output = execFileSync(
          environment("PYTHON") ?? "python",
          [
            "scripts/seed_catalog_series_e2e.py",
            organizationId,
            userId,
            ...(doubleReadManual ? ["--double-read"] : []),
            ...(lightCatalog ? ["--light"] : []),
            ...(unpricedCatalog ? ["--unpriced"] : []),
          ],
          {
            cwd: fileURLToPath(new URL("../../../../", import.meta.url)),
            encoding: "utf8",
            timeout: 120_000,
            env: { ...process.env, PYTHONUTF8: "1" },
          },
        );
        const seeded = JSON.parse(output.trim()) as Omit<CatalogFixture, "organizationId">;
        expect(seeded.pasteValues).toHaveLength(5);
        if (catalogProjects)
          seeded.projects = JSON.parse(
            execFileSync(
              environment("PYTHON") ?? "python",
              ["scripts/seed_today_e2e.py", organizationId, userId],
              {
                cwd: fileURLToPath(new URL("../../../../", import.meta.url)),
                encoding: "utf8",
                timeout: 120_000,
                env: { ...process.env, PYTHONUTF8: "1" },
              },
            ).trim(),
          ) as { issued: string; draft: string };
        // Seed only with the fixture's ownership proof, then exercise the real
        // role through its ordinary session. Never relax the seeder's guard.
        if (catalogRole !== "OWNER")
          await admin(
            `/rest/v1/tenancy_memberships?org_id=eq.${organizationId}&user_id=eq.${userId}`,
            "PATCH",
            { role: catalogRole },
          );
        await page.goto("/login");
        await page.getByLabel("Correo", { exact: true }).fill(email);
        await page.getByRole("button", { name: "Enviar enlace de acceso", exact: true }).click();
        await expect(page.getByRole("status")).toContainText("Revisa tu correo para continuar");
        const message = await waitForMagicLink({ baseUrl: mailpit, supabaseUrl, recipient: email });
        await page.goto(message.link);
        if (catalogRole === "OWNER") {
          await page.getByRole("button", { name: "Configurar autenticador", exact: true }).click();
          const secret = (await page.getByTestId("totp-secret").textContent())?.trim() ?? "";
          const generator = new OTPAuth.TOTP({
            algorithm: "SHA1",
            digits: 6,
            period: 30,
            secret: OTPAuth.Secret.fromBase32(secret),
          });
          await page.getByLabel("Código de seis dígitos").fill(generator.generate());
          await page.getByRole("button", { name: "Verificar", exact: true }).click();
        }
        await expect(page.getByTestId("app-shell")).toBeVisible();
        await use({ ...seeded, organizationId });
      } finally {
        // Cell and price history deliberately prevent tenant deletion. Retain the
        // synthetic tenant until the owned stack ends; never disable immutability.
        if (userId) await admin(`/auth/v1/admin/users/${userId}`, "DELETE");
      }
    },
    { timeout: 180_000 },
  ],
});

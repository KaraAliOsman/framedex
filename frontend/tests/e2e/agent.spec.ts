import { expect } from "@playwright/test";

import { test } from "./support/catalog-series-fixture";
import { environment } from "./support/environment";

// P08 acceptance with the test provider's recorded rounds: a pasted WhatsApp
// becomes a draft work whose windows each cite their phrase, priced by the
// engine with a draft PDF; nothing is sent, and «Deshacer todo» removes it.
// Synthetic request written for DEKOPEN; no real client data.
const REQUEST =
  "Cotiza esto para Rodrigo Soto: Hola, necesito cotizar 2 ventanas oscilobatientes para el living " +
  "de 1,20 por 1,40, una del baño chiquita de 60 x 60 fija, una para el dormitorio de 1,20 x 1,00 " +
  "y otra para la cocina de 90 x 1,10. Todo en PVC blanco, termopanel. ¿Cuánto sería con instalación?";

test.use({ aiTrial: true, viewport: { width: 1440, height: 900 } });

test("a pasted request becomes a cited draft work, nothing is sent and undo removes it", async ({
  page,
  catalog,
}) => {
  test.setTimeout(240_000);
  const reading = page.waitForRequest(
    (request) =>
      new URL(request.url()).pathname === "/api/v1/pricing/simple-policy/" &&
      request.method() === "GET",
  );
  await page.goto("/settings/general?section=prices");
  const headers = {
    Authorization: (await reading).headers().authorization!,
    "X-Organization-ID": catalog.organizationId,
  };
  const backend = environment("DJANGO_URL")!;
  async function api(path: string, method = "GET", data?: unknown) {
    const response = await page.request.fetch(`${backend}/api/v1/${path}`, {
      method,
      headers,
      data,
    });
    return {
      status: response.status(),
      body: response.status() === 204 ? null : await response.json(),
    };
  }

  // «Lo habitual» of the company: the synthetic series, its first glass and finish.
  const options = await api(`projects/design-options/${catalog.systemId}/`);
  expect(options.status).toBe(200);
  const defaults = await api("organization/design-defaults/", "PUT", {
    values: {
      system_id: catalog.systemId,
      color: options.body.colors[0],
      glass_article_sku: options.body.glass_skus[0],
    },
  });
  expect(defaults.status, JSON.stringify(defaults.body)).toBe(200);
  // The agent runs on the test provider; every other capability stays as is.
  const settings = await api("ai/settings/");
  expect(settings.body.mock_available).toBe(true);
  const saved = await api("ai/settings/", "PUT", {
    expected_revision: settings.body.revision,
    monthly_budget_credits: null,
    routes: settings.body.routes.map((route: Record<string, unknown>) => ({
      capability: route.capability,
      provider: route.capability === "agent" ? "MOCK" : route.provider,
      provider_model: route.capability === "agent" ? "dekopen-recorded" : route.provider_model,
      timeout_s: route.timeout_s,
      retries: route.retries,
      tools_mode: route.tools_mode,
      input_usd_per_million: route.input_usd_per_million,
      output_usd_per_million: route.output_usd_per_million,
    })),
  });
  expect(saved.status, JSON.stringify(saved.body)).toBe(200);

  // The worker runs the job without the owner's second factor, so the quote
  // is delegated by an estimator, the role that prepares quotations.
  const supabase = environment("SUPABASE_URL")!;
  const serviceKey = environment("SUPABASE_SERVICE_ROLE_KEY")!;
  const me = await api("auth/me/");
  const demoted = await fetch(
    `${supabase}/rest/v1/tenancy_memberships?org_id=eq.${catalog.organizationId}&user_id=eq.${me.body.user.id}`,
    {
      method: "PATCH",
      headers: {
        apikey: serviceKey,
        Authorization: `Bearer ${serviceKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role: "ESTIMATOR" }),
    },
  );
  expect(demoted.ok).toBe(true);

  await page.goto("/dashboard");
  await page.getByRole("button", { name: "Buscar o ejecutar un comando", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Escribe un comando o busca…", exact: true })
    .fill(REQUEST);
  await page.getByRole("option", { name: /^Pedir a DEKOPEN/ }).click();
  const copilot = page.getByRole("dialog", { name: "Asistente" });
  await expect(copilot).toHaveClass(/is-docked/);
  await expect(copilot.getByLabel("¿Qué necesitas lograr?")).toHaveValue(REQUEST);
  await copilot.getByRole("radio", { name: "Omitir todo" }).click();
  await copilot.getByRole("button", { name: "Encargar", exact: true }).click();

  const origins = copilot.getByRole("region", { name: "Origen de las ventanas" });
  await expect(origins).toBeVisible({ timeout: 90_000 });
  await expect(origins.locator("mark")).toHaveCount(4);
  const windows = origins.getByRole("list", { name: "Ventanas y su frase" }).getByRole("listitem");
  await expect(windows).toHaveCount(4);
  await expect(windows.nth(1)).toContainText("Baño · «una del baño chiquita de 60 x 60 fija»");
  await expect(origins.getByRole("note")).toContainText("2 supuestos que conviene confirmar");
  await expect(origins.getByRole("note")).toContainText("Dormitorio · Apertura");
  await expect(origins.getByRole("note")).toContainText("Cocina · Apertura");

  // The work the agent created holds the four windows the engine accepted.
  const jobs = await api("ai/jobs/");
  const job = (jobs.body.results ?? jobs.body)[0] as { id: string; refs: { project_id?: string } };
  const projectId = job.refs.project_id!;
  const created = await api(`projects/${projectId}/`);
  expect(created.status).toBe(200);
  expect(created.body.positions).toHaveLength(4);
  expect(
    created.body.positions.reduce(
      (sum: number, item: { quantity: number }) => sum + item.quantity,
      0,
    ),
  ).toBe(5);

  // Price and draft PDF with the person's own session; nothing is issued or sent.
  await copilot.getByRole("button", { name: "Aprobar y aplicar", exact: true }).click();
  await expect(
    copilot.getByText("Nada se envió: emitir y enviar siguen siendo tuyos."),
  ).toBeVisible({
    timeout: 60_000,
  });
  const priced = await api(`projects/${projectId}/`);
  expect(priced.body.status).toBe("DRAFT");
  expect(priced.body.working_price.state).toBe("READY");

  await copilot.getByRole("button", { name: "Deshacer todo", exact: true }).click();
  await expect(
    copilot.getByText(/^Deshice (todo y quité la obra borrador|las ventanas)/),
  ).toBeVisible({
    timeout: 30_000,
  });
  const after = await api(`projects/${projectId}/`);
  if (after.status === 200) expect(after.body.positions).toHaveLength(0);
  else expect(after.status).toBe(404);
});

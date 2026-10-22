import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { apiMutator } from "../../api/apiMutator";
import { CatalogChangeReviewProvider } from "./CatalogChangeReview";

vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    session: { user: { id: "owner" } },
    me: { active_organization: { id: "org" } },
  }),
}));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function rejection() {
  const row = {
    key: "cut:0",
    group: "profile_cuts",
    index: 0,
    field: "length_mm",
    role: "FRAME",
    sku: "M-01",
    quantity: 2,
  };
  return new Response(
    JSON.stringify({
      error: { code: "catalog_reference_changed" },
      golden_review: {
        review_token: "accepted-diff",
        changes: [
          {
            reference_id: "ref",
            before: { error: null, measurements: [{ ...row, value_mm: "1206.25" }] },
            after: { error: null, measurements: [{ ...row, value_mm: "1208.25" }] },
          },
        ],
      },
    }),
    { status: 409, headers: { "Content-Type": "application/json" } },
  );
}

it("shows exact before/after and cancellation rejects without replay", async () => {
  const transport = vi.fn(async () => rejection());
  vi.stubGlobal("fetch", transport);
  render(
    <CatalogChangeReviewProvider>
      <p>Ficha</p>
    </CatalogChangeReviewProvider>,
  );
  let pending!: Promise<unknown>;
  act(() => {
    pending = apiMutator("/api/v1/catalogs/systems/s/", { method: "PATCH", body: "{}" }).catch(
      (error: unknown) => error,
    );
  });
  const dialog = await screen.findByRole("dialog");
  expect(dialog).toHaveTextContent(/1\s206,25/);
  expect(dialog).toHaveTextContent(/1\s208,25/);
  fireEvent.click(screen.getByRole("button", { name: "Conservar mi borrador" }));
  await expect(pending).resolves.toMatchObject({ status: 409 });
  expect(transport).toHaveBeenCalledOnce();
});

it("queues concurrent reviews and resolves each exact token only after its click", async () => {
  const transport = vi.fn(async (_url: string, init?: RequestInit) =>
    new Headers(init?.headers).has("X-Catalog-Review")
      ? new Response("{}", { status: 200 })
      : rejection(),
  );
  vi.stubGlobal("fetch", transport);
  render(
    <CatalogChangeReviewProvider>
      <p>Ficha</p>
    </CatalogChangeReviewProvider>,
  );
  let first!: Promise<unknown>, second!: Promise<unknown>;
  act(() => {
    first = apiMutator("/api/v1/catalogs/systems/first/", { method: "PATCH", body: "{}" });
    second = apiMutator("/api/v1/catalogs/systems/second/", { method: "PATCH", body: "{}" });
  });
  await screen.findByRole("dialog");
  expect(screen.getAllByRole("dialog")).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambio y volver a verificar" }));
  await first;
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambio y volver a verificar" }));
  await second;
  expect(transport).toHaveBeenCalledTimes(4);
});

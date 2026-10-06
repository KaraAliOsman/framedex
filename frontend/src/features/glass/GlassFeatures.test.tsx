import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  catalogGlassPreview,
  catalogGlassRules,
  catalogGlassRulesReplace,
  catalogGlassVariantPublish,
  productionGlassOrder,
} from "../../api/generated/dekopen";
import type { DesignOptions, GlassPreviewOutput } from "../../api/generated/models";
import { GlassSelector } from "./GlassSelector";
import { GlassRulesSettings } from "./GlassRulesSettings";
import { GlassOrderPanel } from "./GlassOrderPanel";
import { glassContext } from "./useGlassPreview";
import type { GlassProduct } from "./glassModel";
import { t } from "../../i18n/es-CL";

const identity = vi.hoisted(() => ({ role: "ESTIMATOR" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    me: { active_organization: { id: "org-a", role: identity.role } },
  }),
}));
vi.mock("../../api/generated/dekopen", async (original) => ({
  ...(await original<typeof import("../../api/generated/dekopen")>()),
  catalogGlassPreview: vi.fn(),
  catalogGlassRules: vi.fn(),
  catalogGlassRulesReplace: vi.fn(),
  catalogGlassVariantPublish: vi.fn(),
  productionGlassOrder: vi.fn(),
}));
const product: GlassProduct = {
  authority_id: "frozen-mapping",
  name: "Float de catálogo",
  source: "Ficha revisada del proveedor",
  synthetic: false,
  composition: {
    layers: [
      {
        kind: "PANE",
        interlayers: [],
        plies: [
          {
            thickness_mm: "4",
            type: "FLOAT",
            color: "CLEAR",
            coating_face: null,
            supplier_sku: "F4",
          },
        ],
      },
    ],
  },
  properties: {},
  limits: {},
  billing: {},
};
const preview: GlassPreviewOutput = {
  product,
  notation: "4",
  total_thickness_mm: "4",
  net_thickness_mm: "4",
  weight_kg_m2: "10",
  section: [{ kind: "PANE", x_mm: "0", width_mm: "4", label: "Float incoloro" }],
  section_error: null,
  findings: [],
  price: null,
  price_error: null,
  alternative_skus: [],
  dimensions_known: true,
};
const choice = {
  sku: "F4",
  spec: "4",
  product,
  total_thickness_mm: "4",
  weight_kg_m2: "10",
  compatible: true,
};
const rule = {
  code: "RULE",
  name: "Puerta vidriada",
  zone: "DOOR",
  source: "Ficha aportada",
  synthetic: false,
  mandatory: false,
};
function mount(children: React.ReactNode) {
  return render(
    <MemoryRouter>
      <QueryClientProvider
        client={
          new QueryClient({
            defaultOptions: {
              queries: { retry: false },
            },
          })
        }
      >
        {children}
      </QueryClientProvider>
    </MemoryRouter>,
  );
}
function selector(onPatch = vi.fn()) {
  mount(
    <GlassSelector
      options={{ system_id: "system-a" } as DesignOptions}
      choices={[choice]}
      node={{ id: "B1", type: "BAY", glass_article_sku: "F4", glass_product: product }}
      context={{ width_mm: "800", height_mm: "1200" }}
      busy={false}
      onPatch={onPatch}
    />,
  );
  return onPatch;
}
beforeEach(() => {
  vi.clearAllMocks();
  identity.role = "ESTIMATOR";
  vi.mocked(catalogGlassPreview).mockResolvedValue({
    data: preview,
    status: 200,
    headers: new Headers(),
  });
  vi.mocked(catalogGlassRules).mockResolvedValue({
    data: { items: [], examples: [rule], revision: "r1", configured: false },
    status: 200,
    headers: new Headers(),
  });
});
afterEach(cleanup);

it("sends structured door use to glass safety even when its legacy alias is absent", () => {
  expect(
    glassContext(
      {
        id: "door",
        type: "BAY",
        opening_use: "DOOR",
        opening: {
          movement: "TURN",
          hinge_side: "LEFT",
          direction: "OUTWARD",
          leaf_role: "SINGLE",
          fixed_in_sash: false,
        },
      },
      "m1",
      null,
    ),
  ).toMatchObject({ opening_use: "DOOR", opening_type: "FIXED" });
  expect(
    glassContext({ id: "old-door", type: "BAY", opening_type: "DOOR_ENTRY" }, "m1", null),
  ).toMatchObject({ opening_use: undefined, opening_type: "DOOR_ENTRY" });
});

it("assigns recipe authority, supplier SKU and derived bead thickness together", async () => {
  const patch = selector();
  fireEvent.click(await screen.findByRole("button", { name: /Float de catálogo/ }));
  expect(patch).toHaveBeenCalledWith({
    glass_article_sku: "F4",
    glass_spec: "4",
    glass_product: product,
    glass_thickness_mm: "4",
  });
});

it("keeps composition read-only for an estimator and shows the motor section", async () => {
  selector();
  await screen.findByRole("button", { name: /Float de catálogo/ });
  fireEvent.click(screen.getByText(t("glass.advanced")));
  await screen.findByText(t("glass.section"));
  fireEvent.click(screen.getByRole("button", { name: t("glass.compose") }));
  const dialog = screen.getByRole("dialog");
  expect(within(dialog).getByLabelText(t("glass.name"))).toBeDisabled();
  expect(within(dialog).getByText(t("glass.publishRole"))).toBeInTheDocument();
  expect(within(dialog).queryByRole("button", { name: t("glass.publish") })).toBeNull();
});

it("requires a reviewed diff before publishing and assigns the persisted authority", async () => {
  identity.role = "WORKSHOP_MANAGER";
  const persisted = { ...product, authority_id: "new-mapping" };
  vi.mocked(catalogGlassVariantPublish).mockResolvedValue({
    status: 201,
    headers: new Headers(),
    data: {
      mapping_id: "new-mapping",
      product: persisted,
      spec: "4",
      technical_sku: "VARIANT",
    },
  });
  const patch = selector();
  await screen.findByRole("button", { name: /Float de catálogo/ });
  fireEvent.click(screen.getByText(t("glass.advanced")));
  await screen.findByText(t("glass.section"));
  fireEvent.click(screen.getByRole("button", { name: t("glass.compose") }));
  const dialog = screen.getByRole("dialog");
  fireEvent.change(within(dialog).getByLabelText(t("glass.catalogCode")), {
    target: { value: "VARIANT" },
  });
  fireEvent.change(within(dialog).getByLabelText(t("glass.purchaseCode")), {
    target: { value: "BUY-VARIANT" },
  });
  fireEvent.change(within(dialog).getByLabelText(t("glass.supplier")), {
    target: { value: "Vidriero" },
  });
  expect(vi.mocked(catalogGlassVariantPublish)).not.toHaveBeenCalled();
  const review = within(dialog).getByRole("button", { name: t("glass.reviewPublish") });
  await waitFor(() => expect(review).toBeEnabled());
  fireEvent.click(review);
  expect(within(dialog).getByText(t("glass.before"))).toBeInTheDocument();
  fireEvent.click(within(dialog).getByRole("button", { name: t("glass.publish") }));
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(vi.mocked(catalogGlassVariantPublish)).toHaveBeenCalledWith(
    expect.objectContaining({ product, confirmed: true, technical_sku: "VARIANT" }),
  );
  expect(patch).toHaveBeenCalledWith(
    expect.objectContaining({ glass_product: persisted, glass_article_sku: "VARIANT" }),
  );
});

it("reviews rules and uses optimistic concurrency before replacing their history", async () => {
  vi.mocked(catalogGlassRulesReplace).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { items: [rule], examples: [rule], revision: "r2", configured: true },
  });
  mount(<GlassRulesSettings orgId="org-a" canWrite />);
  fireEvent.click(await screen.findByRole("button", { name: t("glass.examples") }));
  fireEvent.click(screen.getByRole("button", { name: t("glass.reviewRules") }));
  expect(vi.mocked(catalogGlassRulesReplace)).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: t("glass.applyRules") }));
  await waitFor(() =>
    expect(vi.mocked(catalogGlassRulesReplace)).toHaveBeenCalledWith(
      { items: [rule] },
      { headers: { "If-Match": '"r1"' } },
    ),
  );
  await screen.findByRole("button", { name: t("glass.undoRules") });
});

it("loads the supplier view without invoking renderer format negotiation", async () => {
  vi.mocked(productionGlassOrder).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      rows: [],
      labels: [],
      revisions: [],
      authority: "BOM sellado",
    },
  });
  mount(<GlassOrderPanel orderIds={["ot-1", "ot-2"]} />);
  fireEvent.click(screen.getByRole("button", { name: t("glass.reviewOrder") }));
  await screen.findByText(t("glass.noGlass"));
  expect(vi.mocked(productionGlassOrder)).toHaveBeenCalledWith({
    orders: "ot-1,ot-2",
    export_format: "JSON",
  });
});

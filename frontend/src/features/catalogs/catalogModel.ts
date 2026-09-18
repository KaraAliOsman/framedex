import * as client from "../../api/generated/dekopen";
import type {
  SystemWriteRequest,
  ArticleWriteRequest,
  BeadWriteRequest,
  KitWriteRequest,
  CatalogHardwareComponentRequest,
  SystemResponse,
  ArticleResponse,
  BeadResponse,
  KitResponse,
} from "../../api/generated/models";

export type SystemWrite = SystemWriteRequest;
export type ArticleWrite = ArticleWriteRequest;
export type BeadWrite = BeadWriteRequest;
export type KitWrite = KitWriteRequest;
export type HardwareComponent = CatalogHardwareComponentRequest;
export type Writes = {
  systems: SystemWrite;
  articles: ArticleWrite;
  glazing: BeadWrite;
  "hardware-kits": KitWrite;
};
export type Resource = keyof Writes;
type Responses = {
  systems: SystemResponse;
  articles: ArticleResponse;
  glazing: BeadResponse;
  "hardware-kits": KitResponse;
};
export type Row<R extends Resource> = Responses[R];
export type CatalogData = { [R in Resource]: Row<R>[] };

export type Field = {
  name: string;
  kind: "text" | "decimal" | "integer" | "boolean" | "select" | "system" | "bead";
  optional?: boolean;
  places?: number;
  maxLength?: number;
  options?: readonly string[];
};

type Group = { title: string; fields: Field[] };

const text = (name: string, maxLength?: number, optional = false): Field => ({
  name,
  kind: "text",
  maxLength,
  optional,
});

const decimal = (name: string, places = 2, optional = false): Field => ({
  name,
  kind: "decimal",
  places,
  optional,
});

const measures = (...names: string[]): Field[] => names.map((name) => decimal(name));
const integer = (name: string): Field => ({ name, kind: "integer" });
const active: Field = { name: "is_active", kind: "boolean" };
const material: Field = {
  name: "material",
  kind: "select",
  options: ["PVC", "ALUMINIUM"],
};
const rail: Field = {
  name: "rail_type",
  kind: "select",
  options: ["dual", "mono"],
};
const system: Field = { name: "system_id", kind: "system" };

export const schemas: Record<Resource, Group[]> = {
  systems: [
    {
      title: "identity",
      fields: [
        text("name", 150),
        text("code", 50),
        material,
        decimal("depth_mm"),
        integer("chamber_count"),
        integer("version"),
        active,
      ],
    },
    {
      title: "glazingGeometry",
      fields: [
        ...measures("sash_overlap_mm", "glass_clearance_white_mm", "glass_clearance_foil_mm"),
        decimal("chamber_clearance_mm", 2, true),
      ],
    },
    {
      title: "slidingGeometry",
      fields: [
        rail,
        ...measures(
          "pulley_height_mm",
          "central_overlap_mm",
          "sliding_lateral_clearance_mm",
          "sliding_end_add_mm",
          "corner_bracket_loss_mm",
          "hook_depth_mm",
          "sliding_glazing_deduction_width_mm",
          "sliding_glazing_deduction_height_mm",
        ),
      ],
    },
    {
      title: "doorGeometry",
      fields: measures(
        "door_threshold_mm",
        "door_bottom_clearance_mm",
        "door_leaf_side_clearance_mm",
      ),
    },
  ],
  articles: [
    {
      title: "identity",
      fields: [
        system,
        text("sku", 100),
        text("name", 255),
        material,
        {
          name: "role",
          kind: "select",
          options: [
            "FRAME",
            "SASH",
            "MULLION_V",
            "MULLION_H",
            "INVERSOR",
            "GLAZING_BEAD",
            "COUPLER",
            "ADDITIONAL",
            "THRESHOLD",
          ],
        },
      ],
    },
    {
      title: "profileGeometry",
      fields: measures("face_width_mm", "commercial_length_mm", "welding_loss_mm"),
    },
    {
      title: "reinforcement",
      fields: [
        text("reinforcement_sku", 100, true),
        decimal("reinforcement_gap_mm"),
        decimal("weight_kg_m", 4),
        decimal("steel_weight_kg_m", 4),
      ],
    },
  ],
  glazing: [
    {
      title: "compatibility",
      fields: [
        system,
        { name: "bead_article_id", kind: "bead" },
        ...measures(
          "glass_thickness_mm",
          "bead_width_mm",
          "gasket_interior_mm",
          "gasket_exterior_mm",
          "cut_add_mm",
        ),
        active,
      ],
    },
  ],
  "hardware-kits": [
    {
      title: "identity",
      fields: [
        { ...system, optional: true },
        text("sku", 100),
        text("name", 255),
        {
          name: "opening_type",
          kind: "select",
          options: ["TURN", "TILT_TURN", "SLIDING", "DOOR", "AWNING"],
        },
        rail,
        active,
      ],
    },
    {
      title: "leafLimits",
      fields: measures(
        "min_leaf_width_mm",
        "max_leaf_width_mm",
        "min_leaf_height_mm",
        "max_leaf_height_mm",
        "max_leaf_weight_kg",
      ),
    },
    {
      title: "hardware",
      fields: [
        integer("carriages_qty"),
        integer("stay_arms_qty"),
        decimal("weight_kg", 2, true),
        decimal("carriage_capacity_kg", 2, true),
      ],
    },
  ],
};

// Decimal strings remain strings throughout form state and transport.
export const exact = (value: string): string => value.trim().replace(",", ".");

export function fieldsFor(resource: Resource): Field[] {
  return schemas[resource].flatMap((group) => group.fields);
}

export function initialDraft(
  resource: Resource,
  row: object | undefined,
  systemId: string | null,
): Record<string, string> {
  const source = (row ?? {}) as Record<string, unknown>;
  return Object.fromEntries(
    fieldsFor(resource).map((field) => [
      field.name,
      source[field.name] == null
        ? field.name === "system_id"
          ? (systemId ?? "")
          : ""
        : String(source[field.name]),
    ]),
  );
}

export function writeFromDraft<R extends Resource>(
  resource: R,
  draft: Record<string, string>,
  contents: HardwareComponent[],
): Writes[R] {
  const values: Record<string, string | number | boolean | null | HardwareComponent[]> = {};
  for (const field of fieldsFor(resource)) {
    const value = draft[field.name]?.trim() ?? "";
    if (value === "" && field.optional) {
      values[field.name] = null;
    } else if (field.kind === "integer") {
      // Integer counters only; never dimensions, weights, quantities or money.
      const count = Number(value);
      if (
        !/^-?\d+$/.test(value) ||
        !Number.isSafeInteger(count) ||
        count < -2147483648 ||
        count > 2147483647
      )
        throw new Error("Invalid integer");
      values[field.name] = count;
    } else if (field.kind === "boolean") {
      if (value !== "true" && value !== "false") throw new Error("Missing boolean");
      values[field.name] = value === "true";
    } else {
      values[field.name] = field.kind === "decimal" ? exact(value) : value;
    }
  }
  if (resource === "hardware-kits") {
    values.contents = contents.map((item) => ({
      sku: item.sku.trim(),
      name: item.name.trim(),
      qty: exact(item.qty),
      unit: item.unit.trim(),
    }));
  }
  // Only schema-declared writable fields enter the request.
  return values as unknown as Writes[R];
}

export function catalogApi(orgId: string) {
  const options = { headers: { "X-Organization-ID": orgId } };
  return {
    async list<R extends Resource>(resource: R, signal?: AbortSignal): Promise<Row<R>[]> {
      const request = { ...options, signal };
      const response =
        resource === "systems"
          ? await client.catalogSystemList(request)
          : resource === "articles"
            ? await client.catalogArticleList(undefined, request)
            : resource === "glazing"
              ? await client.catalogBeadList(undefined, request)
              : await client.catalogKitList(undefined, request);
      if (response.status !== 200) throw new Error("catalog_read_failed");
      return response.data.items as Row<R>[];
    },
    async save<R extends Resource>(
      resource: R,
      body: Writes[R],
      id?: string,
      revision?: string,
    ): Promise<Row<R>> {
      const options = {
        headers: { "X-Organization-ID": orgId, ...(id ? { "If-Match": `"${revision}"` } : {}) },
      };
      const response =
        resource === "systems"
          ? id
            ? await client.catalogSystemUpdate(id, body as SystemWrite, options)
            : await client.catalogSystemCreate(body as SystemWrite, options)
          : resource === "articles"
            ? id
              ? await client.catalogArticleUpdate(id, body as ArticleWrite, options)
              : await client.catalogArticleCreate(body as ArticleWrite, options)
            : resource === "glazing"
              ? id
                ? await client.catalogBeadUpdate(id, body as BeadWrite, options)
                : await client.catalogBeadCreate(body as BeadWrite, options)
              : id
                ? await client.catalogKitUpdate(id, body as KitWrite, options)
                : await client.catalogKitCreate(body as KitWrite, options);
      if (response.status !== 200 && response.status !== 201)
        throw new Error("catalog_write_failed");
      return response.data as Row<R>;
    },
    async remove(resource: Resource, id: string, revision: string): Promise<void> {
      const options = { headers: { "X-Organization-ID": orgId, "If-Match": `"${revision}"` } };
      const response =
        resource === "systems"
          ? await client.catalogSystemDelete(id, options)
          : resource === "articles"
            ? await client.catalogArticleDelete(id, options)
            : resource === "glazing"
              ? await client.catalogBeadDelete(id, options)
              : await client.catalogKitDelete(id, options);
      if (response.status !== 204) throw new Error("catalog_delete_failed");
    },
  };
}

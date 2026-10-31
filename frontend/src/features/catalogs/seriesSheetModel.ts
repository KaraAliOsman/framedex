import type { CellChangeRequest, SeriesCell, SeriesSheet } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { domainLabels } from "../../i18n/domainLabels";
import type { EditableColumn, EditableRow, TableChange } from "../../ui/EditableTable";
import { schemas, type Resource } from "./catalogModel";

export const seriesTabs = [
  { id: "profiles", label: "Perfiles" },
  { id: "rules", label: "Reglas" },
  { id: "hardware", label: "Herrajes" },
  { id: "glazing_colors", label: "Vidrios y colores" },
  { id: "typologies", label: "Tipologías" },
  { id: "prices", label: "Precios" },
] as const;
export type SeriesTab = (typeof seriesTabs)[number]["id"];
export type Binding = { cell: SeriesCell; index?: number; field?: string };
export type SheetTable = {
  id: string;
  label: string;
  columns: EditableColumn[];
  rows: EditableRow[];
  bindings: Record<string, Record<string, Binding>>;
};

export const address = (cell: Pick<SeriesCell, "resource" | "row_id" | "field">) =>
  JSON.stringify([cell.resource, cell.row_id, cell.field]);

export function usageLabel(usage: SeriesSheet["usage"]): string {
  if (usage.is_example) return "Ejemplo";
  if (!usage.level) return "Completar serie";
  return {
    DRAWABLE: "Lista para dibujar",
    QUOTABLE: "Lista para cotizar",
    MANUFACTURABLE: "Lista para fabricar",
    MACHINE_READY: "Lista para máquina",
  }[usage.level];
}

function column(resource: Resource, id: string): EditableColumn {
  const field = schemas[resource].flatMap((group) => group.fields).find((item) => item.name === id);
  return {
    id,
    label: (field?.label ?? t(`catalog.field.${id}` as Parameters<typeof t>[0])).replace(
      /\s*\((?:mm|kg(?:\/m)?)\)$/,
      "",
    ),
    kind: field?.kind === "decimal" || field?.kind === "integer" ? "decimal" : "text",
    precision: field?.kind === "integer" ? 0 : (field?.places ?? 2),
    nullable: field?.optional ?? false,
    readOnly: id === "sku",
    ...decimalBounds(resource, id),
    ...(id.endsWith("_mm")
      ? { unit: "mm" }
      : id.includes("weight")
        ? { unit: id.endsWith("_kg_m") ? "kg/m" : "kg" }
        : {}),
  };
}

/** Mirrors the write serializers' lexical bounds; the API validates each batch again. */
function decimalBounds(resource: Resource, id: string): Partial<EditableColumn> {
  if (resource === "systems") {
    const small = [
      "sash_overlap_mm",
      "glass_clearance_white_mm",
      "glass_clearance_foil_mm",
      "pulley_height_mm",
      "central_overlap_mm",
      "sliding_lateral_clearance_mm",
      "sliding_end_add_mm",
      "corner_bracket_loss_mm",
      "hook_depth_mm",
      "door_threshold_mm",
      "door_bottom_clearance_mm",
    ];
    return id.endsWith("_mm")
      ? {
          min: ["depth_mm", "chamber_clearance_mm"].includes(id) ? "0.01" : "0",
          max: small.includes(id) ? "99.99" : "99999999.99",
        }
      : {};
  }
  if (resource === "articles") {
    if (id === "weight_kg_m" || id === "steel_weight_kg_m")
      return { min: id === "weight_kg_m" ? "0.0001" : "0", max: "9999.9999" };
    return id.endsWith("_mm")
      ? {
          min: ["face_width_mm", "commercial_length_mm", "cut_rule.cut_step_mm"].includes(id)
            ? "0.01"
            : "0",
          max: "99999999.99",
        }
      : {};
  }
  if (resource === "glazing" && id.endsWith("_mm"))
    return {
      min: ["glass_thickness_mm", "bead_width_mm"].includes(id) ? "0.01" : "0",
      max: "9999.99",
    };
  if (resource === "hardware-kits" && (id.endsWith("_mm") || id === "max_leaf_weight_kg"))
    return { min: "0.01", max: id === "max_leaf_weight_kg" ? "9999.99" : "99999999.99" };
  return {};
}

/** Projection only: every numeric lexeme comes unchanged from the API. */
export function sheetTables(sheet: SeriesSheet, tab: SeriesTab): SheetTable[] {
  const indexed = new Map(sheet.cells.map((cell) => [address(cell), cell]));
  const cellAt = (resource: Resource, rowId: string, field: string) =>
    indexed.get(address({ resource, row_id: rowId, field }));

  function records(
    id: string,
    label: string,
    resource: Resource,
    items: { id: string; name?: string }[],
    fields: string[],
  ): SheetTable {
    const bindings: SheetTable["bindings"] = {};
    return {
      id,
      label,
      columns: fields.map((field) => column(resource, field)),
      bindings,
      rows: items.map((item) => {
        bindings[item.id] = {};
        return {
          id: item.id,
          label: item.name ?? "Junquillo",
          values: Object.fromEntries(
            fields.map((field) => {
              const cell = cellAt(resource, item.id, field);
              if (cell) bindings[item.id]![field] = { cell };
              const fallback = (item as Record<string, unknown>)[field];
              return [field, cell ? cell.value : typeof fallback === "string" ? fallback : null];
            }),
          ),
        };
      }),
    };
  }

  function arrayTable(
    id: string,
    label: string,
    cellField: string,
    items: Record<string, unknown>[],
    columns: EditableColumn[],
    name: (item: Record<string, unknown>, index: number) => string,
  ): SheetTable {
    const cell = cellAt("systems", sheet.id, cellField);
    const bindings: SheetTable["bindings"] = {};
    return {
      id,
      label,
      columns,
      bindings,
      rows: items.map((item, index) => {
        const rowId = `${id}-${index}`;
        bindings[rowId] = {};
        return {
          id: rowId,
          label: name(item, index),
          values: Object.fromEntries(
            columns.map((col) => {
              if (cell) bindings[rowId]![col.id] = { cell, index, field: col.id };
              return [
                col.id,
                item[col.id] === null || item[col.id] === undefined ? null : String(item[col.id]),
              ];
            }),
          ),
        };
      }),
    };
  }

  if (tab === "profiles")
    return [
      records("profiles", "Perfiles", "articles", sheet.tabs.profiles, [
        "sku",
        "face_width_mm",
        "commercial_length_mm",
        "weight_kg_m",
      ]),
    ];

  if (tab === "hardware")
    return [
      records("hardware", "Herrajes", "hardware-kits", sheet.tabs.hardware, [
        "sku",
        "min_leaf_width_mm",
        "max_leaf_width_mm",
        "min_leaf_height_mm",
        "max_leaf_height_mm",
        "max_leaf_weight_kg",
      ]),
    ];

  if (tab === "rules") {
    const bindings: SheetTable["bindings"] = {};
    const fields = schemas.systems
      .filter(
        (group) =>
          !["identity", "slidingGeometry", "doorGeometry"].includes(group.title) ||
          (group.title === "slidingGeometry" &&
            ["SLIDING", "LIFT_SLIDE"].includes(sheet.tabs.rules.system_family ?? "")) ||
          (group.title === "doorGeometry" && sheet.tabs.rules.system_family === "DOOR"),
      )
      .flatMap((group) => group.fields)
      .filter((field) => field.kind === "decimal" && field.name.endsWith("_mm"));
    const rows: EditableRow[] = [];
    function add(resource: Resource, rowId: string, field: string, applies: string, label: string) {
      const cell = cellAt(resource, rowId, field);
      if (!cell) return;
      const id = address(cell);
      const { precision, nullable, min, max } = column(resource, field);
      bindings[id] = { value: { cell } };
      rows.push({
        id,
        label,
        values: { applies, value: cell.value },
        cellOptions: { value: { precision, nullable, min, max } },
        suggested: cell.origin === "SUGGESTED",
      });
    }
    for (const field of fields)
      add(
        "systems",
        sheet.id,
        field.name,
        sheet.tabs.rules.name,
        column("systems", field.name).label,
      );
    for (const profile of sheet.tabs.profiles) {
      for (const field of schemas.articles
        .flatMap((group) => group.fields)
        .filter(
          (field) =>
            field.name.includes(".") && field.name.endsWith("_mm") && field.kind === "decimal",
        ))
        add("articles", profile.id, field.name, profile.name, column("articles", field.name).label);
    }
    return [
      {
        id: "rules",
        label: "Reglas",
        columns: [
          { id: "applies", label: "Se aplica a", readOnly: true },
          {
            id: "value",
            label: "Valor",
            kind: "decimal",
            precision: 2,
            nullable: true,
            unit: "mm",
          },
        ],
        rows,
        bindings,
      },
    ];
  }

  if (tab === "glazing_colors") {
    const finishesCell = cellAt("systems", sheet.id, "finishes");
    const colors: SheetTable = {
      id: "finishes",
      label: "Colores y acabados",
      columns: [{ id: "code", label: "Código de acabado" }],
      bindings: {},
      rows: sheet.tabs.glazing_colors.finishes.map((code, index) => ({
        id: `finish-${index}`,
        label: `Acabado ${index + 1}`,
        values: { code },
      })),
    };
    for (const [index, row] of colors.rows.entries())
      if (finishesCell) colors.bindings[row.id] = { code: { cell: finishesCell, index } };
    return [
      records("beads", "Vidrios y junquillos", "glazing", sheet.tabs.glazing_colors.beads, [
        "glass_thickness_mm",
        "bead_width_mm",
        "gasket_interior_mm",
        "gasket_exterior_mm",
        "cut_add_mm",
      ]),
      colors,
      ...(sheet.tabs.rules.finish_authority
        ? [
            arrayTable(
              "colors",
              "Colores del fabricante",
              "finish_authority.colors",
              sheet.tabs.rules.finish_authority.colors.map((item) => ({ ...item })),
              [
                { id: "name", label: "Nombre del color" },
                { id: "manufacturer_code", label: "Código del fabricante" },
              ],
              (item, index) => String(item.code ?? `Color ${index + 1}`),
            ),
          ]
        : []),
    ];
  }

  if (tab === "typologies") {
    const limits = sheet.tabs.rules.dimensional_limits ?? [];
    return [
      arrayTable(
        "limits",
        "Tamaños de hoja permitidos",
        "dimensional_limits",
        limits.map((item) => ({ ...item })),
        [
          "min_leaf_width_mm",
          "max_leaf_width_mm",
          "min_leaf_height_mm",
          "max_leaf_height_mm",
          "max_leaf_weight_kg",
        ].map((field) =>
          field === "max_leaf_weight_kg"
            ? {
                ...column("hardware-kits", field),
                precision: 4,
                nullable: true,
                min: "0.0001",
                max: "999999.9999",
              }
            : column("hardware-kits", field),
        ),
        (item, index) => {
          const opening = String(item.opening_type ?? "");
          return domainLabels[opening] ?? `Ventana ${index + 1}`;
        },
      ),
    ];
  }
  return [];
}

/** Array-valued rules remain atomic; several edited cells make one audited write. */
export function bindChanges(table: SheetTable, changes: TableChange[]): CellChangeRequest[] {
  const output = new Map<string, CellChangeRequest>();
  for (const change of changes) {
    const binding = table.bindings[change.rowId]?.[change.columnId];
    if (!binding) throw new Error("Esta celda cambió. Vuelve a cargar la serie antes de editarla.");
    const key = address(binding.cell);
    let value: unknown = change.value;
    if (binding.index !== undefined) {
      const existing = output.get(key)?.value ?? JSON.parse(binding.cell.value ?? "[]");
      const items = structuredClone(existing) as unknown[];
      if (binding.field)
        (items[binding.index] as Record<string, unknown>)[binding.field] = change.value;
      else items[binding.index] = change.value;
      value = items;
    }
    output.set(key, {
      resource: binding.cell.resource,
      row_id: binding.cell.row_id,
      field: binding.cell.field,
      value,
    });
  }
  return [...output.values()];
}

import { t } from "../../i18n/es-CL";

export type GlassPiece = {
  bay_id: string;
  leaf_id?: string | null;
  width_mm: string;
  height_mm: string;
  area_m2?: string;
  weight_kg?: string;
  thickness_net_mm?: string;
  glass_spec?: string | null;
  article_sku?: string | null;
};
export type PolishingEntry = {
  bay_id: string;
  leaf_id?: string | null;
  edges?: { top?: boolean; right?: boolean; bottom?: boolean; left?: boolean };
};

type Group = {
  spec: string;
  sku: string;
  thickness: string;
  pieces: { piece: GlassPiece; edges: string }[];
  qty: number;
  area_m2: number;
  weight_kg: number;
};

function num(value: string | number | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function polishKey(bay: string, leaf: string | null | undefined): string {
  return `${bay}|${leaf ?? "-"}`;
}

function edgeLabel(edges: PolishingEntry["edges"] | undefined): string {
  if (!edges) return "—";
  const parts: string[] = [];
  if (edges.top) parts.push(t("production.glassEdgeTop"));
  if (edges.right) parts.push(t("production.glassEdgeRight"));
  if (edges.bottom) parts.push(t("production.glassEdgeBottom"));
  if (edges.left) parts.push(t("production.glassEdgeLeft"));
  return parts.length ? parts.join("·") : "—";
}

export function glassSummaryCsv(groups: Group[]): string {
  const rows: string[][] = [
    [
      t("production.glassColSpec"),
      t("production.glassColSku"),
      t("production.glassColThickness"),
      t("production.glassColDims"),
      t("production.glassColQty"),
      t("production.glassColArea"),
      t("production.glassColWeight"),
      t("production.glassColPolish"),
    ],
  ];
  for (const group of groups) {
    const perSize = new Map<string, { count: number; edges: string; dims: string }>();
    for (const item of group.pieces) {
      const dims = `${item.piece.width_mm}×${item.piece.height_mm}`;
      const sizeKey = `${dims}|${item.edges}`;
      const entry = perSize.get(sizeKey) ?? { count: 0, edges: item.edges, dims };
      entry.count += 1;
      perSize.set(sizeKey, entry);
    }
    for (const entry of perSize.values()) {
      rows.push([
        group.spec,
        group.sku,
        group.thickness,
        entry.dims,
        String(entry.count),
        entry.count === group.qty ? group.area_m2.toFixed(4) : "",
        entry.count === group.qty ? group.weight_kg.toFixed(2) : "",
        entry.edges,
      ]);
    }
  }
  return rows
    .map((row) =>
      row.map((cell) => (/[",\n]/.test(cell) ? `"${cell.replace(/"/g, '""')}"` : cell)).join(","),
    )
    .join("\n");
}

export function GlassSummary({
  glasses,
  polishing,
  onExport,
}: {
  glasses: GlassPiece[];
  polishing: PolishingEntry[];
  onExport: (groups: Group[]) => void;
}) {
  const polishByKey = new Map(
    polishing.map((entry) => [polishKey(entry.bay_id, entry.leaf_id), entry]),
  );
  const groups = new Map<string, Group>();
  for (const piece of glasses) {
    const spec = piece.glass_spec ?? "—";
    const sku = piece.article_sku ?? "—";
    const thickness = piece.thickness_net_mm ?? "—";
    const key = `${spec}|${sku}|${thickness}`;
    let group = groups.get(key);
    if (!group) {
      group = { spec, sku, thickness, pieces: [], qty: 0, area_m2: 0, weight_kg: 0 };
      groups.set(key, group);
    }
    const entry = polishByKey.get(polishKey(piece.bay_id, piece.leaf_id));
    group.pieces.push({ piece, edges: edgeLabel(entry?.edges) });
    group.qty += 1;
    group.area_m2 += num(piece.area_m2);
    group.weight_kg += num(piece.weight_kg);
  }
  const grouped = [...groups.values()];
  const totalArea = grouped.reduce((sum, group) => sum + group.area_m2, 0);
  const totalQty = grouped.reduce((sum, group) => sum + group.qty, 0);
  const totalWeight = grouped.reduce((sum, group) => sum + group.weight_kg, 0);

  return (
    <section className="production-glass" aria-label={t("production.glassSummaryTitle")}>
      <header className="production-optimize-head">
        <h3>{t("production.glassSummaryTitle")}</h3>
        <button type="button" onClick={() => onExport(grouped)}>
          {t("production.glassExport")}
        </button>
      </header>
      {grouped.length ? (
        <table className="production-plan">
          <thead>
            <tr>
              <th>{t("production.glassColSpec")}</th>
              <th>{t("production.glassColSku")}</th>
              <th>{t("production.glassColThickness")}</th>
              <th>{t("production.glassColDims")}</th>
              <th>{t("production.glassColQty")}</th>
              <th>{t("production.glassColArea")}</th>
              <th>{t("production.glassColWeight")}</th>
              <th>{t("production.glassColPolish")}</th>
            </tr>
          </thead>
          <tbody>
            {grouped.map((group) => {
              const sizes = new Map<string, { count: number; edges: string; dims: string }>();
              for (const item of group.pieces) {
                const dims = `${item.piece.width_mm}×${item.piece.height_mm}`;
                const sizeKey = `${dims}|${item.edges}`;
                const entry = sizes.get(sizeKey) ?? { count: 0, edges: item.edges, dims };
                entry.count += 1;
                sizes.set(sizeKey, entry);
              }
              return [...sizes.values()].map((entry, rowIndex) => (
                <tr key={`${group.spec}-${group.sku}-${entry.dims}-${entry.edges}`}>
                  {rowIndex === 0 ? <td rowSpan={sizes.size}>{group.spec}</td> : null}
                  {rowIndex === 0 ? <td rowSpan={sizes.size}>{group.sku}</td> : null}
                  {rowIndex === 0 ? <td rowSpan={sizes.size}>{group.thickness} mm</td> : null}
                  <td>{entry.dims} mm</td>
                  <td>{entry.count}</td>
                  {rowIndex === 0 ? (
                    <td rowSpan={sizes.size}>{group.area_m2.toFixed(3)} m²</td>
                  ) : null}
                  {rowIndex === 0 ? (
                    <td rowSpan={sizes.size}>{group.weight_kg.toFixed(2)} kg</td>
                  ) : null}
                  <td>{entry.edges}</td>
                </tr>
              ));
            })}
            <tr className="production-glass-total">
              <td colSpan={4}>{t("production.glassTotals")}</td>
              <td>{totalQty}</td>
              <td>{totalArea.toFixed(3)} m²</td>
              <td>{totalWeight.toFixed(2)} kg</td>
              <td />
            </tr>
          </tbody>
        </table>
      ) : (
        <p className="production-optimize-empty">{t("production.glassEmpty")}</p>
      )}
    </section>
  );
}

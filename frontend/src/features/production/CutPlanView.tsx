import { useMemo, useState } from "react";

import { t } from "../../i18n/es-CL";

// Full engine payload contract (backend/production/service.py →
// dekopen_engine.cutting + nesting, model_dump(mode="json") — every
// mm/area/pct value arrives as a decimal string).
export type CutPlacement = {
  piece_id: string;
  source_kind?: "PROFILE" | "REINFORCEMENT";
  workshop_sku?: string;
  material?: string;
  color?: string;
  length_mm: string;
  source_position_id?: string | null;
  bay_id?: string | null;
  leaf_id?: string | null;
  role?: string;
  unit_index?: number;
  angle_left?: string | null;
  angle_right?: string | null;
  sequence?: number;
};
export type CutBar = {
  bar_index: number;
  commercial_sku: string;
  material?: string;
  color?: string;
  stock_length_mm: string;
  head_trim_mm?: string;
  tail_trim_mm?: string;
  kerf_mm?: string;
  cuts: CutPlacement[];
  remainder_mm: string;
  waste_mm?: string;
  yield_pct: string;
  waste_pct?: string;
};
export type PurchaseLine = {
  commercial_sku: string;
  qty_bars: number;
  stock_length_mm: string;
};
export type SheetPurchase = { purchasing_sku: string; qty_sheets: number };
export type NestPlacement = {
  piece_id: string;
  workshop_sku?: string;
  x_mm: string;
  y_mm: string;
  width_mm: string;
  height_mm: string;
  rotated: boolean;
  source_position_id?: string | null;
  bay_id?: string | null;
  leaf_id?: string | null;
  unit_index?: number;
  sequence?: number;
};
export type SheetLayout = {
  sheet_index: number;
  purchasing_sku: string;
  sheet_width_mm: string;
  sheet_height_mm: string;
  yield_pct: string;
  placements: NestPlacement[];
};
export type UnnestedPiece = {
  kind: string;
  group: string;
  width_mm: string;
  height_mm: string;
  quantity: number;
};
export type WorkOrderOptimization = {
  schema?: string;
  color?: string;
  units?: number;
  optimized_at?: string;
  actor_id?: string;
  bars?: { workshop_cut_plan?: CutBar[]; purchase_list?: PurchaseLine[] };
  sheets?: SheetLayout[];
  sheet_purchases?: SheetPurchase[];
  unnested?: UnnestedPiece[];
};

type PieceRef = {
  kind: "cut" | "nest";
  key: string;
  piece: CutPlacement | NestPlacement;
};

function num(value: string | number | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

/** Same member = same source opening + sash/pane + role — cross-highlights
 * every cut/nest belonging to one physical fenestration member. */
function memberKey(piece: CutPlacement | NestPlacement): string {
  const role = (piece as CutPlacement).role ?? "";
  return [piece.source_position_id ?? "-", piece.bay_id ?? "-", piece.leaf_id ?? "-", role].join(
    "|",
  );
}

function materialClass(material: string | undefined, kind?: string): string {
  if (kind === "REINFORCEMENT") return "cutplan-piece-steel";
  switch (material) {
    case "ALUMINIUM":
      return "cutplan-piece-alu";
    case "PVC":
    default:
      return "cutplan-piece-pvc";
  }
}

function CutPlanBarSvg({
  bar,
  selectedMember,
  selectedKey,
  onSelect,
}: {
  bar: CutBar;
  selectedMember: string | null;
  selectedKey: string | null;
  onSelect: (ref: PieceRef) => void;
}) {
  const stock = num(bar.stock_length_mm) || 1;
  const head = num(bar.head_trim_mm);
  const tail = num(bar.tail_trim_mm);
  const kerf = num(bar.kerf_mm);
  const scaled = (mm: number) => (mm / stock) * 1000;
  const barH = 56;
  let cursor = head;
  const pieces = bar.cuts.map((cut, index) => {
    const x = cursor;
    const w = num(cut.length_mm);
    cursor += w + kerf;
    const key = `b${bar.bar_index}-c${index}`;
    const keyOfPiece = memberKey(cut);
    const selected = selectedKey === key;
    const memberHit = selectedMember !== null && keyOfPiece === selectedMember;
    const xSc = scaled(x);
    const wSc = scaled(w);
    const mid = xSc + wSc / 2;
    const angleL = cut.angle_left != null && num(cut.angle_left) !== 90;
    const angleR = cut.angle_right != null && num(cut.angle_right) !== 90;
    return (
      <g
        key={key}
        className={`cutplan-cut ${materialClass(cut.material, cut.source_kind)}${
          memberHit ? " is-member" : ""
        }${selected ? " is-selected" : ""}`}
        onClick={() => onSelect({ kind: "cut", key, piece: cut })}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect({ kind: "cut", key, piece: cut });
          }
        }}
      >
        <rect x={xSc} y={8} width={Math.max(wSc, 1)} height={barH - 16} rx={2} />
        {wSc > 52 ? (
          <text x={mid} y={30} textAnchor="middle" className="cutplan-cut-id">
            {cut.piece_id}
          </text>
        ) : null}
        {wSc > 40 ? (
          <text x={mid} y={46} textAnchor="middle" className="cutplan-cut-len">
            {cut.length_mm}
          </text>
        ) : null}
        {angleL ? (
          <text x={xSc + 4} y={30} className="cutplan-miter-mark" aria-hidden>
            ◧
          </text>
        ) : null}
        {angleR ? (
          <text
            x={xSc + wSc - 4}
            y={30}
            textAnchor="end"
            className="cutplan-miter-mark"
            aria-hidden
          >
            ◨
          </text>
        ) : null}
      </g>
    );
  });
  // The engine charges kerf after every cut (process_consumed_mm) — the
  // trailing kerf is part of the consumed span, so the drawn remainder
  // matches the sealed remainder_mm.
  const usedEnd = cursor;
  const remainder = Math.max(stock - tail - usedEnd, 0);
  return (
    <svg
      className="cutplan-bar"
      viewBox={`0 0 1000 ${barH}`}
      role="group"
      aria-label={`${t("production.optimizeBar")} #${bar.bar_index}`}
    >
      <rect
        className="cutplan-frame"
        x={0}
        y={8}
        width={1000}
        height={barH - 16}
        rx={2}
        pointerEvents="none"
      />
      {head > 0 ? (
        <rect
          className="cutplan-trim"
          x={0}
          y={8}
          width={Math.max(scaled(head), 1.5)}
          height={barH - 16}
        />
      ) : null}
      {pieces}
      {remainder > 0 ? (
        <rect
          className="cutplan-remainder"
          x={scaled(usedEnd)}
          y={8}
          width={Math.max(scaled(remainder), 1)}
          height={barH - 16}
        />
      ) : null}
      {tail > 0 ? (
        <rect
          className="cutplan-trim"
          x={scaled(stock - tail)}
          y={8}
          width={Math.max(scaled(tail), 1.5)}
          height={barH - 16}
        />
      ) : null}
    </svg>
  );
}

function CutPlanSheetSvg({
  layout,
  selectedMember,
  selectedKey,
  onSelect,
}: {
  layout: SheetLayout;
  selectedMember: string | null;
  selectedKey: string | null;
  onSelect: (ref: PieceRef) => void;
}) {
  const w = num(layout.sheet_width_mm) || 1;
  const h = num(layout.sheet_height_mm) || 1;
  const vw = 320;
  const vh = Math.max(Math.round((h / w) * vw), 60);
  return (
    <svg
      className="cutplan-sheet"
      viewBox={`0 0 ${vw} ${vh}`}
      role="group"
      aria-label={`${t("production.optimizeSheet")} #${layout.sheet_index}`}
    >
      <rect className="cutplan-sheet-frame" x={0} y={0} width={vw} height={vh} rx={2} />
      {layout.placements.map((piece, index) => {
        const key = `s${layout.sheet_index}-p${index}`;
        const memberHit = selectedMember !== null && memberKey(piece) === selectedMember;
        const selected = selectedKey === key;
        const px = (num(piece.x_mm) / w) * vw;
        const py = (num(piece.y_mm) / h) * vh;
        const pw = Math.max((num(piece.width_mm) / w) * vw, 1);
        const ph = Math.max((num(piece.height_mm) / h) * vh, 1);
        return (
          <g
            key={key}
            className={`cutplan-nest${memberHit ? " is-member" : ""}${
              selected ? " is-selected" : ""
            }`}
            onClick={() => onSelect({ kind: "nest", key, piece })}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect({ kind: "nest", key, piece });
              }
            }}
          >
            <rect x={px} y={py} width={pw} height={ph} rx={1} />
            {pw > 30 && ph > 12 ? (
              <text x={px + pw / 2} y={py + ph / 2} textAnchor="middle" dominantBaseline="middle">
                {piece.piece_id}
                {piece.rotated ? " ⟳" : ""}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

function shortId(value: string | null | undefined): string {
  return value ? value.slice(0, 8) : "—";
}

export function CutPlanView({ optimization }: { optimization: WorkOrderOptimization }) {
  const [selected, setSelected] = useState<PieceRef | null>(null);
  const bars = optimization.bars?.workshop_cut_plan ?? [];
  const sheets = optimization.sheets ?? [];
  const selectedMember = selected ? memberKey(selected.piece) : null;

  const detail = useMemo(() => {
    if (!selected) return null;
    const piece = selected.piece;
    const isCut = selected.kind === "cut";
    const cut = piece as CutPlacement;
    const nest = piece as NestPlacement;
    const angles =
      isCut && (cut.angle_left != null || cut.angle_right != null)
        ? `${cut.angle_left ?? "90"}° / ${cut.angle_right ?? "90"}°`
        : null;
    return {
      id: piece.piece_id,
      kind: selected.kind,
      sku: piece.workshop_sku ?? "—",
      material: cut.material ?? "—",
      color: cut.color ?? "—",
      role: cut.role ?? "—",
      position: shortId(piece.source_position_id),
      bay: shortId(piece.bay_id),
      leaf: shortId(piece.leaf_id),
      unit: piece.unit_index ?? 1,
      measure: isCut
        ? `${cut.length_mm} mm`
        : `${nest.width_mm}×${nest.height_mm} mm${nest.rotated ? ` (${t("production.optimizeRotated")})` : ""}`,
      angles,
      memberCount: 0,
    };
  }, [selected]);

  if (detail && selected) {
    // Count every placement sharing this member across bars + sheets.
    let count = 0;
    for (const bar of bars) {
      for (const cut of bar.cuts) {
        if (memberKey(cut) === selectedMember) count += 1;
      }
    }
    for (const sheet of sheets) {
      for (const piece of sheet.placements) {
        if (memberKey(piece) === selectedMember) count += 1;
      }
    }
    detail.memberCount = count;
  }

  return (
    <div className="cutplan">
      <div className="cutplan-canvas">
        {bars.map((bar) => (
          <figure key={bar.bar_index} className="cutplan-bar-row">
            <figcaption>
              <strong>
                {t("production.optimizeBar")} #{bar.bar_index}
              </strong>{" "}
              {bar.commercial_sku} · {bar.stock_length_mm} mm · {t("production.cutplanYield")}{" "}
              {bar.yield_pct}% · {t("production.cutplanRemainder")} {bar.remainder_mm} mm
            </figcaption>
            <CutPlanBarSvg
              bar={bar}
              selectedMember={selectedMember}
              selectedKey={selected?.key ?? null}
              onSelect={setSelected}
            />
          </figure>
        ))}
        {sheets.length ? (
          <div className="cutplan-sheets">
            {sheets.map((layout) => (
              <figure key={layout.sheet_index} className="cutplan-sheet-card">
                <figcaption>
                  <strong>
                    {t("production.optimizeSheet")} #{layout.sheet_index}
                  </strong>{" "}
                  {layout.purchasing_sku} · {layout.sheet_width_mm}×{layout.sheet_height_mm} mm ·{" "}
                  {t("production.cutplanYield")} {layout.yield_pct}%
                </figcaption>
                <CutPlanSheetSvg
                  layout={layout}
                  selectedMember={selectedMember}
                  selectedKey={selected?.key ?? null}
                  onSelect={setSelected}
                />
              </figure>
            ))}
          </div>
        ) : null}
      </div>
      <aside className="cutplan-detail" aria-label={t("production.cutplanDetail")}>
        {detail ? (
          <dl>
            <div>
              <dt>{t("production.cutplanPiece")}</dt>
              <dd>{detail.id}</dd>
            </div>
            <div>
              <dt>{t("production.cutplanRole")}</dt>
              <dd>{detail.role}</dd>
            </div>
            <div>
              <dt>{t("production.cutplanMeasure")}</dt>
              <dd>{detail.measure}</dd>
            </div>
            {detail.angles ? (
              <div>
                <dt>{t("production.cutplanAngles")}</dt>
                <dd>{detail.angles}</dd>
              </div>
            ) : null}
            <div>
              <dt>{t("production.cutplanMaterial")}</dt>
              <dd>
                {detail.material}
                {detail.color !== "—" ? ` · ${detail.color}` : ""}
              </dd>
            </div>
            <div>
              <dt>{t("production.optimizeSku")}</dt>
              <dd>{detail.sku}</dd>
            </div>
            <div>
              <dt>{t("production.cutplanOrigin")}</dt>
              <dd>
                {t("production.cutplanPosition")} {detail.position} · {t("production.cutplanBay")}{" "}
                {detail.bay} · {t("production.cutplanLeaf")} {detail.leaf} · u{detail.unit}
              </dd>
            </div>
            <div>
              <dt>{t("production.cutplanMemberCuts")}</dt>
              <dd>{detail.memberCount}</dd>
            </div>
          </dl>
        ) : (
          <p className="cutplan-detail-empty">{t("production.cutplanDetailHint")}</p>
        )}
      </aside>
    </div>
  );
}

import { useMemo, useState, type ReactNode } from "react";
import type { PositionResponse } from "../../api/generated/models";
import { fmtMm } from "../../format";
import { findNode } from "../canvas/intentEditing";
import { designProduct, PositionThumb, type DrawingSelection } from "./PositionThumb";
import { ProjectBom } from "./ProjectPositionEditor";

/** Links use the engine's module|bay identities. A missing destination stays
 * unassigned; matching by SKU or row order would select unrelated pieces. */
export function PositionMaterials({
  position,
  orgId,
  drawingDetails,
  children,
}: {
  position: PositionResponse;
  orgId: string;
  drawingDetails?: ReactNode;
  children?: ReactNode;
}): JSX.Element {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [selection, setSelection] = useState<DrawingSelection | null>(null);
  const product = useMemo(() => designProduct(position.design), [position.design]);
  const rows = useMemo(
    () => [
      ...position.bom.profile_cuts.map((item, i) => ({
        key: `profile:${i}`,
        bayId: item.bay_id,
        label: item.sku,
      })),
      ...position.bom.glasses.map((item, i) => ({
        key: `glass:${i}`,
        bayId: item.bay_id,
        label: item.glass_spec || item.article_sku || `Vidrio ${i + 1}`,
      })),
      ...position.bom.hardware_items.map((item, i) => ({
        key: `hardware:${i}`,
        bayId: item.bay_id,
        label: item.name,
      })),
      ...(position.bom.fittings ?? []).map((item, i) => ({
        key: `fitting:${i}`,
        bayId: item.bay_id,
        label: item.sku,
      })),
      ...position.bom.reinforcements.map((item, i) => ({
        key: `reinforcement:${i}`,
        bayId: item.bay_id,
        label: item.reinforcement_sku || item.parent_profile_sku,
      })),
      ...position.bom.panels.map((item, i) => ({
        key: `panel:${i}`,
        bayId: item.bay_id,
        label: item.name,
      })),
    ],
    [position.bom],
  );
  function destination(reference: string | null): DrawingSelection | null {
    if (!reference) return null;
    const module =
      product.assembly.modules.find((item) => reference.startsWith(item.id + "|")) ??
      (product.assembly.modules.length === 1 ? product.assembly.modules[0] : undefined);
    if (!module) return null;
    const nodeId = reference.startsWith(module.id + "|")
      ? reference.slice(module.id.length + 1)
      : reference;
    const node = findNode(module.tree, nodeId);
    if (!node) return null;
    return {
      moduleId: module.id,
      nodeId,
      kind: node.type === "BAY" ? "bay" : node.type === "ROOT" ? "module" : "division",
    };
  }
  const highlighted = new Set(
    rows
      .filter((row) => {
        if (selectedKey) return row.key === selectedKey;
        const target = destination(row.bayId);
        return (
          !!selection &&
          !!target &&
          selection.moduleId === target.moduleId &&
          (selection.kind === "module" || selection.nodeId === target.nodeId)
        );
      })
      .map((row) => row.key),
  );
  const selected = rows.find((row) => row.key === selectedKey);
  return (
    <div className="project-material-workspace">
      <div className="project-material-drawing">
        <PositionThumb
          design={position.design}
          orgId={orgId}
          systemId={position.design.system_id}
          finish={position.bom.finish}
          cuts={position.bom.profile_cuts}
          selection={selection}
          onSelectPart={(target) => {
            setSelectedKey(null);
            setSelection(target);
          }}
        />
        <p className="project-number">
          {fmtMm(position.design.nominal_width_mm)} × {fmtMm(position.design.nominal_height_mm)} mm
          · {position.quantity} ud.
        </p>
        <p>Materiales por unidad. Toca un paño o un perfil para localizar sus piezas.</p>
        <div className="project-material-selection" role="status">
          {selected ? (
            <>
              <strong>{selected.label}</strong>
              <span>
                {selection
                  ? "Zona asociada resaltada en el dibujo."
                  : "Esta pieza no tiene un destino individual asociado al dibujo."}
              </span>
            </>
          ) : selection ? (
            `${highlighted.size} materiales asociados a la selección.`
          ) : (
            "Vista interior · cálculo guardado del motor."
          )}
          {(selectedKey || selection) && (
            <button
              type="button"
              onClick={() => {
                setSelectedKey(null);
                setSelection(null);
              }}
            >
              Quitar selección
            </button>
          )}
        </div>
        {drawingDetails}
      </div>
      <div className="project-material-details">
        <ProjectBom
          result={position.bom}
          expanded
          highlighted={highlighted}
          onSelectMaterial={(key) => {
            setSelectedKey(key);
            setSelection(destination(rows.find((row) => row.key === key)?.bayId ?? null));
          }}
        />
        {children}
      </div>
    </div>
  );
}

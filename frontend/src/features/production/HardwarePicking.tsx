import { useState } from "react";
import { LoadingState } from "../../ui/States";
import { useQuery } from "@tanstack/react-query";
import { productionVersionHardwarePicking } from "../../api/generated/dekopen";
import type { HardwarePickingRow, HardwareMachiningGap } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { fmtMm } from "../../format";

function PickingRows({ rows }: { rows: HardwarePickingRow[] }): JSX.Element {
  if (!rows.length)
    return <p>Esta orden no tiene componentes de herraje declarados en su BOM sellado.</p>;
  return (
    <ul className="production-hardware-rows">
      {rows.map((row, index) => (
        <li key={`${row.sku}:${row.cut_length_mm}:${index}`}>
          <div>
            <strong>{row.name}</strong>
            <span className="production-hardware-quantity">
              {fmtMm(row.quantity)} {row.unit}
              {row.cut_length_mm !== null ? ` · corte a ${fmtMm(row.cut_length_mm)} mm` : ""}
            </span>
          </div>
          <details>
            <summary>Destino y fuente</summary>
            <p>{row.targets.join(" · ")}</p>
            <p>
              {row.source ??
                "Contenido histórico de catálogo. Solicita la fuente técnica antes de mecanizar."}
            </p>
            <details>
              <summary>Detalles técnicos</summary>
              <code>{row.sku}</code>
            </details>
          </details>
        </li>
      ))}
    </ul>
  );
}

export function HardwarePicking({
  rows,
  gaps,
  versionId,
  organizationId,
}: {
  rows: HardwarePickingRow[];
  gaps: HardwareMachiningGap[];
  versionId: string | null;
  organizationId: string;
}): JSX.Element {
  const [revision, setRevision] = useState(false);
  const consolidated = useQuery({
    queryKey: ["hardware-picking", organizationId, versionId],
    queryFn: async () => {
      const result = await productionVersionHardwarePicking(versionId!, {
        headers: { "X-Organization-ID": organizationId },
      });
      if (result.status !== 200) throw new Error("hardware_picking_unavailable");
      return result.data.rows;
    },
    enabled: revision && versionId !== null,
    retry: false,
    staleTime: Infinity,
  });
  return (
    <section className="production-hardware" aria-label="Picking de herrajes">
      <h3>Picking de herrajes</h3>
      <p>Cantidades y largos del BOM de esta orden. La revisión emitida conserva su catálogo.</p>
      <PickingRows rows={rows} />
      {gaps.length > 0 && (
        <details className="production-hardware-gaps">
          <summary>{gaps.length} mecanizados declarados no emitidos</summary>
          <ul>
            {gaps.map((gap, index) => (
              <li key={index}>
                <strong>
                  {gap.component_name} · {gap.declaration}
                </strong>
                <p>
                  {gap.detail} Completa la fuente del catálogo y emite una nueva revisión antes de
                  generar el programa.
                </p>
                <p>{gap.source}</p>
              </li>
            ))}
          </ul>
        </details>
      )}
      {versionId && (
        <details open={revision} onToggle={(event) => setRevision(event.currentTarget.open)}>
          <summary>Picking consolidado de la revisión</summary>
          {revision &&
            (consolidated.isPending ? (
              <LoadingState label="Cargando componentes sellados" />
            ) : consolidated.isError ? (
              <>
                <p role="alert">
                  {consolidated.error instanceof ApiError && consolidated.error.status === 403
                    ? "Tu rol no permite leer esta revisión. Solicita acceso al jefe de taller."
                    : "No se pudo leer la revisión. Vuelve a cargar sus componentes."}
                </p>
                <button type="button" onClick={() => void consolidated.refetch()}>
                  Volver a cargar
                </button>
              </>
            ) : (
              <PickingRows rows={consolidated.data ?? []} />
            ))}
        </details>
      )}
    </section>
  );
}

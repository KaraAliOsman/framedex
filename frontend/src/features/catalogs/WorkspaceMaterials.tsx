import { useEffect, useState } from "react";
import { inventorySheetFormats, pricingAdminList } from "../../api/generated/dekopen";
import type { SheetFormatList, WorkspaceGlass } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { fmtMm } from "../../format";
import { DemoBadge, DimLoader } from "../../ui";

export function WorkspaceGlasses({ glasses = [] }: { glasses?: WorkspaceGlass[] }) {
  const [formats, setFormats] = useState<SheetFormatList | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    void inventorySheetFormats({ signal: controller.signal })
      .then((response) => {
        if (response.status === 200 && !controller.signal.aborted) setFormats(response.data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("No se pudieron cargar los formatos de lámina.");
      });
    return () => controller.abort();
  }, [reload]);
  return (
    <section className="ws-section">
      <header className="ws-section-head">
        <h3>Vidrios y termopaneles</h3>
        <a href="/catalogs/sheet-formats">Declarar o consultar formatos de lámina</a>
      </header>
      {!glasses.length ? (
        <p>
          Sin composiciones declaradas. Importa la ficha del proveedor para revisar su composición y
          fuente.
        </p>
      ) : (
        <div className="ws-glass-list">
          {glasses.map((glass) => (
            <article key={glass.mapping_id}>
              <h4>
                {glass.name} {glass.synthetic ? <DemoBadge /> : null}
              </h4>
              <p className="mono">{glass.notation ?? "Composición: Sin dato"}</p>
              <p>Fuente: {glass.source ?? "Sin dato; revisa la ficha del proveedor"}</p>
              {error ? null : !formats ? (
                <DimLoader label="Cargando formatos…" />
              ) : (
                <ul>
                  {formats.items
                    .filter((item) => item.technical_sku === glass.technical_sku)
                    .map((item) => (
                      <li key={item.id}>
                        {fmtMm(item.width_mm)} × {fmtMm(item.height_mm)} mm · despunte{" "}
                        {fmtMm(item.edge_trim_mm)} mm · {item.supplier ?? "Proveedor: Sin dato"}
                        <p>
                          {item.source ?? "Fuente: Sin dato"}
                          {item.is_demo ? <DemoBadge /> : null}
                        </p>
                      </li>
                    ))}
                  {!formats.items.some((item) => item.technical_sku === glass.technical_sku) ? (
                    <li>
                      Formato de lámina: Sin dato. Decláralo con la fuente del proveedor antes de
                      optimizar.
                    </li>
                  ) : null}
                </ul>
              )}
            </article>
          ))}
        </div>
      )}
      {error ? (
        <>
          <p role="alert">{error}</p>
          <button type="button" onClick={() => setReload((value) => value + 1)}>
            Reintentar formatos
          </button>
        </>
      ) : null}
    </section>
  );
}

type Coverage = {
  sku: string;
  name: string;
  active_cost_items: number;
  is_demo?: boolean;
  blocker?: string | null;
};
export function WorkspaceCosts() {
  const { me } = useAuthSession();
  const allowed = me?.active_organization?.role === "OWNER";
  const [data, setData] = useState<Coverage[] | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    if (!allowed) return;
    const controller = new AbortController();
    setError("");
    void pricingAdminList("coverage", { signal: controller.signal })
      .then((response) => {
        if (response.status === 200 && !controller.signal.aborted)
          setData((response.data as { items: Coverage[] }).items);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("No se pudo cargar la cobertura de costos vigente.");
      });
    return () => controller.abort();
  }, [allowed, reload]);
  return (
    <section className="ws-section">
      <h3>Cobertura de costos</h3>
      {!allowed ? (
        <p role="status">
          La cobertura y las listas de costo requieren acceso del dueño. Puedes consultar las
          referencias técnicas de suministro de esta serie.
        </p>
      ) : (
        <>
          <p>
            Las referencias de suministro se revisan en esta serie. La cobertura comercial usa las
            listas vigentes de la organización y la unidad real de compra.
          </p>
          <a href="/pricing/cost-lists?section=coverage">Abrir costos y resolver faltantes</a>
          {error ? (
            <>
              <p role="alert">{error}</p>
              <button type="button" onClick={() => setReload((value) => value + 1)}>
                Reintentar cobertura
              </button>
            </>
          ) : data === null ? (
            <DimLoader label="Cargando cobertura de costos…" />
          ) : data.length === 0 ? (
            <p>No hay materiales con costos registrados.</p>
          ) : (
            <details>
              <summary>Ver cobertura comercial de la organización</summary>
              <ul>
                {data.map((item, index) => (
                  <li key={`${item.sku}-${index}`}>
                    <strong>{item.name}</strong> {item.is_demo ? <DemoBadge /> : null} ·{" "}
                    {item.blocker ??
                      (item.active_cost_items > 0 ? "Costo vigente declarado" : "Sin dato")}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}

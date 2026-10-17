import type { FinishAuthority } from "../../api/generated/models";
import { finishColorCss } from "../canvas/finishColors";
import { VisualSampleControl } from "./VisualSampleControl";
import { useCatalogVisuals } from "./catalogVisuals";

export function CatalogFinishSamples({
  authority,
  systemId,
  organizationId,
  canEdit,
}: {
  authority?: FinishAuthority | null;
  systemId: string;
  organizationId: string;
  canEdit: boolean;
}) {
  const samples = useCatalogVisuals(systemId, organizationId);
  return (
    <section className="catalog-finish-samples" aria-label="Muestras de acabados">
      <header>
        <h3>El material, a la vista</h3>
        <p>
          Usa la carta de la serie o añade una foto de tu muestra. Una foto de frente, sin fondo ni
          reflejos, funciona mejor.
        </p>
      </header>
      {samples.isError ? (
        <p role="status">
          No se pudieron cargar las fotos.{" "}
          <button type="button" onClick={() => void samples.refetch()}>
            Reintentar
          </button>
        </p>
      ) : null}
      {!authority?.colors.length ? (
        <p>
          Esta serie todavía no tiene carta de acabados. Añádela en los datos de la serie para
          asociar tus muestras.
        </p>
      ) : (
        <div className="catalog-finish-grid">
          {authority.colors.map((color) => {
            const sample = samples.data?.find(
              (entry) => entry.kind === "TEXTURE" && entry.target_key === color.code,
            );
            const url = (!sample?.cleared && sample?.image_url) || color.texture_path;
            return (
              <article className="catalog-finish-card" key={color.code}>
                <div
                  className={`catalog-finish-material${!url && ["FOIL", "WOOD_EFFECT"].includes(color.kind) ? " finish-swatch--illustrative" : ""}`}
                  style={{
                    backgroundColor: finishColorCss(color),
                    backgroundImage: url ? `url(${url})` : undefined,
                  }}
                />
                <div>
                  <h4>{color.name}</h4>
                  <p>
                    {sample && !sample.cleared
                      ? "Foto de tu muestra"
                      : color.texture_path
                        ? "Muestra de la carta"
                        : "Representación de color"}
                  </p>
                  <small>{color.manufacturer_code}</small>
                </div>
                {canEdit ? (
                  <VisualSampleControl
                    organizationId={organizationId}
                    systemId={systemId}
                    kind="TEXTURE"
                    targetKey={color.code}
                    label={color.name}
                    sample={sample}
                  />
                ) : null}
              </article>
            );
          })}
        </div>
      )}
      <p className="catalog-sample-note">
        Las fotos se usan en el muestrario y en la vista de diseño 2D y 3D. Comprueba el material
        con la muestra física antes de fabricar.
      </p>
    </section>
  );
}

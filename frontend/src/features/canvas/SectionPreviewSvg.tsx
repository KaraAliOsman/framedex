import type { ProfileSection } from "../../api/generated/models";
import { fmtMm } from "../../format";
import { t } from "../../i18n/es-CL";
import { memberSurface } from "./materials";
import { ProfileIllustration } from "../catalogs/ProfileIllustration";
import { useProfileSample } from "../catalogs/catalogVisuals";
import "./SectionPreviewSvg.css";

/** Declared sections retain scale. Family illustrations and sample photos have no measurement authority. */

const PAD_MM = 10;
const AXIS_LABELS: Record<string, string> = {
  GLAZING: "Vidrio",
  WEB: "Alma",
  FIXING: "Fijación",
};

function polygonBounds(section: ProfileSection) {
  const xs = section.polygon.map((point) => Number(point.x_mm));
  const ys = section.polygon.map((point) => Number(point.y_mm));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return {
    minX,
    minY,
    width: Math.max(maxX - minX, 1),
    height: Math.max(maxY - minY, 1),
  };
}

export function SectionPreviewSvg({
  section,
  faceWidthMm,
  depthMm,
  material,
  profileRole,
  profileSku,
  sampleUrl,
  recognition = false,
}: {
  section: ProfileSection | null | undefined;
  faceWidthMm: number;
  depthMm?: number;
  material?: string;
  profileRole?: string;
  profileSku?: string | null;
  sampleUrl?: string | null;
  recognition?: boolean;
}) {
  const sample = useProfileSample(profileSku);
  const photo = sampleUrl ?? sample?.image_url;
  const declared = section?.polygon?.length ? section : null;
  if (recognition) {
    return (
      <div className="section-preview section-preview--recognition">
        <figure className="section-preview__recognition">
          {photo ? (
            <img
              className="section-preview__photo"
              src={photo}
              alt="Foto de referencia del perfil"
            />
          ) : (
            <ProfileIllustration role={profileRole} material={material} depthMm={depthMm} />
          )}
          <figcaption>{photo ? "Foto de referencia" : "Ilustración de familia"}</figcaption>
        </figure>
        {declared ? (
          <details className="section-preview__detail">
            <summary>Ver sección declarada</summary>
            <SectionPreviewSvg
              section={declared}
              faceWidthMm={faceWidthMm}
              depthMm={depthMm}
              material={material}
            />
          </details>
        ) : (
          <span className="section-preview__pending">Sección por confirmar</span>
        )}
      </div>
    );
  }
  const widthMm = declared ? polygonBounds(declared).width : Math.max(faceWidthMm, 1);
  const heightMm = declared ? polygonBounds(declared).height : Math.max(depthMm ?? faceWidthMm, 1);
  const bounds = declared
    ? polygonBounds(declared)
    : { minX: 0, minY: 0, width: widthMm, height: heightMm };
  const viewX = bounds.minX - PAD_MM;
  const viewY = bounds.minY - PAD_MM;
  const viewW = widthMm + PAD_MM * 2;
  const viewH = heightMm + PAD_MM * 2;
  const surface = memberSurface(material ?? "PVC");
  const provenance = declared
    ? declared.source === "DXF_REFERENCE"
      ? t("assembly.sectionExact")
      : t("assembly.sectionDeclared")
    : t("assembly.sectionApproximate");

  return (
    <figure
      className="section-preview"
      data-provenance={declared ? declared.source : "APPROXIMATE"}
    >
      {photo ? (
        <img className="section-preview__photo" src={photo} alt="Foto de referencia del perfil" />
      ) : null}
      {!declared ? (
        !photo ? (
          <ProfileIllustration role={profileRole} material={material} depthMm={depthMm} />
        ) : null
      ) : (
        <svg
          viewBox={`${viewX} ${viewY} ${viewW} ${viewH}`}
          role="img"
          aria-label={`${t("assembly.sectionTitle")} · ${provenance}`}
        >
          <polygon
            className="section-preview__shape"
            style={{ fill: surface.fill, stroke: surface.edge }}
            points={declared.polygon
              .map((point) => `${Number(point.x_mm)},${Number(point.y_mm)}`)
              .join(" ")}
          />
          {(declared?.axes ?? []).map((axis) => (
            <g key={axis.name}>
              <line
                className="section-preview__axis"
                x1={bounds.minX}
                y1={Number(axis.y_mm)}
                x2={bounds.minX + widthMm}
                y2={Number(axis.y_mm)}
              />
            </g>
          ))}
        </svg>
      )}
      <figcaption>
        {declared ? (
          <span className="section-preview__dims">{`${fmtMm(widthMm)} × ${fmtMm(heightMm)} mm`}</span>
        ) : null}
        <span>
          {declared
            ? provenance
            : photo
              ? "Foto de referencia · sección por confirmar"
              : "Ilustración de familia · sección por confirmar"}
        </span>
        {declared?.axes?.length ? (
          <dl className="section-preview__axes" aria-label="Ejes de la sección">
            {declared.axes.map((axis) => (
              <div key={axis.name}>
                <dt>{AXIS_LABELS[axis.name.toUpperCase()] ?? "Eje declarado"}</dt>
                <dd>{fmtMm(axis.y_mm)} mm</dd>
              </div>
            ))}
          </dl>
        ) : null}
      </figcaption>
    </figure>
  );
}

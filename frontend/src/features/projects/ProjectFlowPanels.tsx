import { useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  documentaryListArtifacts,
  documentaryArtifactAccess,
  productionOrders,
} from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import type { ProjectResponse } from "../../api/generated/models";
import { formatDateTime, formatRevision } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { Loading, StatusBadge } from "../../ui";
import { ProjectPrices } from "../pricing/ProjectPrices";
import { usePricingRequest } from "../pricing/PricingPage";
import { actionErrorDetail } from "../errors";
import type { FactsSection } from "./ProjectPages";
import { ProjectMaterials } from "./ProjectMaterials";

function ProjectPricePanel({
  project,
  orgId,
  isOwner,
  onChanged,
}: {
  project: ProjectResponse;
  orgId: string;
  isOwner: boolean;
  onChanged(): Promise<unknown>;
}): JSX.Element {
  const request = usePricingRequest(orgId);
  const changed = useRef(onChanged);
  changed.current = onChanged;
  const updatedRequest = useCallback(
    async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
      const response = await request<T>(path, method, body);
      if (method !== "GET") await changed.current();
      return response;
    },
    [request],
  );
  return (
    <section className="pricing-page">
      <h2>Precio del proyecto</h2>
      <ProjectPrices request={updatedRequest} owner={isOwner} projectId={project.id} />
    </section>
  );
}
function ProjectProductionPanel({
  project,
  orgId,
}: {
  project: ProjectResponse;
  orgId: string;
}): JSX.Element {
  const query = useQuery({
    queryKey: ["project-production", orgId, project.id],
    queryFn: async () => {
      const response = await productionOrders(
        { project_id: project.id },
        { headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      const versions = new Set(project.versions?.map((version) => version.id));
      return response.data.orders.filter(
        (order) => order.project_version_id && versions.has(order.project_version_id),
      );
    },
  });
  return (
    <div className="project-production">
      {query.isPending ? (
        <Loading label="Cargando órdenes de trabajo" />
      ) : query.isError ? (
        <p role="alert">
          No se pudieron cargar las OT. Revisa la conexión.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      ) : query.data.length === 0 ? (
        <p>
          Aún no hay órdenes liberadas. Se liberan en Producción cuando la cotización está aprobada
          y completa para taller.
        </p>
      ) : (
        <ul className="project-production-list">
          {query.data.map((order) => (
            <li key={order.id}>
              <Link to={`/production?order=${encodeURIComponent(order.id)}`}>
                {order.order_code}
              </Link>
              <StatusBadge>{domainLabel(order.status)}</StatusBadge>
              <span className="project-number">
                {order.steps_done} de {order.steps_total} estaciones completadas
              </span>
              {order.shortage > 0 && (
                <span>
                  Bloqueada · faltan materiales.{" "}
                  <Link to={`/purchasing?project=${encodeURIComponent(project.id)}`}>
                    Revisar compras
                  </Link>
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
// Mirrors backend/documents/renderers.py titles.
const names: Record<string, string> = {
  "DOC-01": "Cotización",
  "DOC-02": "Pedido de vidrios",
  "DOC-03": "Orden de trabajo",
  "DOC-04": "Pedido de perfiles",
  "DOC-05": "Orden de corte",
  "DOC-06": "Control final",
  "DOC-07": "Informe de costos",
  "DOC-08": "Orden de compra",
};
const layouts: Record<string, string> = {
  ESENCIAL: "Esencial",
  PROYECTO: "Proyecto",
  ALTERNATIVAS: "Alternativas",
  PLANO: "plano técnico",
  COMPACTA: "lista compacta",
  VENTANA: "por ventana",
  OBRA: "pedido por obra",
};
function ProjectDocumentPanel({
  project,
  orgId,
  onCompare,
}: {
  project: ProjectResponse;
  orgId: string;
  onCompare(): void;
}): JSX.Element {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const query = useQuery({
    queryKey: ["project-artifacts", orgId, project.id],
    queryFn: async () => {
      const response = await documentaryListArtifacts(project.id, {
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data.artifacts;
    },
  });
  async function open(id: string): Promise<void> {
    setError("");
    setBusy(id);
    const popup = window.open("about:blank", "_blank");
    try {
      const response = await documentaryArtifactAccess(id, {
        headers: { "X-Organization-ID": orgId },
      });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (popup) {
        popup.opener = null;
        popup.location.href = response.data.signed_url;
      } else
        throw new Error(
          "El navegador bloqueó la ventana. Habilita las ventanas de este sitio y vuelve a abrir el documento.",
        );
    } catch (cause) {
      popup?.close();
      setError(
        actionErrorDetail(
          cause,
          "No se pudo abrir el documento. Habilita las ventanas de este sitio y vuelve a intentar.",
        ),
      );
    } finally {
      setBusy("");
    }
  }
  return (
    <section>
      <h2>Documentos por revisión</h2>
      <button onClick={onCompare}>Comparar revisiones</button>
      {error && <p role="alert">{error}</p>}
      {query.isPending ? (
        <Loading label="Cargando documentos de la obra" />
      ) : query.isError ? (
        <p role="alert">
          No se pudieron cargar los documentos.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      ) : query.data.length === 0 ? (
        <p>
          Sin archivos generados. Prepara y emite la cotización para obtener el PDF sellado; los
          documentos de origen están en Importar documento o plano.
        </p>
      ) : (
        <ul className="project-document-list">
          {[...query.data]
            .sort((a, b) => b.created_at.localeCompare(a.created_at))
            .map((artifact) => (
              <li key={artifact.id}>
                <strong>
                  {names[artifact.document_type] ?? "Documento técnico"}
                  {artifact.layout && layouts[artifact.layout]
                    ? ` · ${layouts[artifact.layout]}`
                    : ""}{" "}
                  · {formatRevision(artifact.revision_code)} · {artifact.format}
                </strong>
                <time dateTime={artifact.created_at}>{formatDateTime(artifact.created_at)}</time>
                {artifact.revision_code !== project.current_revision ? (
                  <StatusBadge>Histórico · revisión anterior</StatusBadge>
                ) : null}
                <button disabled={Boolean(busy)} onClick={() => void open(artifact.id)}>
                  {busy === artifact.id ? "Abriendo documento…" : "Abrir documento sellado"}
                </button>
              </li>
            ))}
        </ul>
      )}
    </section>
  );
}
export function ProjectFlowPanels({
  project,
  orgId,
  section,
  isOwner,
  onChanged,
  onCompare,
}: {
  project: ProjectResponse;
  orgId: string;
  section: FactsSection | null;
  isOwner: boolean;
  onChanged(): Promise<unknown>;
  onCompare(): void;
}): JSX.Element | null {
  if (section === "pricing")
    return (
      <ProjectPricePanel project={project} orgId={orgId} isOwner={isOwner} onChanged={onChanged} />
    );
  if (section === "production")
    return (
      <ProjectMaterials
        project={project}
        orgId={orgId}
        production={<ProjectProductionPanel project={project} orgId={orgId} />}
      />
    );
  if (section === "documents")
    return <ProjectDocumentPanel project={project} orgId={orgId} onCompare={onCompare} />;
  return null;
}

import { useState } from "react";

import { documentaryArtifactAccess } from "../../api/generated/dekopen";
import type { ProjectResponse } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { Button } from "../../ui";
import { runJob } from "../jobs/runJob";

type Layout = "OT" | "VIDRIOS" | "MONTAJE" | "STANDARD";

const DOCUMENTS: { type: string; layout: Layout; label: string; hint: string }[] = [
  { type: "DOC-03", layout: "OT", label: "Orden de trabajo", hint: "Una hoja por ventana" },
  { type: "DOC-05", layout: "STANDARD", label: "Optimización de corte", hint: "Barra por barra" },
  { type: "DOC-03", layout: "VIDRIOS", label: "Informe de vidrios", hint: "Para el vidriero" },
  {
    type: "DOC-03",
    layout: "MONTAJE",
    label: "Listado de montaje",
    hint: "Con casillas de control",
  },
];

/** The sealed, releasable revision of the work: what the workshop prints. */
export function releasableVersion(project: ProjectResponse): string | null {
  const versions = project.versions ?? [];
  const chosen =
    versions.find((version) => version.id === project.accepted_version_id) ??
    versions.find((version) => version.revision_code === project.current_revision);
  return chosen?.production_allowed ? chosen.id : null;
}

/** Print-ready workshop documents of the approved revision, one click each. */
export function WorkshopDocuments({
  project,
  orgId,
}: {
  project: ProjectResponse;
  orgId: string;
}): JSX.Element | null {
  const versionId = releasableVersion(project);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  if (!versionId) return null;

  async function open(document: (typeof DOCUMENTS)[number]) {
    if (!versionId) return;
    // Open the tab inside the click so the popup blocker lets it through.
    const tab = window.open("", "_blank");
    setBusy(document.label);
    setMessage("");
    try {
      const options = { headers: { "X-Organization-ID": orgId } };
      const job = await runJob(
        {
          type: "document.artifact.generate",
          payload: {
            document_type: document.type,
            format: "PDF",
            project_version_id: versionId,
            order_id: null,
            layout: document.layout,
          },
          idempotency_key: `${document.type.toLowerCase()}:pdf:${versionId}:${document.layout === "STANDARD" ? "" : document.layout.toLowerCase()}`,
        },
        options,
      );
      const artifact = (job.result as { artifact: { id: string } }).artifact;
      const access = await documentaryArtifactAccess(artifact.id, options);
      if (access.status !== 200) throw new ApiError(access.status, access.data);
      if (tab) tab.location.href = access.data.signed_url;
      else window.open(access.data.signed_url, "_blank", "noopener,noreferrer");
    } catch {
      tab?.close();
      setMessage("No se pudo preparar el documento. Vuelve a intentarlo.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="workshop-docs" aria-label="Documentos para el taller">
      <h3>Documentos para el taller</h3>
      <div className="workshop-docs__list">
        {DOCUMENTS.map((document) => (
          <Button
            key={`${document.type}-${document.layout}`}
            variant="secondary"
            disabled={busy !== null}
            onClick={() => void open(document)}
          >
            <span className="workshop-docs__label">
              {busy === document.label ? "Preparando…" : document.label}
              <small>{document.hint}</small>
            </span>
          </Button>
        ))}
      </div>
      {message && <p role="alert">{message}</p>}
    </section>
  );
}

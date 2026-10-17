import { Link } from "react-router-dom";
import type { ProjectResponse } from "../../api/generated/models";
import { Icon } from "../../ui/Icon";
import { StatusBadge } from "../../ui/StatusBadge";
import { formatDate, formatMoney } from "../money";

const STAGES: Record<ProjectResponse["status"], { label: string; next: string; step: number }> = {
  DRAFT: { label: "En diseño", next: "Continuar diseño", step: 0 },
  QUOTED: { label: "Cotizada", next: "Revisar propuesta", step: 1 },
  APPROVED: { label: "Aprobada", next: "Preparar fabricación", step: 2 },
  IN_PRODUCTION: { label: "En fabricación", next: "Ver avance del taller", step: 3 },
  COMPLETED: { label: "Terminada", next: "Consultar obra", step: 4 },
  CANCELLED: { label: "Cancelada", next: "Consultar obra", step: -1 },
};

export function ProjectBoard({
  projects,
  disabled,
}: {
  projects: ProjectResponse[];
  disabled: boolean;
}) {
  return (
    <div className="project-board" aria-label="Obras">
      {projects.map((project) => {
        const stage = STAGES[project.status];
        return (
          <article className="project-cover" key={project.id}>
            <header>
              <span className="project-cover__code">{project.code}</span>
              <StatusBadge showIcon={false} tone={stage.step === 4 ? "success" : "neutral"}>
                {stage.label}
              </StatusBadge>
            </header>
            <h2>
              {disabled ? (
                project.name || project.code
              ) : (
                <Link to={`/projects/${project.id}`}>{project.name || project.code}</Link>
              )}
            </h2>
            <p className="project-cover__client">{project.client_name || "Cliente por definir"}</p>
            <div className="project-cover__facts">
              <span>
                <Icon name="window" size={19} />
                <strong>{project.position_count}</strong>{" "}
                {project.position_count === 1 ? "posición" : "posiciones"}
              </span>
              <strong>
                {project.pricing_current
                  ? formatMoney(project.total_price_gross, project.currency)
                  : "Precio por preparar"}
              </strong>
            </div>
            <div className="project-cover__progress" aria-label={stage.label}>
              {[0, 1, 2, 3, 4].map((step) => (
                <span key={step} data-done={stage.step >= step || undefined} />
              ))}
            </div>
            <footer>
              <time dateTime={project.updated_at}>{formatDate(project.updated_at)}</time>
              {disabled ? (
                <span>{stage.next}</span>
              ) : (
                <Link
                  to={`/projects/${project.id}${project.status === "QUOTED" ? "?section=quote" : project.status === "IN_PRODUCTION" ? "?section=production" : ""}`}
                >
                  {stage.next}
                  <Icon name="arrow" size={17} />
                </Link>
              )}
            </footer>
          </article>
        );
      })}
    </div>
  );
}

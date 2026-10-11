import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import activation from "../../../../docs/operations/ACTIVACION.md?raw";
import { aiSettingsGet } from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { ErrorState, LoadingState, StatusBadge } from "../../ui";
import { AI_CAPABILITIES } from "../assistant/providerLabels";

const guideUrl =
  "https://github.com/KaraAliOsman/framedex/blob/integracion/v1/docs/operations/ACTIVACION.md";
const headings = [
  "Railway / hosting",
  "Flow",
  "SII / DTE",
  "Correo con dominio propio",
  "Webhooks productivos",
  "Proveedor de IA",
];

function instructions(heading: string): { introduction: string; steps: string[] } {
  const section =
    activation.split(`## ${heading}\n`)[1]?.split(/\n## /u)[0] ??
    activation.replace(/\r/gu, "").split(`## ${heading}\n`)[1]?.split(/\n## /u)[0] ??
    "";
  const introduction =
    section
      .split("\n")
      .find((line) => /^\|\s*Activacion\s*\|/u.test(line))
      ?.split("|")[2]
      ?.trim() ?? "";
  const steps = [...section.matchAll(/^\d+\. ([\s\S]*?)(?=^\d+\. |\n\n|$)/gmu)].map((match) =>
    match[1]!.replace(/\s+/gu, " ").trim(),
  );
  return { introduction, steps };
}

function plain(value: string): string {
  return value.replace(/\[([^\]]+)\]\([^)]*\)/gu, "$1").replace(/[`*]/gu, "");
}

export function ActivationGuide({ orgId }: { orgId: string }): JSX.Element {
  const ai = useQuery({
    queryKey: ["ai", "settings", orgId],
    queryFn: async ({ signal }) => {
      const result = await aiSettingsGet({ headers: { "X-Organization-ID": orgId }, signal });
      if (result.status !== 200) throw new ApiError(result.status, result.data);
      return result.data;
    },
  });
  return (
    <section className="settings-card">
      <h2>Activación de proveedores</h2>
      <p>
        Flow, SII y correo muestran su conexión comprobada abajo. Los simuladores conservan la marca
        de prueba en pagos y documentos.
      </p>
      <h3>Inteligencia artificial</h3>
      {ai.isPending ? (
        <LoadingState label="Comprobando proveedor de IA" />
      ) : ai.isError ? (
        <ErrorState
          body="No pudimos comprobar las rutas de IA."
          onRetry={() => void ai.refetch()}
        />
      ) : (
        <ul className="settings-invitations">
          {ai.data.routes.map((route) => (
            <li key={route.capability}>
              <strong>{AI_CAPABILITIES[route.capability]}</strong>
              <StatusBadge
                label={
                  {
                    CONNECTED: "Conectado",
                    MISSING_CREDENTIAL: "No configurado",
                    UNTESTED: "Configurado · falta prueba",
                    ERROR: "Error de conexión",
                  }[route.state]
                }
                tone={route.state === "ERROR" ? "danger" : "neutral"}
              />
              {route.last_cause && <p>{route.last_cause}</p>}
            </li>
          ))}
        </ul>
      )}
      <Link className="ui-button" to="/settings/general?section=ai">
        Revisar proveedor, prueba y presupuesto
      </Link>
      <h3>Pasos de activación</h3>
      <p>
        Estas instrucciones proceden de la guía de activación del producto. Hosting y webhooks
        requieren configurar y verificar el entorno público antes de distribuir enlaces.
      </p>
      {headings.map((heading) => {
        const guide = instructions(heading);
        return (
          <details key={heading} className="settings-activation">
            <summary>{heading === "Railway / hosting" ? "Despliegue y hosting" : heading}</summary>
            <p>{plain(guide.introduction)}</p>
            {guide.steps.length > 0 && (
              <ol>
                {guide.steps.map((step, index) => (
                  <li key={index}>{plain(step)}</li>
                ))}
              </ol>
            )}
          </details>
        );
      })}
      <a href={guideUrl} target="_blank" rel="noreferrer">
        Abrir guía completa de activación
      </a>
    </section>
  );
}

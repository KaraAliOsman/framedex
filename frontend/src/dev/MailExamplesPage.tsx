import { useQuery } from "@tanstack/react-query";
import { mailExamples } from "../api/generated/dekopen";
import { ApiError } from "../api/apiMutator";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { MailFrame } from "../features/notifications/MailPanels";
import { DeniedState, ErrorState, LoadingState } from "../ui";
const LABEL: Record<string, string> = {
  MAGIC_LINK: "Enlace de acceso",
  QUOTE: "Cotización al cliente",
  APPROVAL: "Aprobación recibida",
  PAYMENT: "Pago registrado",
  ORDER_BLOCKED: "OT bloqueada",
};

export function MailExamplesPage(): JSX.Element {
  const org = useAuthSession().me?.active_organization;
  const allowed = ["OWNER", "ESTIMATOR"].includes(org?.role ?? "");
  const query = useQuery({
    queryKey: ["mail-examples", org?.id],
    enabled: allowed,
    queryFn: async ({ signal }) => {
      const response = await mailExamples({ headers: { "X-Organization-ID": org!.id }, signal });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
  });
  if (!allowed)
    return <DeniedState reason="El dueño o estimador revisa los correos de la organización." />;
  return (
    <main className="mail-examples" data-density="office">
      <h1>Correos de la organización</h1>
      <p>
        Vista previa sin envío. Los correos reales toman sus datos de la emisión o del evento
        registrado.
      </p>
      {query.isPending ? (
        <LoadingState label="Cargando plantillas" />
      ) : query.isError ? (
        <ErrorState
          title="No se pudieron cargar los correos"
          onRetry={() => {
            void query.refetch();
          }}
        />
      ) : (
        query.data.map((item) => (
          <section key={item.kind} aria-label={LABEL[item.kind]}>
            <h2>{LABEL[item.kind]}</h2>
            <MailFrame html={item.html} title={LABEL[item.kind] ?? "Correo"} />
          </section>
        ))
      )}
    </main>
  );
}

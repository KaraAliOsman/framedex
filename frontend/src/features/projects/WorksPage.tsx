import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { ApiError } from "../../api/apiMutator";
import { projectsWorks } from "../../api/generated/dekopen";
import type { ProjectsWorksParams } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { Button, DeniedState, ErrorState, LoadingState } from "../../ui";
import { ProjectsHome } from "./ProjectsHome";

export function WorksPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  const user = auth.session?.user.id;
  if (!org || !user || !["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role))
    return (
      <DeniedState reason="Tu trabajo está en Hoy y Taller. Solicita acceso al dueño para consultar Obras." />
    );
  const identity = [user, org.id, org.role].join(":");
  return (
    <WorksIndex
      key={identity}
      orgId={org.id}
      orgName={org.name}
      canWrite={org.role !== "WORKSHOP_MANAGER"}
      identity={identity}
    />
  );
}

function WorksIndex({
  orgId,
  orgName,
  canWrite,
  identity,
}: {
  orgId: string;
  orgName: string;
  canWrite: boolean;
  identity: string;
}): JSX.Element {
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(
    ["q", "view", "stage", "status", "sort", "attention", "phase", "currency"].map((key) => [
      key,
      params.get(key) ?? "",
    ]),
  ) as ProjectsWorksParams;
  const rawOffset = Number(params.get("offset") ?? 0);
  const offset = Number.isSafeInteger(rawOffset) && rawOffset >= 0 ? rawOffset : 0;
  const query = useQuery({
    queryKey: ["works", identity, filters, offset],
    queryFn: async ({ signal }) => {
      const response = await projectsWorks(
        { ...filters, offset, limit: 50 },
        { signal, headers: { "X-Organization-ID": orgId } },
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      return response.data;
    },
    retry: false,
    placeholderData: keepPreviousData,
  });
  if (query.isPending) return <LoadingState label="Cargando obras" />;
  if (query.isError)
    return (
      <section>
        <ErrorState
          title="No se pudieron cargar las obras"
          body={
            query.error instanceof ApiError && query.error.status === 409
              ? "La lista cambió mientras la consultabas. Vuelve a cargar las obras."
              : "Reintenta la consulta o quita los filtros del enlace."
          }
          onRetry={() => void query.refetch()}
        />
        <Button onClick={() => setParams({})}>Quitar filtros</Button>
      </section>
    );
  return (
    <ProjectsHome
      items={query.data.items}
      index={query.data}
      orgId={orgId}
      orgName={orgName}
      canWrite={canWrite}
      loading={query.isPlaceholderData}
    />
  );
}

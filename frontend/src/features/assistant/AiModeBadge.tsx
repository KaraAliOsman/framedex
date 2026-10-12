import { StatusBadge } from "../../ui/StatusBadge";
import { useQuery } from "@tanstack/react-query";
import { aiModeGet } from "../../api/generated/dekopen";
import { useAuthSession } from "../../auth/AuthSessionProvider";

export function AiModeBadge(): JSX.Element | null {
  const org = useAuthSession().me?.active_organization;
  const query = useQuery({
    queryKey: ["ai", "mode", org?.id],
    enabled:
      import.meta.env.DEV && !!org && ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"].includes(org.role),
    staleTime: 30000,
    refetchInterval: 30000,
    queryFn: async () => {
      const response = await aiModeGet({ headers: { "X-Organization-ID": org!.id } });
      return response.status === 200 && response.data.test_mode;
    },
  });
  return import.meta.env.DEV && query.data ? (
    <StatusBadge
      showIcon={false}
      className="status-chip"
      title="La IA de esta organización incluye un proveedor de prueba explícito"
    >
      Proveedor de prueba
    </StatusBadge>
  ) : null;
}

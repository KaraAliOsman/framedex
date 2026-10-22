import { useQuery } from "@tanstack/react-query";
import { engineSystems } from "../../api/generated/dekopen";

/** The choice belongs to the new project, never to company defaults. */
export function NewProjectSeries({
  orgId,
  value,
  disabled,
  onChange,
}: {
  orgId: string;
  value: string;
  disabled: boolean;
  onChange: (id: string) => void;
}): JSX.Element {
  const systems = useQuery({
    queryKey: ["project-systems", orgId],
    queryFn: async ({ signal }) => {
      const response = await engineSystems({ headers: { "X-Organization-ID": orgId }, signal });
      if (response.status !== 200) throw new Error("systems");
      return response.data.systems;
    },
  });
  const available = systems.data?.some((item) => item.id === value);
  return (
    <label>
      Serie inicial para las ventanas
      <select
        aria-label="Serie inicial para las ventanas"
        value={value}
        disabled={disabled || systems.isPending}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">Elegir en cada ventana</option>
        {value && !available && (
          <option value={value}>
            {systems.isPending ? "Cargando la serie…" : "Serie no disponible · elige otra"}
          </option>
        )}
        {systems.data?.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
      <small>Esta elección se guarda solo en la nueva obra. Podrás cambiarla después.</small>
      {systems.isError && (
        <span role="alert">
          No se pudieron cargar las series.{" "}
          <button type="button" onClick={() => void systems.refetch()}>
            Volver a intentar
          </button>
        </span>
      )}
    </label>
  );
}

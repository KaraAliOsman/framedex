import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { catalogVisualsCreate } from "../../api/generated/dekopen";
import type { CatalogVisual } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { Icon } from "../../ui/Icon";
import { catalogVisualKey } from "./catalogVisuals";

export function VisualSampleControl({
  organizationId,
  systemId,
  kind,
  targetKey,
  label,
  sample,
}: {
  organizationId: string;
  systemId: string;
  kind: "PROFILE" | "TEXTURE";
  targetKey: string;
  label: string;
  sample?: CatalogVisual;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(file?: File): Promise<void> {
    if (busy) return;
    if (file && (!/image\/(png|jpeg|webp)/.test(file.type) || file.size > 8_000_000)) {
      setError("Usa una foto PNG, JPG o WebP de hasta 8 MB.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await catalogVisualsCreate(
        { system_id: systemId, kind, target_key: targetKey, file, cleared: !file },
        { headers: { "X-Organization-ID": organizationId } },
      );
      if (result.status !== 201) throw new ApiError(result.status, result.data);
      queryClient.setQueryData<CatalogVisual[]>(
        catalogVisualKey(organizationId, systemId),
        (old) => [
          result.data,
          ...(old ?? []).filter((entry) => entry.kind !== kind || entry.target_key !== targetKey),
        ],
      );
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.status === 403
          ? "Pide al dueño o encargado de taller que guarde la muestra."
          : "No se pudo guardar la foto. Revisa el archivo y reintenta.",
      );
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }
  return (
    <div className="catalog-sample-control">
      <input
        ref={fileInput}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        hidden
        aria-label={`Foto de ${label}`}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void save(file);
        }}
      />
      <button
        type="button"
        className="ui-button ui-button--small"
        disabled={busy}
        onClick={() => fileInput.current?.click()}
      >
        <Icon name="upload" size={15} />
        {busy ? "Guardando…" : sample && !sample.cleared ? "Cambiar foto" : "Añadir foto"}
      </button>
      {sample && !sample.cleared ? (
        <button
          type="button"
          className="ui-button ui-button--ghost ui-button--small"
          disabled={busy}
          onClick={() => void save()}
        >
          Usar ilustración
        </button>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}

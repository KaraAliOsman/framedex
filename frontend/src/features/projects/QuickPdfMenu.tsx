import { useEffect, useState } from "react";
import { apiFetchBlob } from "../../api/apiMutator";
import { getDocumentsQuickDraftUrl } from "../../api/generated/dekopen";
import type { DocumentEnum } from "../../api/generated/models";
import { Icon } from "../../ui/Icon";
import { Menu } from "../../ui/Overlays";
import { useToast } from "../../ui/Toast";
import { actionErrorDetail } from "../errors";

const DOCUMENTS: { id: DocumentEnum; label: string; hint: string }[] = [
  {
    id: "QUOTE",
    label: "Cotización borrador",
    hint: "Con el precio de tus reglas. Dice «Borrador» hasta que la emitas.",
  },
  { id: "CUT", label: "Hoja de corte", hint: "Barras, piezas y medidas de corte." },
  { id: "PLAN", label: "Plano de ventanas", hint: "Dibujo acotado de cada ventana." },
  { id: "MATERIALS", label: "Materiales", hint: "Perfiles y refuerzos que pide la obra." },
];

/** Any document from a name and one window — no step is a gate. The server
 * composes it with the issuing authority and stores nothing. */
export function QuickPdfMenu({
  projectId,
  orgId,
}: {
  projectId: string;
  orgId: string;
}): JSX.Element {
  const { notify } = useToast();
  const [busy, setBusy] = useState<DocumentEnum | null>(null);
  const [ready, setReady] = useState<{ label: string; url: string; name: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => (ready ? URL.revokeObjectURL(ready.url) : undefined), [ready]);

  async function generate(document: (typeof DOCUMENTS)[number]): Promise<void> {
    setBusy(document.id);
    setError(null);
    try {
      const { blob, filename } = await apiFetchBlob(getDocumentsQuickDraftUrl(projectId), {
        method: "POST",
        headers: { "X-Organization-ID": orgId, "Content-Type": "application/json" },
        body: JSON.stringify({ document: document.id }),
      });
      const url = URL.createObjectURL(blob);
      const name = filename ?? `${document.label.toLowerCase().replaceAll(" ", "-")}.pdf`;
      const link = window.document.createElement("a");
      link.href = url;
      link.download = name;
      link.click();
      setReady({ label: document.label, url, name });
      notify(`${document.label} lista.`);
    } catch (failure) {
      setError(
        actionErrorDetail(failure, `No se pudo preparar «${document.label}». Inténtalo de nuevo.`),
      );
    } finally {
      setBusy(null);
    }
  }

  const working = DOCUMENTS.find((item) => item.id === busy);
  return (
    <span className="quick-pdf">
      <Menu
        label="Sacar PDF"
        busy={busy !== null}
        note="Con un nombre y una ventana ya puedes sacar cualquiera. No hace falta terminar los pasos."
        trigger={
          <>
            <Icon name="document" size={16} />
            {working ? `Preparando ${working.label.toLowerCase()}…` : "Sacar PDF"}
          </>
        }
        items={DOCUMENTS.map((item) => ({
          id: item.id,
          label: item.label,
          hint: item.hint,
          onSelect: () => void generate(item),
        }))}
      />
      {ready && !busy ? (
        <a className="quick-pdf__again" href={ready.url} target="_blank" rel="noreferrer">
          Abrir {ready.label.toLowerCase()}
        </a>
      ) : null}
      {error ? (
        <span className="quick-pdf__error" role="alert">
          {error}
        </span>
      ) : null}
    </span>
  );
}

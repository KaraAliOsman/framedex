import { useEffect, useState } from "react";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { ApiError } from "../../api/apiMutator";
import { inventorySheetFormatDeclare, inventorySheetFormats } from "../../api/generated/dekopen";
import type {
  SheetFormatList,
  SheetFormatOption,
  SheetFormatRequestRequest,
} from "../../api/generated/models";
import { fmtMm } from "../../format";
import { parseDecimalInput } from "../../decimal";
import { Button, DeniedState, DimLoader, PageHeader } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";
import "./catalogs.css";

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = (error.payload as { error?: { detail?: string } })?.error?.detail;
    return detail ?? "No se pudo guardar el formato. Revisa tus permisos y reintenta.";
  }
  return "No se pudieron cargar los formatos. Revisa la conexión y reintenta.";
}

export function SheetFormatsPage(): JSX.Element {
  const { status, me } = useAuthSession();
  const role = me?.active_organization?.role;
  if (status !== "ready") return <DimLoader label="Cargando formatos de lámina…" />;
  if (!role || !["OWNER", "WORKSHOP_MANAGER", "ESTIMATOR", "OPERATOR"].includes(role))
    return <DeniedState reason="Tu rol no permite consultar formatos de lámina." />;
  return (
    <SheetFormats
      key={me?.active_organization?.id}
      canWrite={["OWNER", "WORKSHOP_MANAGER"].includes(role)}
    />
  );
}

function SheetFormats({ canWrite }: { canWrite: boolean }): JSX.Element {
  const [data, setData] = useState<SheetFormatList | null>(null);
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [draft, setDraft] = useState(false);
  const [selected, setSelected] = useState<SheetFormatOption | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    void inventorySheetFormats({ signal: controller.signal })
      .then((response) => {
        if (response.status !== 200) throw Error();
        if (!controller.signal.aborted) {
          setData(response.data);
          setError("");
        }
      })
      .catch((caught) => {
        if (!controller.signal.aborted) setError(errorText(caught));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reload]);
  return (
    <section className="catalog sheet-formats" aria-busy={busy || loading}>
      <PageHeader
        title="Formatos de lámina"
        context="Catálogo › Vidrios y paneles"
        actions={
          canWrite && data && !draft ? (
            <Button
              variant="primary"
              disabled={!data.options.length}
              onClick={() => setDraft(true)}
            >
              Declarar formato
            </Button>
          ) : undefined
        }
      />
      <p>
        Declara las medidas y el despunte indicados por el proveedor. Cada formato conserva su
        fuente; el plan de corte cambia cuando vuelves a optimizar la OT.
      </p>
      <a href="/production">Volver a Producción</a>
      {loading ? <DimLoader label="Cargando formatos de lámina…" /> : null}
      {error ? (
        <div>
          <p role="alert">{error}</p>
          <Button onClick={() => setReload((value) => value + 1)}>Reintentar</Button>
        </div>
      ) : null}
      {notice ? <p role="status">{notice}</p> : null}
      {!canWrite ? (
        <p>
          El jefe de taller o el dueño puede declarar un suministro. Puedes consultar los formatos
          existentes.
        </p>
      ) : null}
      {data && !data.options.length ? (
        <p role="status">
          Sin vidrio o panel en el catálogo. Declara primero la composición o el artículo compatible
          en <a href="/catalogs/systems">Catálogo técnico</a>.
        </p>
      ) : null}
      {data && !data.items.length ? (
        <p>
          Sin formatos de lámina declarados. Las piezas conservarán su medida y aparecerán como no
          ubicadas.
        </p>
      ) : null}
      {draft && data ? (
        <ValidatedForm
          className="sheet-format-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!selected) return;
            const fields = new FormData(event.currentTarget);
            const value = (key: string) => String(fields.get(key) ?? "").trim();
            const body: SheetFormatRequestRequest = {
              kind: selected.kind as SheetFormatRequestRequest["kind"],
              technical_sku: selected.sku,
              sku: value("sku"),
              supplier: value("supplier"),
              source: value("source"),
              width_mm: parseDecimalInput(value("width_mm"), 2)!,
              height_mm: parseDecimalInput(value("height_mm"), 2)!,
              edge_trim_mm: parseDecimalInput(value("edge_trim_mm"), 2)!,
            };
            setBusy(true);
            setError("");
            setNotice("");
            void inventorySheetFormatDeclare(body)
              .then(() => {
                setDraft(false);
                setSelected(null);
                setReload((current) => current + 1);
                setNotice("Formato declarado. Vuelve a la OT y optimiza con este suministro.");
              })
              .catch((caught) => setError(errorText(caught)))
              .finally(() => setBusy(false));
          }}
        >
          <fieldset disabled={busy}>
            <legend>Declaración del suministro</legend>
            <label>
              Vidrio o panel
              <select
                aria-label="Vidrio o panel"
                required
                value={selected ? `${selected.kind}:${selected.sku}` : ""}
                onChange={(event) =>
                  setSelected(
                    data.options.find(
                      (item) => `${item.kind}:${item.sku}` === event.target.value,
                    ) ?? null,
                  )
                }
              >
                <option value="">Seleccione el artículo</option>
                {data.options.map((item) => (
                  <option key={`${item.kind}:${item.sku}`} value={`${item.kind}:${item.sku}`}>
                    {item.kind === "GLASS" ? "Vidrio" : "Panel"} · {item.name}
                    {item.is_demo ? " · DEMO" : ""}
                  </option>
                ))}
              </select>
            </label>
            {selected?.is_demo ? (
              <p>
                DEMO · Artículo sintético, sin certificación. La declaración conserva esta marca.
              </p>
            ) : null}
            <label>
              Código de compra del proveedor
              <input name="sku" required maxLength={100} />
            </label>
            <label>
              Proveedor
              <input name="supplier" required maxLength={255} />
            </label>
            {(["width_mm", "height_mm", "edge_trim_mm"] as const).map((key) => (
              <label key={key}>
                {
                  {
                    width_mm: "Ancho de lámina (mm)",
                    height_mm: "Alto de lámina (mm)",
                    edge_trim_mm: "Despunte por borde (mm)",
                  }[key]
                }
                <input
                  name={key}
                  required
                  type="text"
                  inputMode="decimal"
                  data-precision="2"
                  min={key === "edge_trim_mm" ? "0" : "0.01"}
                />
              </label>
            ))}
            <label>
              Fuente de las medidas
              <input
                name="source"
                required
                maxLength={500}
                placeholder="Ficha o declaración del proveedor, fecha y referencia"
              />
            </label>
            <div className="sheet-format-actions">
              <Button type="submit" variant="primary">
                {busy ? "Guardando…" : "Guardar declaración"}
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setDraft(false);
                  setSelected(null);
                }}
              >
                Cancelar
              </Button>
            </div>
          </fieldset>
        </ValidatedForm>
      ) : null}
      {data?.items.length ? (
        <div className="catalog-table-scroll">
          <table className="catalog-contents">
            <caption>Formatos declarados para la optimización</caption>
            <thead>
              <tr>
                <th>Artículo / compra</th>
                <th>Formato mm</th>
                <th>Despunte mm</th>
                <th>Proveedor</th>
                <th>Fuente</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id}>
                  <td data-label="Artículo / compra">
                    {item.technical_sku} · {item.sku}
                    {item.is_demo ? " · DEMO" : ""}
                  </td>
                  <td className="ui-value" data-label="Formato mm">
                    {fmtMm(item.width_mm)} × {fmtMm(item.height_mm)}
                  </td>
                  <td className="ui-value" data-label="Despunte mm">
                    {fmtMm(item.edge_trim_mm)}
                  </td>
                  <td data-label="Proveedor">
                    {item.supplier ?? "Sin dato · declaración histórica"}
                  </td>
                  <td data-label="Fuente">{item.source ?? "Sin dato · declaración histórica"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

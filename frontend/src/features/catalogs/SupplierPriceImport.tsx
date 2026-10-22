import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  pricingAdminList,
  pricingAdminWrite,
  pricingSupplierInspect,
  pricingSupplierReview,
} from "../../api/generated/dekopen";
import type { SupplierInspection, SupplierPreview } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { formatDate, formatDecimal } from "../../format";
import { Button, Loading } from "../../ui";
import { ValidatedForm } from "../../ui/FormValidation";
import { actionErrorDetail } from "../errors";
import "./supplier-price-import.css";

const fields = [
  ["sku", "Código"],
  ["description", "Descripción"],
  ["unit", "Unidad de compra"],
  ["unit_cost", "Precio de compra"],
] as const;
type Field = (typeof fields)[number][0];
type Mapping = Record<Field, string>;
type CostList = { id: string; supplier_name: string; currency: string; valid_from: string };
export type PriceImportReceipt = { costListId: string; fileName: string; total: number };
const emptyMapping: Mapping = { sku: "", description: "", unit: "", unit_cost: "" };
const units: Record<string, string> = {
  BAR: "Barra",
  M: "Metro",
  M2: "m²",
  KIT: "Kit",
  UNIT: "Unidad",
  EA: "Unidad",
};

/** Codes and amounts remain strings; parsing and validation belong to the server. */
export function SupplierPricePreview({
  inspection,
  mapping,
  preview,
  currency,
}: {
  inspection: SupplierInspection;
  mapping: Mapping;
  preview: SupplierPreview | null;
  currency?: string;
}): JSX.Element {
  const rows =
    preview?.items.map((item) => [
      item.sku,
      item.description,
      units[item.unit] ?? item.unit,
      `${formatDecimal(item.unit_cost, 4)} ${currency ?? ""}`.trim(),
    ]) ??
    inspection.preview.map((row) =>
      fields.map(([field]) => {
        const index = inspection.columns.indexOf(mapping[field]);
        return index < 0 ? "Elige una columna" : row[index] || "Vacío en el archivo";
      }),
    );
  return (
    <div
      className="supplier-prices__scroll"
      role="region"
      aria-label="Muestra de precios"
      tabIndex={0}
    >
      <table>
        <caption>
          Muestra de precios · {rows.length} / {preview?.total ?? inspection.total}
        </caption>
        <thead>
          <tr>
            {fields.map(([field, label]) => (
              <th key={field} scope="col">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((value, column) => (
                <td key={column} className={column === 3 ? "supplier-prices__amount" : undefined}>
                  {value}
                </td>
              ))}
            </tr>
          ))}
          {!rows.length && (
            <tr>
              <td colSpan={4}>El archivo no tiene filas de precios. Elige otro archivo.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export function SupplierPriceImport({
  orgId,
  initialSupplier = "",
  onApplied,
  onBusyChange,
}: {
  orgId: string;
  initialSupplier?: string;
  onApplied?: (receipt: PriceImportReceipt) => void;
  onBusyChange?: (busy: boolean) => void;
}): JSX.Element {
  const client = useQueryClient();
  const queryKey = ["supplier-price-lists", orgId];
  const options = { headers: { "X-Organization-ID": orgId } };
  const [file, setFile] = useState<File | null>(null);
  const [inspection, setInspection] = useState<SupplierInspection | null>(null);
  const [mapping, setMapping] = useState<Mapping>(emptyMapping);
  const [separator, setSeparator] = useState<"." | ",">(",");
  const [listId, setListId] = useState("");
  const [creating, setCreating] = useState(false);
  const [preview, setPreview] = useState<SupplierPreview | null>(null);
  const [receipt, setReceipt] = useState<PriceImportReceipt | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const lists = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await pricingAdminList("cost-lists", { ...options, signal });
      if (response.status !== 200) throw new Error("lists");
      return response.data.items.filter(
        (row) =>
          row.is_active === true &&
          typeof row.id === "string" &&
          typeof row.supplier_name === "string" &&
          typeof row.currency === "string" &&
          typeof row.valid_from === "string",
      ) as CostList[];
    },
    refetchOnWindowFocus: false,
  });
  const selectedList = lists.data?.find((row) => row.id === listId);
  const completeMapping =
    fields.every(([field]) => !!mapping[field]) &&
    new Set(Object.values(mapping)).size === fields.length;

  function invalidate() {
    setPreview(null);
    setError("");
  }
  async function run(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    onBusyChange?.(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) setPreview(null);
      setError(
        actionErrorDetail(
          failure,
          "No se pudo completar la importación. Conservamos tu selección; vuelve a intentarlo.",
        ),
      );
    } finally {
      lock.current = false;
      setBusy(false);
      onBusyChange?.(false);
    }
  }
  function chooseFile(next: File | undefined) {
    if (lock.current) return;
    setFile(null);
    setInspection(null);
    setMapping(emptyMapping);
    invalidate();
    if (!next) return;
    if (!/\.(xlsx|csv)$/i.test(next.name) || !next.size || next.size > 5 * 1024 * 1024) {
      setError("Elige un XLSX o CSV con contenido, de hasta 5 MB.");
      return;
    }
    setFile(next);
    void run(async () => {
      const response = await pricingSupplierInspect({ file: next }, options);
      if (response.status !== 200) throw new Error("inspect");
      setInspection(response.data);
      setMapping(
        Object.fromEntries(
          fields.map(([field]) => [field, response.data.suggested_mapping[field] ?? ""]),
        ) as Mapping,
      );
    });
  }
  async function review(apply: boolean) {
    if (
      !file ||
      !selectedList ||
      !completeMapping ||
      !inspection?.total ||
      (apply && !preview?.review_token)
    )
      return;
    const token = preview?.review_token;
    if (!apply) setPreview(null);
    await run(async () => {
      const response = await pricingSupplierReview(
        {
          file,
          mapping: JSON.stringify(mapping),
          decimal_separator: separator,
          cost_list_id: selectedList.id,
          reason: "Precios del proveedor revisados por el dueño del taller",
          apply,
          ...(apply && token ? { review_token: token } : {}),
        },
        options,
      );
      if (response.status !== 200 || response.data.applied !== apply) throw new Error("review");
      if (!apply) setPreview(response.data);
      else {
        const saved = {
          costListId: selectedList.id,
          fileName: file.name,
          total: response.data.total,
        };
        setReceipt(saved);
        setPreview(null);
        onApplied?.(saved);
      }
    });
  }
  if (receipt)
    return (
      <div className="supplier-prices" role="status">
        <h2>Precios guardados</h2>
        <p>
          {receipt.total} {receipt.total === 1 ? "precio guardado" : "precios guardados"} de{" "}
          {receipt.fileName}. Origen: datos del taller.
        </p>
        <p>
          Proveedor: {selectedList?.supplier_name} · {selectedList?.currency}. Los cambios conservan
          su historial.
        </p>
      </div>
    );

  return (
    <div className="supplier-prices" aria-busy={busy}>
      <header>
        <h2>Importa los precios de tu proveedor</h2>
        <p>Elige el archivo, revisa sus columnas y confirma los precios antes de guardarlos.</p>
      </header>
      {error && <p role="alert">{error}</p>}
      <label>
        Archivo de precios
        <input
          className="ui-field__input"
          type="file"
          accept=".xlsx,.csv"
          disabled={busy}
          onChange={(event) => chooseFile(event.target.files?.[0])}
        />
      </label>
      <p className="supplier-prices__hint">
        XLSX o CSV UTF-8 · hasta 5 MB y 5.000 filas. Precios netos, sin separadores de miles.
        Reemplaza las fórmulas por valores.
      </p>
      {file && (
        <p>
          {file.name}
          {inspection && (
            <>
              {" "}
              · hoja {inspection.sheet} · {inspection.total}{" "}
              {inspection.total === 1 ? "fila" : "filas"}
            </>
          )}
        </p>
      )}
      {file && !inspection && !busy && (
        <Button onClick={() => chooseFile(file)}>Volver a leer el archivo</Button>
      )}
      {lists.isPending ? (
        <Loading label="Cargando listas de precios" />
      ) : lists.isError ? (
        <div role="alert">
          <p>No se pudieron cargar las listas del taller.</p>
          <Button onClick={() => void lists.refetch()}>Volver a cargar listas</Button>
        </div>
      ) : (
        <label>
          Lista de destino
          <select
            className="ui-field__input"
            value={listId}
            disabled={busy || creating}
            onChange={(event) => {
              setListId(event.target.value);
              invalidate();
            }}
          >
            <option value="">Elige una lista de precios</option>
            {lists.data.map((list) => (
              <option key={list.id} value={list.id}>
                {list.supplier_name} · {list.currency} · desde {formatDate(list.valid_from)}
              </option>
            ))}
          </select>
        </label>
      )}
      {!creating ? (
        <Button
          disabled={busy || lists.isPending || lists.isError}
          onClick={() => {
            setCreating(true);
            invalidate();
          }}
        >
          Crear una lista nueva
        </Button>
      ) : (
        <ValidatedForm
          className="supplier-prices__new"
          onSubmit={(event) => {
            event.preventDefault();
            const values = new FormData(event.currentTarget);
            void run(async () => {
              const response = await pricingAdminWrite(
                "cost-lists",
                {
                  reason: "Lista creada para importar los precios del proveedor",
                  values: {
                    supplier_name: String(values.get("supplier")).trim(),
                    currency: values.get("currency"),
                    valid_from: values.get("from"),
                    is_active: true,
                  },
                },
                options,
              );
              const created = response.status === 200 ? response.data.items[0] : null;
              if (!created || typeof created.id !== "string") throw new Error("create");
              client.setQueryData<CostList[]>(queryKey, (current) => [
                ...(current ?? []),
                created as CostList,
              ]);
              setListId(created.id);
              setCreating(false);
              invalidate();
            });
          }}
        >
          <fieldset disabled={busy}>
            <legend>Nueva lista del proveedor</legend>
            <label>
              Proveedor
              <input
                className="ui-field__input"
                name="supplier"
                defaultValue={initialSupplier}
                required
                maxLength={200}
              />
            </label>
            <label>
              Moneda
              <select className="ui-field__input" name="currency">
                <option value="CLP">Pesos chilenos · CLP</option>
                <option value="USD">Dólares · USD</option>
              </select>
            </label>
            <label>
              Vigente desde
              <input className="ui-field__input" type="date" name="from" required />
            </label>
          </fieldset>
          <p>Este clic crea una lista vacía. Los precios se guardan después de revisarlos.</p>
          <div className="supplier-prices__actions">
            <Button type="submit" variant="primary" loading={busy}>
              Crear lista
            </Button>
            <Button disabled={busy} onClick={() => setCreating(false)}>
              Cancelar nueva lista
            </Button>
          </div>
        </ValidatedForm>
      )}
      {inspection && (
        <>
          <fieldset className="supplier-prices__mapping" disabled={busy || creating}>
            <legend>Relaciona las columnas del archivo</legend>
            {fields.map(([field, label]) => (
              <label key={field}>
                {label}
                <select
                  className="ui-field__input"
                  value={mapping[field]}
                  onChange={(event) => {
                    setMapping({ ...mapping, [field]: event.target.value });
                    invalidate();
                  }}
                >
                  <option value="">Elige una columna</option>
                  {inspection.columns.map(
                    (column, index) =>
                      column && (
                        <option
                          key={index}
                          value={column}
                          disabled={inspection.columns.filter((name) => name === column).length > 1}
                        >
                          {column}
                        </option>
                      ),
                  )}
                </select>
              </label>
            ))}
            <label>
              Separador decimal en texto
              <select
                className="ui-field__input"
                value={separator}
                onChange={(event) => {
                  setSeparator(event.target.value as "." | ",");
                  invalidate();
                }}
              >
                <option value=",">Coma · 1234,5678</option>
                <option value=".">Punto · 1234.5678</option>
              </select>
            </label>
          </fieldset>
          {!completeMapping && (
            <p>
              Elige una columna distinta para cada campo. Los encabezados repetidos deben corregirse
              en el archivo.
            </p>
          )}
          <p>Unidades admitidas: Barra, Metro, m², Kit y Unidad. No convertimos kilos a metros.</p>
          <SupplierPricePreview
            inspection={inspection}
            mapping={mapping}
            preview={preview}
            currency={selectedList?.currency}
          />
          {preview ? (
            <section className="supplier-prices__confirmation" aria-label="Confirmación de precios">
              <h3>
                Revisa y confirma {preview.total} {preview.total === 1 ? "precio" : "precios"}
              </h3>
              <p>
                Lista de {selectedList?.supplier_name} · {selectedList?.currency}, vigente desde{" "}
                {formatDate(selectedList?.valid_from)}.
              </p>
              <p>
                Revisamos todas las filas; aquí ves hasta diez. Se guardarán como datos del taller.
                Si un código ya existe en esa lista, usa una lista nueva o edítalo en la ficha.
              </p>
              <Button variant="primary" loading={busy} onClick={() => void review(true)}>
                Confirmar y guardar precios
              </Button>
            </section>
          ) : (
            !creating && (
              <Button
                variant="primary"
                loading={busy}
                disabled={!selectedList || !completeMapping || !inspection.total}
                onClick={() => void review(false)}
              >
                Revisar todos los precios
              </Button>
            )
          )}
        </>
      )}
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetchBlob } from "../../api/apiMutator";
import { getProductionGlassOrderUrl, productionGlassOrder } from "../../api/generated/dekopen";
import { formatDecimal } from "../../decimal";
import { t } from "../../i18n/es-CL";
import { glassError } from "./glassErrors";
import "./glass.css";
import { LoadingState } from "../../ui/States";

export function GlassOrderPanel({ orderIds }: { orderIds: string[] }) {
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["glass-order", orderIds],
    enabled: show && orderIds.length > 0,
    retry: false,
    queryFn: async () => {
      const response = await productionGlassOrder({
        orders: orderIds.join(","),
        export_format: "JSON",
      });
      if (response.status !== 200 || !("rows" in response.data))
        throw new Error("glass_order_load");
      return response.data;
    },
  });
  async function download(format: "PDF" | "CSV") {
    setBusy(true);
    setError(null);
    try {
      const { blob, filename } = await apiFetchBlob(
        getProductionGlassOrderUrl({ orders: orderIds.join(","), export_format: format }),
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename ?? `pedido-vidrio.${format.toLowerCase()}`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (cause) {
      setError(glassError(cause));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="glass-order" aria-label={t("glass.orderTitle")}>
      <h3>{t("glass.orderTitle")}</h3>
      <p className="glass-help">{t("glass.orderHelp")}</p>
      {!orderIds.length ? (
        <p>{t("glass.orderEmpty")}</p>
      ) : (
        <>
          <div className="glass-order-controls">
            <button type="button" className="ghost-button" onClick={() => setShow(!show)}>
              {show ? t("glass.hideOrder") : t("glass.reviewOrder")}
            </button>
            <button
              type="button"
              className="ghost-button"
              disabled={busy}
              onClick={() => void download("PDF")}
            >
              {t("glass.orderPdf")}
            </button>
            <button
              type="button"
              className="ghost-button"
              disabled={busy}
              onClick={() => void download("CSV")}
            >
              {t("glass.orderCsv")}
            </button>
          </div>
          {show &&
            (query.isPending ? (
              <LoadingState label={t("glass.orderLoading")} />
            ) : query.isError ? (
              <div role="alert">
                <p>{glassError(query.error)}</p>
                <button type="button" className="ghost-button" onClick={() => void query.refetch()}>
                  {t("glass.retry")}
                </button>
              </div>
            ) : query.data?.rows.length === 0 ? (
              <p>{t("glass.noGlass")}</p>
            ) : (
              <>
                <p>{query.data.authority}</p>
                <ol className="glass-order-rows">
                  {query.data.rows.map((row, index) => (
                    <li key={index}>
                      <strong>
                        {row.order_code} · P{row.position_index} · {row.location}
                      </strong>
                      <p className="glass-number">
                        {formatDecimal(row.width_mm, row.integer_dimensions ? 0 : 2)} ×{" "}
                        {formatDecimal(row.height_mm, row.integer_dimensions ? 0 : 2)} mm ·{" "}
                        {row.quantity} {t("glass.pieces")}
                      </p>
                      <p>{row.composition}</p>
                      {row.instructions.map((instruction) => (
                        <p key={instruction}>{instruction}</p>
                      ))}
                    </li>
                  ))}
                </ol>
              </>
            ))}
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}

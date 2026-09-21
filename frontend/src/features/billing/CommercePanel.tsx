import { useEffect, useRef, useState } from "react";
import {
  billingChangeAbandon,
  billingChangeConfirm,
  billingChangePreview,
  billingCheckout,
  billingSync,
  commerceRetrieve,
} from "../../api/generated/dekopen";
import type { ChangeResult, Commerce, Offer } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";

const planLabel = (value: string) => t(`billing.${value}` as Parameters<typeof t>[0]);
const date = (value: string) =>
  new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Santiago",
  }).format(new Date(value));

export function CommercePanel({
  orgId,
  subscribed,
  onRefresh,
}: {
  orgId: string;
  subscribed: boolean;
  onRefresh: () => void;
}): JSX.Element {
  const [commerce, setCommerce] = useState<Commerce | null>(null);
  const [preview, setPreview] = useState<ChangeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const [pending, setPending] = useState(false);
  const [revision, setRevision] = useState(0);
  const mounted = useRef(true);
  const keys = useRef(new Map<string, string>());
  const options = { headers: { "X-Organization-ID": orgId } };
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void commerceRetrieve({ headers: { "X-Organization-ID": orgId }, signal: controller.signal })
      .then((result) => {
        if (!controller.signal.aborted) {
          if (result.status === 200) {
            setCommerce(result.data);
            if (result.data.pending_change) setPreview(result.data.pending_change);
          } else setFailed(true);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [orgId, revision]);
  const operation = (selection: string) => {
    if (!keys.current.has(selection)) keys.current.set(selection, crypto.randomUUID());
    return keys.current.get(selection)!;
  };
  const run = async (action: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    setFailed(false);
    setPending(false);
    try {
      await action();
    } catch {
      if (mounted.current) setFailed(true);
    } finally {
      if (mounted.current) {
        setBusy(false);
        setRevision((value) => value + 1);
      }
    }
  };
  const checkout = (offer: Pick<Offer, "id">, key?: string) =>
    run(async () => {
      const result = await billingCheckout(
        { offer_id: offer.id, operation_key: key ?? operation(offer.id) },
        options,
      );
      if (!mounted.current) return;
      if (result.status !== 200) throw new Error("checkout_failed");
      if (result.data.redirect_url) {
        const url = new URL(result.data.redirect_url);
        if (
          url.protocol !== "https:" ||
          !["sandbox.flow.cl", "www.flow.cl"].includes(url.hostname) ||
          url.username ||
          url.password
        )
          throw new Error("invalid_payment_destination");
        window.location.assign(url.href);
      } else {
        setPending(result.data.state !== "succeeded");
        if (result.data.state === "succeeded") keys.current.delete(offer.id);
        onRefresh();
      }
    });
  const change = (offer?: Offer) =>
    run(async () => {
      const result = await billingChangePreview(
        {
          operation_key: operation("change:" + (offer?.id ?? "cancel")),
          ...(offer ? { offer_id: offer.id } : { cancel: true }),
        },
        options,
      );
      if (!mounted.current) return;
      if (result.status !== 200) throw new Error("preview_failed");
      setPreview(result.data);
    });
  const confirm = () =>
    run(async () => {
      if (!preview) return;
      const result = await billingChangeConfirm({ operation_id: preview.id }, options);
      if (!mounted.current) return;
      if (result.status !== 200) throw new Error("confirmation_failed");
      setPreview(null);
      setPending(true);
      onRefresh();
    });
  return (
    <section aria-label={t("billing.manage")}>
      <h2>{t("billing.manage")}</h2>
      {failed && <p role="alert">{t("billing.commerceError")}</p>}
      {commerce?.reconciliation_required && (
        <p role="alert">{t("billing.invoiceReconciliation")}</p>
      )}
      {pending && <p role="status">{t("billing.awaitingProvider")}</p>}
      <button
        disabled={busy}
        type="button"
        onClick={() =>
          void run(async () => {
            const result = await billingSync(options);
            if (result.status !== 200) throw new Error("sync_failed");
            if (mounted.current) onRefresh();
          })
        }
      >
        {t("billing.verifyPayment")}
      </button>
      {!commerce && !failed && <p role="status">{t("wallet.loading")}</p>}
      {commerce?.offers.length === 0 && <p>{t("billing.noOffers")}</p>}
      {commerce && commerce.offers.length > 0 && (
        <>
          <p>{t("billing.offerPolicy")}</p>
          <div className="wallet-table">
            <table>
              <thead>
                <tr>
                  <th>{t("wallet.plan")}</th>
                  <th>{t("billing.amount")}</th>
                  <th>{t("wallet.balance")}</th>
                  <th>{t("billing.action")}</th>
                </tr>
              </thead>
              <tbody>
                {commerce.offers.map((offer) => (
                  <tr key={offer.id}>
                    <td>
                      {offer.plan_tier
                        ? planLabel(offer.plan_tier)
                        : t(`billing.${offer.product_code}` as Parameters<typeof t>[0])}
                      {offer.billing_cycle && <> · {planLabel(offer.billing_cycle)}</>}
                    </td>
                    <td>CLP {offer.amount}</td>
                    <td>
                      {new Intl.NumberFormat("es-CL").format(offer.credits)}
                      <br />
                      {offer.kind === "pack"
                        ? t("billing.noExpiry")
                        : t("billing.monthlyAllowance")}
                    </td>
                    <td>
                      <button
                        disabled={busy || preview !== null}
                        type="button"
                        onClick={() => {
                          if (subscribed && offer.kind === "subscription") void change(offer);
                          else void checkout(offer);
                        }}
                      >
                        {subscribed && offer.kind === "subscription"
                          ? t("billing.previewChange")
                          : t("billing.buy")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {subscribed && (
        <button disabled={busy || preview !== null} type="button" onClick={() => void change()}>
          {t("billing.cancelAtEnd")}
        </button>
      )}
      {preview && (
        <div role="region" aria-label={t("billing.previewTitle")}>
          <h3>{t("billing.previewTitle")}</h3>
          <p>{preview.product_code ? planLabel(preview.product_code) : t("billing.cancelAtEnd")}</p>
          <p>
            {preview.effective_at
              ? `${t("billing.effectiveAt")}: ${date(preview.effective_at)}`
              : t("billing.immediateUpgrade")}
          </p>
          {preview.amount !== null && (
            <p>
              {t("billing.flowAdjustment")}: {preview.currency} {preview.amount}
            </p>
          )}
          <p>{t("billing.noAutomaticRefund")}</p>
          <button
            disabled={busy || preview.state !== "prepared"}
            type="button"
            onClick={() =>
              void run(async () => {
                const result = await billingChangeAbandon({ operation_id: preview.id }, options);
                if (result.status !== 200) throw new Error("abandon_failed");
                if (mounted.current) {
                  setPreview(null);
                  keys.current.clear();
                }
              })
            }
          >
            {t("billing.abandonChange")}
          </button>
          <button disabled={busy} type="button" onClick={() => void confirm()}>
            {t(preview.state === "prepared" ? "billing.confirmChange" : "billing.verifyPayment")}
          </button>
        </div>
      )}
      {commerce?.scheduled_changes.map((scheduled) => (
        <p role="status" key={scheduled.id}>
          {scheduled.product_code ? planLabel(scheduled.product_code) : t("billing.cancelAtEnd")}
          {scheduled.effective_at &&
            ` · ${t("billing.effectiveAt")}: ${date(scheduled.effective_at)}`}
        </p>
      ))}
      {!!commerce?.checkouts.length && (
        <>
          <h3>{t("billing.recentCheckouts")}</h3>
          <ul>
            {commerce.checkouts.map((purchase) => (
              <li key={purchase.id}>
                {t(`billing.${purchase.product_code}` as Parameters<typeof t>[0])} ·{" "}
                {date(purchase.created_at)}{" "}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void checkout({ id: purchase.offer_id }, purchase.operation_key)}
                >
                  {t("billing.continueCheckout")}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

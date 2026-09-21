import { useEffect, useState } from "react";
import { billingRetrieve } from "../../api/generated/dekopen";
import type { Billing } from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { t } from "../../i18n/es-CL";
import "./billing.css";
import { CommercePanel } from "./CommercePanel";

const label = (value: string) => t(`billing.${value}` as Parameters<typeof t>[0]);
const date = (value: string) =>
  new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeZone: "America/Santiago",
  }).format(new Date(value));

export function BillingPage(): JSX.Element {
  const auth = useAuthSession();
  const org = auth.me?.active_organization;
  if (!org || org.role !== "OWNER") return <p role="alert">{t("wallet.ownerOnly")}</p>;
  return <BillingWorkspace key={`${auth.session?.user.id}:${org.id}`} orgId={org.id} />;
}

function BillingWorkspace({ orgId }: { orgId: string }): JSX.Element {
  const [billing, setBilling] = useState<Billing | null>(null);
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setFailed(false);
    void billingRetrieve({ headers: { "X-Organization-ID": orgId }, signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;
        if (result.status === 200) setBilling(result.data);
        else setFailed(true);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [orgId, revision]);
  return (
    <section className="billing-page">
      <header>
        <h1>{t("billing.title")}</h1>
        <button type="button" onClick={() => setRevision((value) => value + 1)}>
          {t("wallet.refresh")}
        </button>
      </header>
      {failed && <p role="alert">{t("wallet.error")}</p>}
      {!billing && !failed && <p role="status">{t("wallet.loading")}</p>}
      {billing && (
        <>
          <div className="wallet-summary">
            <div>
              <p>{t("wallet.plan")}</p>
              <strong>{label(billing.plan)}</strong>
            </div>
            {billing.plan === "TRIAL" && billing.trial_ends_at && (
              <div>
                <p>{t("wallet.trialEnd")}</p>
                {date(billing.trial_ends_at)}
              </div>
            )}
            {billing.subscription && (
              <div>
                <p>{label(billing.subscription.billing_cycle)}</p>
                <strong>{label(billing.subscription.status)}</strong>
                <p>
                  {billing.subscription.currency} {billing.subscription.amount}
                </p>
                {billing.subscription.current_period_end && (
                  <p>
                    {t("billing.periodEnd")}: {date(billing.subscription.current_period_end)}
                  </p>
                )}
              </div>
            )}
          </div>
          {!billing.subscription && <p>{t("billing.noSubscription")}</p>}
          <CommercePanel
            orgId={orgId}
            subscribed={billing.subscription?.status === "active"}
            onRefresh={() => setRevision((value) => value + 1)}
          />
          <h2>{t("billing.payments")}</h2>
          {billing.payments.length === 0 ? (
            <p>{t("billing.noPayments")}</p>
          ) : (
            <div className="wallet-table">
              <table>
                <thead>
                  <tr>
                    <th>{t("wallet.date")}</th>
                    <th>{t("billing.amount")}</th>
                    <th>{t("billing.status")}</th>
                    <th>{t("billing.receipt")}</th>
                  </tr>
                </thead>
                <tbody>
                  {billing.payments.map((payment) => (
                    <tr key={payment.id}>
                      <td>{date(payment.created_at)}</td>
                      <td>
                        {payment.currency} {payment.amount}
                      </td>
                      <td>{label(payment.status)}</td>
                      <td>{payment.tax_doc_folio ?? t("billing.unavailable")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}

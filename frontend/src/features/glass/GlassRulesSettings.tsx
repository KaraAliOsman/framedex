import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { catalogGlassRules, catalogGlassRulesReplace } from "../../api/generated/dekopen";
import { decimalInputValue, parseDecimalInput } from "../../decimal";
import { glassError } from "./glassErrors";
import { t } from "../../i18n/es-CL";
import "./glass.css";
import { LoadingState } from "../../ui/States";

type Rule = {
  code: string;
  name: string;
  zone: "DOOR" | "SIDELIGHT" | "LOW_PANE" | "LARGE_PANE";
  source: string;
  synthetic: boolean;
  mandatory: boolean;
  required_classes?: ("A" | "B" | "C")[];
  maximum_sill_mm?: string | null;
  minimum_area_m2?: string | null;
};
const ZONES: [Rule["zone"], string][] = [
  ["DOOR", "Puerta vidriada"],
  ["SIDELIGHT", "Paño lateral de puerta"],
  ["LOW_PANE", "Paño bajo"],
  ["LARGE_PANE", "Gran ventanal"],
];
export function GlassRulesSettings({ orgId, canWrite }: { orgId: string; canWrite: boolean }) {
  const query = useQuery({
    queryKey: ["glass-rules", orgId],
    retry: false,
    queryFn: async () => {
      const response = await catalogGlassRules();
      if (response.status !== 200) throw new Error("glass_rules_load");
      return response.data;
    },
  });
  const [draft, setDraft] = useState<Rule[] | null>(null);
  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [previous, setPrevious] = useState<Rule[] | null>(null);
  const items = draft ?? (query.data?.items as Rule[] | undefined) ?? [];
  function change(next: Rule[]) {
    setDraft(next);
    setReview(false);
    setMessage(null);
  }
  function patch(index: number, value: Partial<Rule>) {
    change(items.map((item, i) => (i === index ? { ...item, ...value } : item)));
  }
  async function apply(payload: Rule[]) {
    if (!query.data) return;
    setBusy(true);
    setMessage(null);
    try {
      const response = await catalogGlassRulesReplace(
        { items: payload },
        { headers: { "If-Match": `"${query.data.revision}"` } },
      );
      if (response.status !== 200) throw new Error("glass_rules_save");
      setPrevious(query.data.items as Rule[]);
      await query.refetch();
      setDraft(null);
      setReview(false);
      setMessage(t("glass.rulesSaved"));
    } catch (error) {
      setMessage(glassError(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="settings-group glass-rules" aria-labelledby="glass-rules-title">
      <h2 id="glass-rules-title" className="settings-group__title">
        {t("glass.rulesTitle")}
      </h2>
      <p>{t("glass.rulesHelp")}</p>
      <Link to="/catalogs">{t("glass.rulesImport")}</Link>
      {query.isPending ? (
        <LoadingState label={t("glass.rulesLoading")} />
      ) : query.isError ? (
        <div role="alert">
          <p>{glassError(query.error)}</p>
          <button type="button" className="ghost-button" onClick={() => void query.refetch()}>
            {t("glass.retry")}
          </button>
        </div>
      ) : (
        <>
          {!items.length && <p>{t("glass.rulesEmpty")}</p>}
          {!canWrite && <p>{t("glass.rulesRole")}</p>}
          <fieldset className="glass-edit-fields" disabled={!canWrite || busy}>
            {items.map((rule, index) => (
              <div className="glass-rule" key={index}>
                <div className="glass-rule-fields">
                  <label className="glass-field">
                    <span>{t("glass.ruleCode")}</span>
                    <input
                      value={rule.code}
                      onChange={(event) => patch(index, { code: event.target.value })}
                    />
                  </label>
                  <label className="glass-field">
                    <span>{t("glass.ruleName")}</span>
                    <input
                      value={rule.name}
                      onChange={(event) => patch(index, { name: event.target.value })}
                    />
                  </label>
                  <label className="glass-field">
                    <span>{t("glass.zone")}</span>
                    <select
                      value={rule.zone}
                      onChange={(event) =>
                        patch(index, { zone: event.target.value as Rule["zone"] })
                      }
                    >
                      {ZONES.map(([value, label]) => (
                        <option value={value} key={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="glass-field">
                    <span>{t("glass.ruleSource")}</span>
                    <input
                      value={rule.source}
                      onChange={(event) => patch(index, { source: event.target.value })}
                    />
                  </label>
                  {rule.zone === "LOW_PANE" && (
                    <label className="glass-field">
                      <span>{t("glass.sillLimit")}</span>
                      <input
                        inputMode="decimal"
                        value={decimalInputValue(rule.maximum_sill_mm)}
                        onChange={(event) =>
                          patch(index, {
                            maximum_sill_mm:
                              parseDecimalInput(event.target.value) ?? event.target.value,
                          })
                        }
                      />
                    </label>
                  )}
                  {rule.zone === "LARGE_PANE" && (
                    <label className="glass-field">
                      <span>{t("glass.areaLimit")}</span>
                      <input
                        inputMode="decimal"
                        value={decimalInputValue(rule.minimum_area_m2)}
                        onChange={(event) =>
                          patch(index, {
                            minimum_area_m2:
                              parseDecimalInput(event.target.value, 4) ?? event.target.value,
                          })
                        }
                      />
                    </label>
                  )}
                </div>
                <div className="glass-actions" role="group" aria-label={t("glass.requiredClasses")}>
                  {(["A", "B", "C"] as const).map((value) => (
                    <label className="glass-check" key={value}>
                      <input
                        type="checkbox"
                        checked={(rule.required_classes ?? ["A", "B", "C"]).includes(value)}
                        onChange={(event) => {
                          const classes = rule.required_classes ?? ["A", "B", "C"];
                          patch(index, {
                            required_classes: event.target.checked
                              ? [...classes, value]
                              : classes.filter((item) => item !== value),
                          });
                        }}
                      />
                      {t("glass.class")} {value}
                    </label>
                  ))}
                </div>
                <label className="glass-check">
                  <input
                    type="checkbox"
                    checked={rule.mandatory}
                    onChange={(event) => patch(index, { mandatory: event.target.checked })}
                  />
                  {t("glass.mandatory")}
                </label>
                <label className="glass-check">
                  <input
                    type="checkbox"
                    checked={rule.synthetic}
                    onChange={(event) => patch(index, { synthetic: event.target.checked })}
                  />
                  {t("glass.synthetic")}
                </label>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => change(items.filter((_, i) => i !== index))}
                >
                  {t("glass.removeRule")}
                </button>
              </div>
            ))}
          </fieldset>
          {canWrite && (
            <div className="glass-actions">
              <button
                type="button"
                className="ghost-button"
                disabled={busy || items.length >= 200}
                onClick={() =>
                  change([
                    ...items,
                    {
                      code: "",
                      name: "",
                      zone: "DOOR",
                      source: "",
                      synthetic: false,
                      mandatory: false,
                    },
                  ])
                }
              >
                {t("glass.addRule")}
              </button>
              <button
                type="button"
                className="ghost-button"
                disabled={busy}
                onClick={() => change(query.data!.examples as Rule[])}
              >
                {t("glass.examples")}
              </button>
            </div>
          )}
          {draft !== null && !review && (
            <button
              type="button"
              className="ghost-button"
              disabled={busy}
              onClick={() => setReview(true)}
            >
              {t("glass.reviewRules")}
            </button>
          )}
          {draft !== null && review && (
            <div className="glass-publication">
              <h3>{t("glass.rulesDiff")}</h3>
              <p>{t("glass.rulesConsequence")}</p>
              <dl className="glass-facts">
                <div>
                  <dt>{t("glass.before")}</dt>
                  <dd>
                    {(query.data?.items as Rule[])
                      .map(
                        (rule) =>
                          `${rule.name} · ${rule.mandatory ? t("glass.blocked") : t("glass.notice")}`,
                      )
                      .join("; ") || t("glass.rulesEmpty")}
                  </dd>
                </div>
                <div>
                  <dt>{t("glass.after")}</dt>
                  <dd>
                    {items
                      .map(
                        (rule) =>
                          `${rule.name} · ${rule.mandatory ? t("glass.blocked") : t("glass.notice")} · ${rule.source}`,
                      )
                      .join("; ") || t("glass.rulesEmpty")}
                  </dd>
                </div>
              </dl>
              <button
                type="button"
                className="primary-action"
                disabled={busy}
                onClick={() => void apply(items)}
              >
                {t("glass.applyRules")}
              </button>
              <button
                type="button"
                className="ghost-button"
                disabled={busy}
                onClick={() => {
                  setDraft(null);
                  setReview(false);
                }}
              >
                {t("glass.discard")}
              </button>
            </div>
          )}
          {previous && (
            <button
              type="button"
              className="ghost-button"
              disabled={busy}
              onClick={() => {
                change(previous);
                setReview(true);
                setPrevious(null);
              }}
            >
              {t("glass.undoRules")}
            </button>
          )}
        </>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}

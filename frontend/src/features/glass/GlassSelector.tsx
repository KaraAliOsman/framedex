import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { glassError } from "./glassErrors";
import { catalogGlassVariantPublish } from "../../api/generated/dekopen";
import type {
  DesignOptions,
  GlassPreviewOutput,
  GlassSpecChoice,
} from "../../api/generated/models";
import { useAuthSession } from "../../auth/AuthSessionProvider";
import { decimalInputValue, parseDecimalInput, formatDecimal, formatMoney } from "../../decimal";
import { t } from "../../i18n/es-CL";
import { fmtMm } from "../../format";
import { Dialog } from "../../ui/Dialog";
import { LoadingState } from "../../ui/States";
import type { IntentNode } from "../canvas/intentEditing";
import {
  asGlassProduct,
  glassChoicePatch,
  newPane,
  newPly,
  NO_PROCESSING,
  type GlassProduct,
  type GlassPly,
  type Pane,
  type SupplierDatum,
} from "./glassModel";
import { requestGlassPreview, type GlassContext } from "./useGlassPreview";
import "./glass.css";

const PLY_TYPES: [GlassPly["type"], string][] = [
  ["FLOAT", "Float incoloro"],
  ["TEMPERED", "Templado"],
  ["HEAT_STRENGTHENED", "Termoendurecido"],
  ["LOW_E", "Low-E"],
  ["SOLAR", "Control solar"],
  ["REFLECTIVE", "Reflectivo"],
  ["MIRROR", "Espejo"],
  ["SATIN", "Satinado / arenado"],
  ["PRINTED", "Impreso"],
];
const COLORS: [GlassPly["color"], string][] = [
  ["CLEAR", "Incoloro"],
  ["BRONZE", "Bronce"],
  ["GREY", "Gris"],
  ["GREEN", "Verde"],
];
function Field({
  label,
  value,
  onChange,
  decimal = false,
}: {
  label: string;
  value: string | null | undefined;
  onChange(value: string): void;
  decimal?: boolean;
}) {
  return (
    <label className="glass-field">
      <span>{label}</span>
      <input
        value={decimal ? decimalInputValue(value) : (value ?? "")}
        title={value ?? undefined}
        inputMode={decimal ? "decimal" : undefined}
        onChange={(event) =>
          onChange(
            decimal
              ? (parseDecimalInput(event.target.value, 6) ?? event.target.value)
              : event.target.value,
          )
        }
      />
    </label>
  );
}
function Findings({ preview }: { preview: GlassPreviewOutput | undefined }) {
  return preview?.findings.length ? (
    <ul className="glass-findings" aria-label={t("glass.findings")}>
      {preview.findings.map((finding) => (
        <li key={finding.code} data-blocking={finding.blocking}>
          <strong>{finding.blocking ? t("glass.blocked") : t("glass.notice")}</strong> ·{" "}
          {finding.message}
          {finding.synthetic ? ` · ${t("glass.demo")}` : ""}
          {finding.source && <small>{finding.source}</small>}
        </li>
      ))}
    </ul>
  ) : null;
}
function Section({ preview }: { preview: GlassPreviewOutput | undefined }) {
  if (!preview) return null;
  if (preview.section_error || !preview.total_thickness_mm)
    return <p role="status">{preview.section_error ?? t("glass.sectionUnknown")}</p>;
  // Conversion only supplies SVG coordinates. All lengths/positions are engine outputs.
  const width = Number(preview.total_thickness_mm);
  return (
    <figure className="glass-section">
      <figcaption>{t("glass.section")}</figcaption>
      <div className="glass-section__ends">
        <span>{t("glass.exterior")}</span>
        <span>{t("glass.interior")}</span>
      </div>
      <svg
        viewBox={`0 0 ${width} 20`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`${t("glass.section")}: ${preview.notation}`}
      >
        {preview.section.map((part, i) => (
          <rect
            key={i}
            x={Number(part.x_mm)}
            y={1}
            width={Number(part.width_mm)}
            height={18}
            className={`glass-section__${part.kind.toLowerCase()}`}
          >
            <title>
              {part.label} · {fmtMm(part.width_mm)} mm
            </title>
          </rect>
        ))}
      </svg>
      <ol>
        {preview.section.map((part, i) => (
          <li key={i}>
            {part.label} · <span className="glass-number">{fmtMm(part.width_mm)} mm</span>
          </li>
        ))}
      </ol>
    </figure>
  );
}
function RecipeEditor({
  product,
  onChange,
}: {
  product: GlassProduct;
  onChange(product: GlassProduct): void;
}) {
  function updateLayer(index: number, value: GlassProduct["composition"]["layers"][number]) {
    onChange({
      ...product,
      authority_id: null,
      composition: {
        layers: product.composition.layers.map((layer, i) => (i === index ? value : layer)),
      },
    });
  }
  function updatePane(index: number, pane: Pane, plyIndex: number, patch: Partial<GlassPly>) {
    updateLayer(index, {
      ...pane,
      plies: pane.plies.map((ply, i) => (i === plyIndex ? { ...ply, ...patch } : ply)),
    });
  }
  return (
    <div className="glass-recipe">
      <Field
        label={t("glass.name")}
        value={product.name}
        onChange={(name) => onChange({ ...product, name, authority_id: null })}
      />
      <Field
        label={t("glass.source")}
        value={product.source}
        onChange={(source) => onChange({ ...product, source, authority_id: null })}
      />
      <label className="glass-check">
        <input
          type="checkbox"
          checked={product.synthetic}
          onChange={(event) =>
            onChange({ ...product, synthetic: event.target.checked, authority_id: null })
          }
        />
        {t("glass.synthetic")}
      </label>
      <p className="glass-help">{t("glass.layerOrder")}</p>
      {product.composition.layers.map((layer, index) => (
        <fieldset key={index} className="glass-layer">
          <legend>
            {layer.kind === "PANE" ? t("glass.pane") : t("glass.chamber")} {index + 1}
          </legend>
          {layer.kind === "PANE" ? (
            <>
              {layer.plies.map((ply, pi) => (
                <div className="glass-layer__fields" key={pi}>
                  <Field
                    label={t("glass.plyThickness")}
                    value={ply.thickness_mm}
                    decimal
                    onChange={(thickness_mm) => updatePane(index, layer, pi, { thickness_mm })}
                  />
                  <label className="glass-field">
                    <span>{t("glass.type")}</span>
                    <select
                      value={ply.type}
                      title={PLY_TYPES.find(([type]) => type === ply.type)?.[1]}
                      onChange={(event) =>
                        updatePane(index, layer, pi, {
                          type: event.target.value as GlassPly["type"],
                        })
                      }
                    >
                      {PLY_TYPES.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="glass-field">
                    <span>{t("glass.color")}</span>
                    <select
                      value={ply.color}
                      onChange={(event) =>
                        updatePane(index, layer, pi, {
                          color: event.target.value as GlassPly["color"],
                        })
                      }
                    >
                      {COLORS.map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Field
                    label={t("glass.supplierSku")}
                    value={ply.supplier_sku}
                    onChange={(supplier_sku) =>
                      updatePane(index, layer, pi, { supplier_sku: supplier_sku || null })
                    }
                  />
                  {(ply.type === "LOW_E" || ply.type === "SOLAR" || ply.type === "REFLECTIVE") && (
                    <Field
                      label={t("glass.coatingFace")}
                      value={ply.coating_face?.toString()}
                      decimal
                      onChange={(value) =>
                        updatePane(index, layer, pi, { coating_face: value ? Number(value) : null })
                      }
                    />
                  )}
                </div>
              ))}
              {layer.interlayers.map((pvb, pi) => (
                <div className="glass-layer__fields" key={`pvb${pi}`}>
                  <label className="glass-field">
                    <span>{t("glass.interlayer")}</span>
                    <select
                      value={pvb.type}
                      onChange={(event) =>
                        updateLayer(index, {
                          ...layer,
                          interlayers: layer.interlayers.map((item, i) =>
                            i === pi
                              ? { ...item, type: event.target.value as "PVB" | "ACOUSTIC_PVB" }
                              : item,
                          ),
                        })
                      }
                    >
                      <option value="PVB">PVB</option>
                      <option value="ACOUSTIC_PVB">{t("glass.acousticPvb")}</option>
                    </select>
                  </label>
                  <Field
                    label={t("glass.pvbThickness")}
                    value={pvb.thickness_mm}
                    decimal
                    onChange={(value) =>
                      updateLayer(index, {
                        ...layer,
                        interlayers: layer.interlayers.map((item, i) =>
                          i === pi ? { ...item, thickness_mm: value || null } : item,
                        ),
                      })
                    }
                  />
                  <Field
                    label={t("glass.pvbDensity")}
                    value={pvb.density_kg_m3}
                    decimal
                    onChange={(value) =>
                      updateLayer(index, {
                        ...layer,
                        interlayers: layer.interlayers.map((item, i) =>
                          i === pi ? { ...item, density_kg_m3: value || null } : item,
                        ),
                      })
                    }
                  />
                  <Field
                    label={t("glass.pvbSource")}
                    value={pvb.source}
                    onChange={(value) =>
                      updateLayer(index, {
                        ...layer,
                        interlayers: layer.interlayers.map((item, i) =>
                          i === pi ? { ...item, source: value || null } : item,
                        ),
                      })
                    }
                  />
                </div>
              ))}
              <div className="glass-actions">
                <button
                  type="button"
                  className="ghost-button"
                  disabled={layer.plies.length >= 6}
                  onClick={() =>
                    updateLayer(index, {
                      ...layer,
                      plies: [...layer.plies, newPly()],
                      interlayers: [
                        ...layer.interlayers,
                        { thickness_mm: null, type: "PVB", density_kg_m3: null, source: null },
                      ],
                    })
                  }
                >
                  {t("glass.addPly")}
                </button>
                {layer.plies.length > 1 && (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() =>
                      updateLayer(index, {
                        ...layer,
                        plies: layer.plies.slice(0, -1),
                        interlayers: layer.interlayers.slice(0, -1),
                      })
                    }
                  >
                    {t("glass.removePly")}
                  </button>
                )}
              </div>
            </>
          ) : (
            <div className="glass-layer__fields">
              <Field
                label={t("glass.chamberWidth")}
                value={layer.width_mm}
                decimal
                onChange={(width_mm) => updateLayer(index, { ...layer, width_mm })}
              />
              <label className="glass-field">
                <span>{t("glass.gas")}</span>
                <select
                  value={layer.gas ?? ""}
                  onChange={(event) =>
                    updateLayer(index, {
                      ...layer,
                      gas: (event.target.value as "AIR" | "ARGON") || null,
                    })
                  }
                >
                  <option value="">{t("glass.unknown")}</option>
                  <option value="AIR">{t("glass.air")}</option>
                  <option value="ARGON">{t("glass.argon")}</option>
                </select>
              </label>
              <label className="glass-field">
                <span>{t("glass.spacer")}</span>
                <select
                  value={layer.spacer ?? ""}
                  onChange={(event) =>
                    updateLayer(index, {
                      ...layer,
                      spacer: (event.target.value as "ALUMINIUM" | "WARM_EDGE") || null,
                    })
                  }
                >
                  <option value="">{t("glass.unknown")}</option>
                  <option value="ALUMINIUM">{t("glass.aluminium")}</option>
                  <option value="WARM_EDGE">{t("glass.warmEdge")}</option>
                </select>
              </label>
              <Field
                label={t("glass.sealant")}
                value={layer.sealant}
                onChange={(sealant) => updateLayer(index, { ...layer, sealant: sealant || null })}
              />
            </div>
          )}
        </fieldset>
      ))}
      <div className="glass-actions">
        <button
          type="button"
          className="ghost-button"
          disabled={product.composition.layers.length >= 11}
          onClick={() =>
            onChange({
              ...product,
              authority_id: null,
              composition: {
                layers: [
                  ...product.composition.layers,
                  { kind: "CHAMBER", width_mm: "", gas: null, spacer: null, sealant: null },
                  newPane(),
                ],
              },
            })
          }
        >
          {t("glass.addChamber")}
        </button>
        {product.composition.layers.length > 1 && (
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              onChange({
                ...product,
                authority_id: null,
                composition: { layers: product.composition.layers.slice(0, -2) },
              })
            }
          >
            {t("glass.removeChamber")}
          </button>
        )}
      </div>
      <details>
        <summary>{t("glass.supplierData")}</summary>
        <p className="glass-help">{t("glass.supplierDataHelp")}</p>
        {(
          [
            ["ug", "Ug · W/(m²·K)"],
            ["solar_factor", "g · factor solar (0–1)"],
            ["light_transmittance", "Transmisión luminosa (0–1)"],
            ["weight_kg_m2", "Peso declarado · kg/m²"],
          ] as const
        ).map(([key, label]) => (
          <div className="glass-layer__fields" key={key}>
            <Field
              label={label}
              value={product.properties[key]?.value}
              decimal
              onChange={(value) =>
                onChange({
                  ...product,
                  authority_id: null,
                  properties: {
                    ...product.properties,
                    [key]: value ? { value, source: product.properties[key]?.source ?? "" } : null,
                  },
                })
              }
            />
            <Field
              label={t("glass.datumSource")}
              value={product.properties[key]?.source}
              onChange={(source) => {
                const datum = product.properties[key];
                if (datum)
                  onChange({
                    ...product,
                    authority_id: null,
                    properties: { ...product.properties, [key]: { ...datum, source } },
                  });
              }}
            />
          </div>
        ))}
        <label className="glass-field">
          <span>{t("glass.safetyClass")}</span>
          <select
            value={product.properties.safety_class?.value ?? ""}
            onChange={(event) =>
              onChange({
                ...product,
                authority_id: null,
                properties: {
                  ...product.properties,
                  safety_class: event.target.value
                    ? {
                        value: event.target.value as "A" | "B" | "C",
                        source: product.properties.safety_class?.source ?? "",
                      }
                    : null,
                },
              })
            }
          >
            <option value="">{t("glass.unknown")}</option>
            {["A", "B", "C"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <Field
          label={t("glass.datumSource")}
          value={product.properties.safety_class?.source}
          onChange={(source) => {
            const datum = product.properties.safety_class;
            if (datum)
              onChange({
                ...product,
                authority_id: null,
                properties: { ...product.properties, safety_class: { ...datum, source } },
              });
          }}
        />
      </details>
      <details>
        <summary>{t("glass.limits")}</summary>
        {(
          [
            ["min_width_mm", "Ancho mínimo · mm"],
            ["max_width_mm", "Ancho máximo · mm"],
            ["min_height_mm", "Alto mínimo · mm"],
            ["max_height_mm", "Alto máximo · mm"],
            ["max_area_m2", "Área máxima · m²"],
            ["max_aspect_ratio", "Relación máxima entre lados"],
          ] as const
        ).map(([key, label]) => (
          <Field
            key={key}
            label={label}
            value={product.limits[key]}
            decimal
            onChange={(value) =>
              onChange({
                ...product,
                authority_id: null,
                limits: { ...product.limits, [key]: value || null },
              })
            }
          />
        ))}
        <Field
          label={t("glass.source")}
          value={product.limits.source}
          onChange={(source) =>
            onChange({ ...product, authority_id: null, limits: { ...product.limits, source } })
          }
        />
      </details>
      <details>
        <summary>{t("glass.billing")}</summary>
        <Field
          label={t("glass.minimumArea")}
          value={product.billing.minimum_area_m2 ?? "0"}
          decimal
          onChange={(value) =>
            onChange({
              ...product,
              authority_id: null,
              billing: { ...product.billing, minimum_area_m2: value },
            })
          }
        />
        {(
          [
            ["tempering_sku", "Tarifa de templado"],
            ["polishing_sku", "Tarifa de canto pulido"],
            ["drilling_sku", "Tarifa de perforación"],
            ["bars_per_m_sku", "Tarifa de palillaje por metro"],
            ["bars_per_crossing_sku", "Tarifa por cruce de palillaje"],
          ] as const
        ).map(([key, label]) => (
          <Field
            key={key}
            label={label}
            value={product.billing[key]}
            onChange={(value) =>
              onChange({
                ...product,
                authority_id: null,
                billing: { ...product.billing, [key]: value || null },
              })
            }
          />
        ))}
        <Field
          label={t("glass.source")}
          value={product.billing.source}
          onChange={(source) =>
            onChange({ ...product, authority_id: null, billing: { ...product.billing, source } })
          }
        />
      </details>
    </div>
  );
}

export function GlassSelector({
  options,
  choices,
  node,
  context,
  busy,
  onPatch,
  compact = false,
}: {
  options?: DesignOptions;
  choices: GlassSpecChoice[];
  node: IntentNode;
  context: GlassContext;
  busy: boolean;
  onPatch(patch: Partial<IntentNode>): void;
  compact?: boolean;
}) {
  const auth = useAuthSession();
  const orgId = auth.me?.active_organization?.id;
  const canPublish = ["OWNER", "WORKSHOP_MANAGER"].includes(
    auth.me?.active_organization?.role ?? "",
  );
  const queryClient = useQueryClient();
  const [published, setPublished] = useState<GlassSpecChoice[]>([]);
  const allChoices = [
    ...choices,
    ...published.filter((item) => !choices.some((choice) => choice.sku === item.sku)),
  ];
  const selected = allChoices.find((choice) => choice.sku === node.glass_article_sku);
  const chosenProduct = node.glass_product ?? asGlassProduct(selected?.product);
  const [advanced, setAdvanced] = useState(false);
  const [draft, setDraft] = useState<GlassProduct | null>(
    chosenProduct ? structuredClone(chosenProduct) : null,
  );
  const [delayedDraft, setDelayedDraft] = useState(draft);
  const [sku, setSku] = useState("");
  const [purchaseSku, setPurchaseSku] = useState("");
  const [supplier, setSupplier] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [review, setReview] = useState(false);
  const [composing, setComposing] = useState(false);
  useEffect(() => {
    setDraft(chosenProduct ? structuredClone(chosenProduct) : null);
    setReview(false);
  }, [node.glass_product, selected?.product]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    setReview(false);
    const timer = setTimeout(() => setDelayedDraft(draft), 220);
    return () => clearTimeout(timer);
  }, [draft]);
  const catalog = useQuery({
    queryKey: [
      "glass-selector",
      orgId,
      options?.system_id,
      allChoices,
      context,
      node.glass_processing,
    ],
    enabled: !!options,
    retry: false,
    queryFn: async ({ signal }) =>
      Object.fromEntries(
        await Promise.all(
          allChoices
            .filter((choice) => choice.product && choice.compatible !== false)
            .map(
              async (choice) =>
                [
                  choice.sku,
                  await requestGlassPreview(
                    {
                      system_id: options!.system_id,
                      product: choice.product,
                      technical_sku: choice.sku,
                      processing: node.glass_processing ?? {},
                      ...context,
                    },
                    signal,
                  ),
                ] as const,
            ),
        ),
      ) as Record<string, GlassPreviewOutput>,
  });
  const preview = useQuery({
    queryKey: ["glass-compositor", orgId, options?.system_id, delayedDraft, context],
    enabled: advanced && !!options && !!delayedDraft,
    retry: false,
    queryFn: ({ signal }) =>
      requestGlassPreview(
        { system_id: options!.system_id, product: delayedDraft!, ...context },
        signal,
      ),
  });
  const selectedPreview = selected ? catalog.data?.[selected.sku] : undefined;
  const visible = allChoices.filter(
    (choice) =>
      choice.sku === selected?.sku ||
      (choice.compatible !== false &&
        !catalog.data?.[choice.sku]?.findings.some((finding) => finding.blocking)),
  );
  function changeDraft(value: GlassProduct) {
    setDraft(value);
    setMessage(null);
  }
  async function publish() {
    if (!options || !draft || !review || !sku.trim() || !purchaseSku.trim() || !supplier.trim())
      return;
    setPublishing(true);
    setMessage(null);
    try {
      const response = await catalogGlassVariantPublish({
        system_id: options.system_id,
        technical_sku: sku.trim(),
        purchasing_sku: purchaseSku.trim(),
        manufacturer_name: supplier.trim(),
        version: 1,
        product: draft,
        confirmed: true,
      });
      if (response.status !== 201) throw new Error("glass_publish_failed");
      const result = response.data;
      const choice: GlassSpecChoice = {
        sku: result.technical_sku,
        spec: result.spec,
        product: result.product,
        total_thickness_mm: preview.data?.total_thickness_mm,
        weight_kg_m2: preview.data?.weight_kg_m2,
        compatible: true,
        relative_price: t("glass.pricePending"),
      };
      setPublished((items) => [...items, choice]);
      onPatch(glassChoicePatch(choice));
      await queryClient.invalidateQueries({ queryKey: ["project-design-options"] });
      setReview(false);
      setComposing(false);
      setMessage(t("glass.published"));
    } catch (error) {
      setMessage(glassError(error));
    } finally {
      setPublishing(false);
    }
  }
  const processing = node.glass_processing ?? NO_PROCESSING;
  return (
    <section
      className={`glass-selector${compact ? " glass-selector--compact" : ""}`}
      aria-label={t("glass.selector")}
      aria-busy={catalog.isFetching}
    >
      {!options ? (
        <p role="status">{t("glass.loading")}</p>
      ) : catalog.isError ? (
        <div role="alert">
          <p>{glassError(catalog.error)}</p>
          <button type="button" className="ghost-button" onClick={() => void catalog.refetch()}>
            {t("glass.retry")}
          </button>
        </div>
      ) : catalog.isPending ? (
        <LoadingState label={t("glass.checking")} />
      ) : visible.length === 0 ? (
        <p>
          {t("glass.empty")} <Link to="/catalogs">{t("glass.openCatalog")}</Link>
        </p>
      ) : compact ? (
        <label className="assembly-field">
          <span>Vidrio</span>
          <select
            aria-label="Vidrio"
            disabled={busy || catalog.isFetching}
            value={selected?.sku ?? ""}
            onChange={(event) => {
              const choice = visible.find((item) => item.sku === event.target.value);
              if (choice) onPatch(glassChoicePatch(choice));
            }}
          >
            <option value="">Elige un vidrio compatible</option>
            {visible.map((choice) => (
              <option
                key={choice.sku}
                value={choice.sku}
                disabled={
                  !choice.product ||
                  choice.compatible === false ||
                  catalog.data?.[choice.sku]?.findings.some((finding) => finding.blocking)
                }
              >
                {asGlassProduct(choice.product)?.name ?? choice.spec}
                {asGlassProduct(choice.product)?.synthetic ? " · DEMO" : ""}
              </option>
            ))}
          </select>
        </label>
      ) : (
        <div className="glass-products" role="group" aria-label={t("glass.compatible")}>
          {visible.map((choice) => {
            const product = asGlassProduct(choice.product);
            const check = catalog.data?.[choice.sku];
            const blocked =
              !product ||
              choice.compatible === false ||
              check?.findings.some((finding) => finding.blocking);
            return (
              <button
                type="button"
                key={choice.sku}
                data-glass-sku={choice.sku}
                className="glass-product"
                aria-pressed={choice.sku === node.glass_article_sku}
                disabled={busy || blocked || catalog.isFetching}
                onClick={() => onPatch(glassChoicePatch(choice))}
              >
                <strong>{product?.name ?? choice.spec ?? t("glass.reviewRequired")}</strong>
                <span className="glass-number">
                  {fmtMm(choice.total_thickness_mm)} mm · {formatDecimal(choice.weight_kg_m2, 1)}{" "}
                  kg/m²
                </span>
                <small>
                  {choice.relative_price || t("glass.pricePending")}
                  {product?.synthetic ? ` · ${t("glass.demo")}` : ""}
                </small>
                {blocked && (
                  <small>
                    {choice.review_reason ||
                      check?.findings.find((finding) => finding.blocking)?.message ||
                      t("glass.reviewRequired")}
                  </small>
                )}
              </button>
            );
          })}
        </div>
      )}
      {!node.glass_article_sku && <p className="glass-help">{t("glass.choose")}</p>}
      <Findings preview={selectedPreview} />
      {selectedPreview?.findings.some((finding) => finding.code !== "tempered_exact") &&
        selectedPreview.alternative_skus
          .map((alternative) => {
            const choice = allChoices.find((item) => item.sku === alternative);
            return choice ? (
              <button
                className="ghost-button"
                type="button"
                key={alternative}
                disabled={busy}
                onClick={() => onPatch(glassChoicePatch(choice))}
              >
                {t("glass.useAlternative")} {asGlassProduct(choice.product)?.name ?? choice.spec}
              </button>
            ) : null;
          })
          .slice(0, 1)}
      <details open={advanced} onToggle={(event) => setAdvanced(event.currentTarget.open)}>
        <summary>{t("glass.advanced")}</summary>
        <Section preview={preview.data} />
        {preview.isFetching && <LoadingState label={t("glass.validating")} />}
        {preview.isError && <p role="alert">{glassError(preview.error)}</p>}
        {chosenProduct && (
          <details>
            <summary>{t("glass.whereFrom")}</summary>
            <p>{chosenProduct.source}</p>
            <p>{t("glass.derivation")}</p>
            <dl className="glass-facts">
              <div>
                <dt>Peso exacto del motor</dt>
                <dd className="glass-number">{fmtMm(selectedPreview?.weight_kg_m2)} kg/m²</dd>
              </div>
              <div>
                <dt>{t("glass.cut")}</dt>
                <dd className="glass-number">
                  {context.width_mm && context.height_mm
                    ? `${fmtMm(context.width_mm)} × ${fmtMm(context.height_mm)} mm`
                    : t("glass.cutPending")}
                </dd>
              </div>
              {(
                [
                  ["ug", "Ug · W/(m²·K)"],
                  ["solar_factor", "g"],
                  ["light_transmittance", "Transmisión luminosa"],
                ] as const
              ).map(([key, label]) => {
                const datum: SupplierDatum | null | undefined = chosenProduct.properties[key];
                return (
                  <div key={key}>
                    <dt>{label}</dt>
                    <dd>
                      {datum ? (
                        <>
                          <span className="glass-number">{formatDecimal(datum.value, 2)}</span> ·{" "}
                          {datum.source}
                        </>
                      ) : (
                        t("glass.supplierUnknown")
                      )}
                    </dd>
                  </div>
                );
              })}
            </dl>
          </details>
        )}
        <label className="glass-field">
          <span>{t("glass.sill")}</span>
          <input
            inputMode="decimal"
            value={decimalInputValue(node.sill_height_mm)}
            disabled={busy}
            onChange={(event) => {
              const value = parseDecimalInput(event.target.value);
              if (value !== null || !event.target.value) onPatch({ sill_height_mm: value });
            }}
          />
        </label>
        <label className="glass-check">
          <input
            type="checkbox"
            checked={node.is_sidelight ?? false}
            disabled={busy}
            onChange={(event) => onPatch({ is_sidelight: event.target.checked })}
          />
          {t("glass.sidelight")}
        </label>
        <details>
          <summary>{t("glass.processing")}</summary>
          <div className="glass-actions">
            {(
              [
                ["TOP", "Superior"],
                ["BOTTOM", "Inferior"],
                ["LEFT", "Izquierdo"],
                ["RIGHT", "Derecho"],
              ] as const
            ).map(([edge, label]) => (
              <label className="glass-check" key={edge}>
                <input
                  type="checkbox"
                  disabled={busy}
                  checked={processing.polished_edges.includes(edge)}
                  onChange={(event) =>
                    onPatch({
                      glass_processing: {
                        ...processing,
                        polished_edges: event.target.checked
                          ? [...processing.polished_edges, edge]
                          : processing.polished_edges.filter((value) => value !== edge),
                      },
                    })
                  }
                />
                {t("glass.polish")} {label.toLowerCase()}
              </label>
            ))}
          </div>
          {(
            [
              ["holes", "Perforaciones"],
              ["bars_vertical", "Palillos verticales"],
              ["bars_horizontal", "Palillos horizontales"],
            ] as const
          ).map(([key, label]) => (
            <label className="glass-field" key={key}>
              <span>{label}</span>
              <input
                inputMode="numeric"
                value={processing[key]}
                disabled={busy}
                onChange={(event) => {
                  if (/^\d{0,3}$/.test(event.target.value))
                    onPatch({
                      glass_processing: { ...processing, [key]: Number(event.target.value) },
                    });
                }}
              />
            </label>
          ))}
          {selectedPreview?.price_error && <p role="status">{selectedPreview.price_error}</p>}
          {selectedPreview?.price != null && (
            <details>
              <summary>{t("glass.billable")}</summary>
              <p className="glass-number">
                {formatDecimal(
                  (selectedPreview.price as { billable_area_m2: string }).billable_area_m2,
                  2,
                )}{" "}
                m²
              </p>
              {auth.me?.active_organization?.role === "OWNER" && (
                <p className="glass-number">
                  {formatMoney((selectedPreview.price as { total_cost: string }).total_cost)}
                </p>
              )}
              <p>{chosenProduct?.billing.source ?? t("glass.noMinimum")}</p>
            </details>
          )}
        </details>
        {draft ? (
          <>
            <button type="button" className="ghost-button" onClick={() => setComposing(true)}>
              {t("glass.compose")}
            </button>
            {composing && (
              <Dialog
                title={t("glass.compose")}
                width="l"
                onClose={() => {
                  setComposing(false);
                  setReview(false);
                }}
              >
                <div className="glass-composer">
                  <Section preview={preview.data} />
                  <fieldset className="glass-edit-fields" disabled={busy || !canPublish}>
                    <RecipeEditor product={draft} onChange={changeDraft} />
                  </fieldset>
                  {!canPublish ? (
                    <p>{t("glass.publishRole")}</p>
                  ) : (
                    <>
                      <Field
                        label={t("glass.catalogCode")}
                        value={sku}
                        onChange={(value) => {
                          setSku(value);
                          setReview(false);
                        }}
                      />
                      <Field
                        label={t("glass.purchaseCode")}
                        value={purchaseSku}
                        onChange={(value) => {
                          setPurchaseSku(value);
                          setReview(false);
                        }}
                      />
                      <Field
                        label={t("glass.supplier")}
                        value={supplier}
                        onChange={(value) => {
                          setSupplier(value);
                          setReview(false);
                        }}
                      />
                      {review ? (
                        <div className="glass-publication">
                          <p>{t("glass.publishDiff")}</p>
                          <dl className="glass-facts">
                            <div>
                              <dt>{t("glass.before")}</dt>
                              <dd>{selected?.spec ?? t("glass.noProduct")}</dd>
                            </div>
                            <div>
                              <dt>{t("glass.after")}</dt>
                              <dd>{preview.data?.notation}</dd>
                            </div>
                            <div>
                              <dt>{t("glass.source")}</dt>
                              <dd>{draft.source}</dd>
                            </div>
                          </dl>
                          <button
                            type="button"
                            className="primary-action"
                            disabled={
                              publishing || busy || preview.isFetching || delayedDraft !== draft
                            }
                            onClick={() => void publish()}
                          >
                            {publishing ? t("glass.publishing") : t("glass.publish")}
                          </button>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={() => setReview(false)}
                          >
                            {t("glass.back")}
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="ghost-button"
                          disabled={
                            busy ||
                            !sku.trim() ||
                            !purchaseSku.trim() ||
                            !supplier.trim() ||
                            !preview.data ||
                            preview.isFetching ||
                            preview.isError ||
                            delayedDraft !== draft ||
                            preview.data.findings.some((finding) => finding.blocking)
                          }
                          onClick={() => setReview(true)}
                        >
                          {t("glass.reviewPublish")}
                        </button>
                      )}
                    </>
                  )}
                </div>
                {preview.isError && <p role="alert">{glassError(preview.error)}</p>}
                <Findings preview={preview.data} />
              </Dialog>
            )}
            <Findings preview={preview.data} />
          </>
        ) : (
          <p>{t("glass.chooseToCompose")}</p>
        )}
      </details>
      {message && <p role="status">{message}</p>}
    </section>
  );
}

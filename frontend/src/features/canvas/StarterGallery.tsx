import { useMemo, useState } from "react";

import type { DesignOptions, ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { STARTER_DEFINITIONS, starterNominalSize, type StarterDefinition } from "./designLibrary";
import type { MemberGeometry } from "./members";
import { ProductFrontSvg } from "./ProductFrontSvg";
import type { ProductJson } from "./productEditing";
import { intentBays } from "./intentEditing";

function family(product: ProductJson): string {
  if (product.assembly.modules.length > 1) return "Conjuntos";
  const openings = intentBays(product.assembly.modules[0]!.tree).map(
    (bay) => bay.opening_type ?? "FIXED",
  );
  if (openings.some((value) => value.startsWith("SLIDING"))) return "Correderas";
  if (openings.some((value) => value.startsWith("DOOR"))) return "Puertas";
  if (openings.some((value) => value.startsWith("TILT_TURN"))) return "Oscilobatientes";
  if (openings.includes("AWNING")) return "Proyectantes";
  if (openings.some((value) => value.startsWith("TURN"))) return "Abatibles";
  return "Fijos";
}

const NO_ISSUES: ProductIssue[] = [];
const NOOP = () => {};

function StarterThumb({
  product,
  members,
}: {
  product: ProductJson;
  members: MemberGeometry;
}): JSX.Element {
  return (
    <ProductFrontSvg
      product={product}
      members={members}
      selectedId={null}
      issues={NO_ISSUES}
      disabled
      preview
      onSelectModule={NOOP}
      onAddUnit={NOOP}
      onCommitModuleWidth={NOOP}
      onCommitTotalWidth={NOOP}
      onCommitHeight={NOOP}
    />
  );
}

/** Design library: starter cards previewed through the same front-elevation
 * renderer as the workspace, so a template reads exactly like the product it
 * creates — including catalog face widths and material surfaces once a series
 * is selected. Cards are creation recipes, not product types. */
export function StarterGallery({
  members,
  disabled,
  onPick,
  allowedOpenings,
  options,
}: {
  members: MemberGeometry;
  disabled: boolean;
  allowedOpenings?: string[];
  options?: DesignOptions;
  onPick(definition: StarterDefinition): void;
}): JSX.Element {
  const previews = useMemo(
    () =>
      STARTER_DEFINITIONS.map((definition) => {
        const { widthMm, heightMm } = starterNominalSize(definition.key);
        return { definition, product: definition.build(widthMm, heightMm) };
      }),
    [],
  );
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const compatible = previews.filter(
      ({ product }) =>
        (!options || !product.assembly.couplings.length || options.coupler_skus.length > 0) &&
        (!options?.system_family ||
          product.assembly.modules.every((module) =>
            options.system_family === "FRAMELESS" ? Boolean(module.frameless) : !module.frameless,
          )) &&
        (!options ||
          product.assembly.modules.every((module) => {
            const divisions = (node: typeof module.tree): boolean =>
              (node.type !== "SPLIT_V" ||
                options.profiles.some((profile) => profile.role === "MULLION_V")) &&
              (node.type !== "SPLIT_H" ||
                options.profiles.some((profile) => profile.role === "MULLION_H")) &&
              (node.children?.every(divisions) ?? true);
            return divisions(module.tree);
          })) &&
        (!allowedOpenings ||
          product.assembly.modules.every((module) =>
            intentBays(module.tree).every((bay) =>
              allowedOpenings.includes(bay.opening_type ?? "FIXED"),
            ),
          )),
    );
    if (!needle) return compatible;
    return compatible.filter(({ definition }) =>
      `${t(definition.titleKey)} ${t(definition.hintKey)}`.toLowerCase().includes(needle),
    );
  }, [previews, query, allowedOpenings, options]);
  return (
    <div className="starter-gallery-wrap">
      <label className="starter-search">
        <input
          type="search"
          value={query}
          placeholder={t("assembly.starterSearch")}
          aria-label={t("assembly.starterSearch")}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      {filtered.length === 0 ? (
        <p className="starter-empty" role="status">
          {t("assembly.starterNoMatch")}
        </p>
      ) : (
        <div className="starter-gallery" role="list" aria-label={t("assembly.starterLibrary")}>
          {Array.from(new Set(filtered.map(({ product }) => family(product)))).map((group) => (
            <section className="starter-family" key={group}>
              <h4>{group}</h4>
              <div>
                {filtered
                  .filter(({ product }) => family(product) === group)
                  .map(({ definition, product }) => (
                    <div key={definition.key} role="listitem" className="starter-card-wrap">
                      <button
                        type="button"
                        className="starter-card"
                        aria-label={`${t(definition.titleKey)} · ${t(definition.hintKey)}`}
                        disabled={disabled}
                        onClick={() => onPick(definition)}
                      >
                        <span className="starter-thumb">
                          <StarterThumb product={product} members={members} />
                        </span>
                        <span className="starter-card-title">{t(definition.titleKey)}</span>
                        <span className="starter-card-hint">{t(definition.hintKey)}</span>
                      </button>
                    </div>
                  ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

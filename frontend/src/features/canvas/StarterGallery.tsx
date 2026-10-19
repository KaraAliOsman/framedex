import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { DesignOptions, ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import {
  STARTER_DEFINITIONS,
  catalogStarters,
  starterSize,
  starterTitle,
  starterHint,
  type StarterDefinition,
} from "./designLibrary";
import {
  physicalLabel,
  choiceMatches,
  openingChoices,
  type OpeningLeafFact,
  type AdvancedAvailability,
} from "./physicalOpenings";
import type { MemberGeometry } from "./members";
import { ProductFrontSvg } from "./ProductFrontSvg";
import type { ProductJson } from "./productEditing";
import { intentBays } from "./intentEditing";
import { compatibleCouplers } from "./couplerAuthority";

function family(product: ProductJson): string {
  if (product.assembly.modules.length > 1) return "Conjuntos";
  const advanced = intentBays(product.assembly.modules[0]!.tree).find(
    (bay) => bay.opening_recipe_code,
  );
  if (advanced?.opening) return physicalLabel(advanced.opening, advanced.opening_use ?? "WINDOW");
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
  leaves = [],
}: {
  product: ProductJson;
  members: MemberGeometry;
  leaves?: OpeningLeafFact[];
}): JSX.Element {
  return (
    <ProductFrontSvg
      product={product}
      members={members}
      openingFacts={{
        [product.assembly.modules[0]!.id]: leaves.map((leaf) => ({
          ...leaf,
          bay_id: product.assembly.modules[0]!.tree.id,
        })),
      }}
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
      [...STARTER_DEFINITIONS, ...catalogStarters(options)].map((definition) => {
        const { widthMm, heightMm } = starterSize(definition);
        return { definition, product: definition.build(widthMm, heightMm) };
      }),
    [options],
  );
  const [query, setQuery] = useState("");
  const [availability, setAvailability] = useState<AdvancedAvailability | null>(null);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const compatible = previews.filter(
      ({ product }) =>
        (!options ||
          product.assembly.couplings.every(
            (coupling) =>
              compatibleCouplers(options.coupler_profiles ?? [], coupling.angle_deg).length > 0,
          )) &&
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
              bay.opening_recipe_code
                ? openingChoices(options).some((choice) => choiceMatches(bay, choice))
                : allowedOpenings.includes(bay.opening_type ?? "FIXED"),
            ),
          )),
    );
    if (!needle) return compatible;
    return compatible.filter(({ definition }) =>
      `${starterTitle(definition)} ${starterHint(definition)}`.toLowerCase().includes(needle),
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
                        aria-label={`${starterTitle(definition)} · ${starterHint(definition)}`}
                        disabled={disabled}
                        onClick={() => onPick(definition)}
                      >
                        <span className="starter-thumb">
                          <StarterThumb
                            product={product}
                            members={members}
                            leaves={definition.previewLeaves}
                          />
                        </span>
                        <span className="starter-card-title">{starterTitle(definition)}</span>
                        <span className="starter-card-hint">{starterHint(definition)}</span>
                      </button>
                    </div>
                  ))}
              </div>
            </section>
          ))}
        </div>
      )}
      {Boolean(options?.advanced_availability?.length) && (
        <details className="advanced-availability">
          <summary>Elegir una apertura avanzada · series y datos necesarios</summary>
          <div className="advanced-availability-choices">
            {(options!.advanced_availability as unknown as AdvancedAvailability[]).map((item) => (
              <button
                type="button"
                key={`${item.use}-${item.movement}`}
                aria-pressed={
                  availability?.movement === item.movement && availability?.use === item.use
                }
                onClick={() => setAvailability(item)}
              >
                {item.label} · {item.available ? "Disponible" : "Sin dato"}
              </button>
            ))}
          </div>
          {availability && (
            <div role="status">
              <p>
                <strong>{availability.label}</strong> · {availability.reason}
              </p>
              <p>
                {availability.compatible_systems.length
                  ? `Series que la permiten: ${availability.compatible_systems.join("; ")}.`
                  : "No hay una serie disponible con estos datos completos."}
              </p>
              {!availability.available && (
                <Link to="/catalogs/systems">Completar la serie en Catálogos</Link>
              )}
            </div>
          )}
        </details>
      )}
    </div>
  );
}

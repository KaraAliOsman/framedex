import { useMemo } from "react";

import type { ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import {
  STARTER_DEFINITIONS,
  starterNominalSize,
  type StarterDefinition,
} from "./designLibrary";
import type { MemberGeometry } from "./members";
import { ProductFrontSvg } from "./ProductFrontSvg";
import type { ProductJson } from "./productEditing";

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
}: {
  members: MemberGeometry;
  disabled: boolean;
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
  return (
    <div className="starter-gallery" role="list" aria-label={t("assembly.starterLibrary")}>
      {previews.map(({ definition, product }) => (
        <div key={definition.key} role="listitem" className="starter-card-wrap">
          <button
            type="button"
            className="starter-card"
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
  );
}

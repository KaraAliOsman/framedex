import { useMemo } from "react";

import type { PositionDesign, ProductIssue } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import type { IntentNode } from "../canvas/intentEditing";
import { resolveMembers } from "../canvas/members";
import { isProductModel, wrapTreeAsProduct, type ProductJson } from "../canvas/productEditing";
import { frontLayout, ProductFrontContent } from "../canvas/ProductFrontSvg";
import { StudioImage } from "../canvas/renderStudio";

const NO_ISSUES: ProductIssue[] = [];
const NOOP = () => {};

/** Neutral PVC-60 member geometry — the thumbnail shows real bay layout and
 * opening glyphs; catalog face widths only exist inside the editor. */
const THUMB_MEMBERS = resolveMembers(undefined);

function designProduct(design: PositionDesign): ProductJson {
  const tree = design.parametric_tree;
  if (isProductModel(tree)) return tree;
  return wrapTreeAsProduct(tree as IntentNode, design.nominal_width_mm, design.nominal_height_mm);
}

/** Live front-elevation thumbnail for a saved position: classic trees are
 * wrapped as a one-module product so both storage shapes render identically.
 * The tight viewBox crops the dimension chains — only the product reads. */
export function PositionThumb({
  design,
  variant = "elevation",
}: {
  design: PositionDesign;
  /** "studio" renders the §05 commercial view — the premium visual for
   * project cards; "elevation" keeps the technical line drawing used
   * where changes are compared side by side. */
  variant?: "elevation" | "studio";
}): JSX.Element {
  const product = useMemo(() => designProduct(design), [design]);
  const { totalW, height, lift, dip, leftOver, rightOver } = frontLayout(product);
  if (variant === "studio") {
    return (
      <StudioImage
        product={product}
        members={THUMB_MEMBERS}
        options={{ width: 360, height: 300 }}
        alt={t("projects.positionThumb")}
        className="position-thumb"
      />
    );
  }
  const pad = 8;
  return (
    <svg
      className="position-thumb"
      viewBox={`${-pad - leftOver} ${-pad} ${totalW + leftOver + rightOver + pad * 2} ${height + lift + dip + pad * 2}`}
      role="img"
      aria-label={t("projects.positionThumb")}
    >
      <ProductFrontContent
        product={product}
        members={THUMB_MEMBERS}
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
    </svg>
  );
}

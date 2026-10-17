import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type {
  PositionDesign,
  ProductIssue,
  ResolvedFinish,
  ProfileCut,
} from "../../api/generated/models";
import { projectDesignOptions } from "../../api/generated/dekopen";
import { t } from "../../i18n/es-CL";
import type { IntentNode } from "../canvas/intentEditing";
import {
  resolveMembers,
  withFinishMembers,
  withCutJoints,
  type MemberGeometry,
} from "../canvas/members";
import { isProductModel, wrapTreeAsProduct, type ProductJson } from "../canvas/productEditing";
import { frontLayout, ProductFrontContent } from "../canvas/ProductFrontSvg";
import { webglAvailable } from "../canvas/webglAvailable";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";

// three.js stays behind the dynamic boundary — the studio renderer only
// loads when a card actually renders it (lazy fetches on first render).
const LazyStudioImage = lazy(() =>
  import("../canvas/renderStudio").then((mod) => ({ default: mod.StudioImage })),
);

const NO_ISSUES: ProductIssue[] = [];
const NO_LEAVES: OpeningLeafFact[] = [];
const NOOP = () => {};

/** Fallback geometry when a historical position has no catalog section. */
export const THUMB_MEMBERS = resolveMembers(undefined);

export function designProduct(design: PositionDesign): ProductJson {
  const tree = design.parametric_tree;
  if (isProductModel(tree)) return tree;
  return wrapTreeAsProduct(tree as IntentNode, design.nominal_width_mm, design.nominal_height_mm);
}

/** WebGL thumb renders are the expensive part of a position grid — only
 * pay for them once the card actually scrolls into view. Off-screen cards
 * keep the cheap elevation until then. */
function useVisible<T extends HTMLElement>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node || visible || typeof IntersectionObserver === "undefined") {
      if (!visible && typeof IntersectionObserver === "undefined") setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible]);
  return [ref, visible];
}

/** Live front-elevation thumbnail for a saved position: classic trees are
 * wrapped as a one-module product so both storage shapes render identically.
 * The tight viewBox crops the dimension chains — only the product reads. */
export type DrawingSelection = {
  moduleId: string;
  nodeId?: string;
  kind: "module" | "bay" | "division";
};

type PositionThumbProps = {
  design: PositionDesign;
  /** "studio" renders the §05 commercial view — the premium visual for
   * project cards; "elevation" keeps the technical line drawing used
   * where changes are compared side by side. */
  variant?: "elevation" | "studio";
  /** Member geometry+material override — callers that know the sealed finish
   * (portal) pass a re-skinned set so the render matches the quoted color. */
  members?: MemberGeometry;
  openingLeaves?: OpeningLeafFact[];
  orgId?: string;
  systemId?: string;
  finish?: ResolvedFinish | null;
  cuts?: ProfileCut[];
  selection?: DrawingSelection | null;
  onSelectPart?(selection: DrawingSelection): void;
};

export function PositionThumb(props: PositionThumbProps): JSX.Element {
  if (props.orgId && props.systemId && !props.members) return <CatalogPositionThumb {...props} />;
  return <PositionVisual {...props} />;
}

function CatalogPositionThumb(props: PositionThumbProps): JSX.Element {
  const { orgId, systemId } = props;
  const options = useQuery({
    queryKey: ["design-options", orgId, systemId],
    enabled: !!orgId && !!systemId,
    staleTime: 60_000,
    queryFn: async () => {
      const response = await projectDesignOptions(systemId!, {
        headers: { "X-Organization-ID": orgId! },
      });
      if (response.status !== 200) throw new Error("catalog_unavailable");
      return response.data;
    },
  });
  const members = useMemo(() => resolveMembers(options.data), [options.data]);
  return <PositionVisual {...props} members={members} />;
}

function PositionVisual({
  design,
  variant = "elevation",
  members: suppliedMembers,
  openingLeaves = NO_LEAVES,
  finish,
  cuts,
  selection,
  onSelectPart,
}: PositionThumbProps): JSX.Element {
  const members = useMemo(() => {
    let resolved = suppliedMembers ?? THUMB_MEMBERS;
    if (finish) resolved = withFinishMembers(resolved, finish);
    return cuts ? withCutJoints(resolved, cuts) : resolved;
  }, [suppliedMembers, finish, cuts]);
  const product = useMemo(() => designProduct(design), [design]);
  const openingFacts = useMemo(
    () =>
      Object.fromEntries(
        product.assembly.modules.map((module) => [
          module.id,
          openingLeaves
            .filter(
              (leaf) =>
                leaf.bay_id.startsWith(module.id + "|") ||
                (product.assembly.modules.length === 1 && !leaf.bay_id.includes("|")),
            )
            .map((leaf) => ({
              ...leaf,
              bay_id: leaf.bay_id.startsWith(module.id + "|")
                ? leaf.bay_id.slice(module.id.length + 1)
                : leaf.bay_id,
            })),
        ]),
      ),
    [product, openingLeaves],
  );
  const [hostRef, visible] = useVisible<HTMLDivElement>();
  // Grid cards re-render on every parent pass — the layout must not.
  const { totalW, height, lift, dip, leftOver, rightOver } = useMemo(
    () => frontLayout(product),
    [product],
  );
  // No WebGL → the technical elevation keeps rendering; the studio card
  // would otherwise degrade to an empty placeholder.
  const pad = 8;
  const elevation = (
    <svg
      className="position-thumb"
      viewBox={`${-pad - leftOver} ${-pad} ${totalW + leftOver + rightOver + pad * 2} ${height + lift + dip + pad * 2}`}
      role={onSelectPart ? "group" : "img"}
      aria-label={t("projects.positionThumb")}
    >
      <ProductFrontContent
        product={product}
        members={members}
        openingFacts={openingFacts}
        selectedId={selection?.moduleId ?? null}
        selectedBayId={selection?.kind === "bay" ? (selection.nodeId ?? null) : null}
        selectedDivisionId={selection?.kind === "division" ? (selection.nodeId ?? null) : null}
        issues={NO_ISSUES}
        disabled
        preview={!onSelectPart}
        selectionOnly={!!onSelectPart}
        onSelectModule={
          onSelectPart ? (moduleId) => onSelectPart({ moduleId, kind: "module" }) : NOOP
        }
        onSelectBay={
          onSelectPart
            ? (moduleId, nodeId) => onSelectPart({ moduleId, nodeId, kind: "bay" })
            : undefined
        }
        onSelectDivision={
          onSelectPart
            ? (moduleId, nodeId) => onSelectPart({ moduleId, nodeId, kind: "division" })
            : undefined
        }
        onAddUnit={NOOP}
        onCommitModuleWidth={NOOP}
        onCommitTotalWidth={NOOP}
        onCommitHeight={NOOP}
      />
    </svg>
  );
  if (variant === "studio" && webglAvailable()) {
    return (
      <div ref={hostRef} className="position-thumb-host">
        {visible ? (
          <Suspense fallback={elevation}>
            <LazyStudioImage
              product={product}
              members={members}
              options={{
                width: 360,
                height: 300,
                inside: members.viewFace !== "exterior",
                openingFacts,
              }}
              alt={t("projects.positionThumb")}
              className="position-thumb"
            />
          </Suspense>
        ) : (
          elevation
        )}
      </div>
    );
  }
  return elevation;
}

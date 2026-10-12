import fixtures from "../../../engine/tests/fixtures/symbols/assemblies.json";
import type { DrawingFacts } from "../api/generated/models";
import { CanvasViewport } from "../features/canvas/CanvasViewport";
import { frontBounds, ProductFrontContent } from "../features/canvas/ProductFrontSvg";
import { resolveMembers } from "../features/canvas/members";
import type { ProductJson } from "../features/canvas/productEditing";

const noEdit = (): void => undefined;

/** DEV grammar fixtures have no coupler authority and cannot be manufactured. */
export function DrawingTable(): JSX.Element {
  return (
    <section className="drawing-table" aria-label="Cotas de conjuntos DEMO">
      <p>DEMO · gramática de dibujo sin acoplador autorizado. No habilita fabricación.</p>
      {fixtures.map((fixture) => {
        const product = fixture.product as ProductJson;
        const facts = fixture.drawing as Record<string, DrawingFacts>;
        return (["interior", "exterior"] as const).map((face) => (
          <figure key={`${fixture.name}-${face}`} data-drawing-case={`${fixture.name}-${face}`}>
            <figcaption>
              {fixture.label} · Vista {face}
            </figcaption>
            <div className="drawing-table__sheet">
              <CanvasViewport
                contentBox={frontBounds(product, facts, true)}
                selectionBox={null}
                status="DEMO · dibujo de referencia"
              >
                <ProductFrontContent
                  product={product}
                  members={resolveMembers(undefined, undefined, face)}
                  selectedId={null}
                  issues={[]}
                  disabled
                  dimLevel="technical"
                  drawingFacts={facts}
                  elevation={fixture.elevation}
                  onSelectModule={noEdit}
                  onAddUnit={noEdit}
                  onCommitModuleWidth={noEdit}
                  onCommitTotalWidth={noEdit}
                  onCommitHeight={noEdit}
                />
              </CanvasViewport>
            </div>
          </figure>
        ));
      })}
    </section>
  );
}

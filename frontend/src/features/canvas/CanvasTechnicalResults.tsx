import type { EngineCalculateResponse } from "../../api/generated/models";
import { selectCanvasTechnicalValues } from "./technicalResults";

type CanvasTechnicalResultsProps = {
  response: EngineCalculateResponse;
};

export function CanvasTechnicalResults({ response }: CanvasTechnicalResultsProps): JSX.Element {
  const values = selectCanvasTechnicalValues(response);
  return (
    <aside className="canvas-technical-results" aria-labelledby="canvas-results-title">
      <p className="eyebrow">RESULTADOS DEL ENGINE</p>
      <h2 id="canvas-results-title">Despiece técnico G1</h2>
      <dl>
        <div>
          <dt>FRAME cut</dt>
          <dd data-testid="technical-frame">{values.frame}</dd>
        </div>
        <div>
          <dt>FRAME reinforcement</dt>
          <dd data-testid="technical-reinforcement">{values.reinforcement}</dd>
        </div>
        <div>
          <dt>Glass</dt>
          <dd data-testid="technical-glass">{values.glass}</dd>
        </div>
        <div>
          <dt>Glazing bead</dt>
          <dd data-testid="technical-bead">{values.glazingBead}</dd>
        </div>
      </dl>
    </aside>
  );
}

import { Icon } from "./Icon";

/** «¿De dónde sale?» as a quiet information mark (constitution P2: every
 * number's source one click away) instead of a sentence repeated on every
 * row. The words stay for screen readers and the tooltip. */
export function SourceSummary(): JSX.Element {
  return (
    <summary className="ui-source-summary" title="¿De dónde sale?">
      <Icon name="info" size={16} />
      <span className="sr-only">¿De dónde sale?</span>
    </summary>
  );
}

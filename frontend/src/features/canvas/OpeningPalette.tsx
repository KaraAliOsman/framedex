import type { DesignOptions } from "../../api/generated/models";
import type { IntentNode } from "./intentEditing";
import { choiceMatches, choicePatch, openingChoices } from "./physicalOpenings";
import { OpeningSymbol } from "../../ui/OpeningSymbol";

export function OpeningPalette({
  options,
  bay,
  disabled,
  onPick,
  onPreview,
}: {
  options: DesignOptions;
  bay: IntentNode;
  disabled: boolean;
  onPick(patch: Partial<IntentNode>): void;
  onPreview(patch: Partial<IntentNode> | null): void;
}): JSX.Element {
  const choices = openingChoices(options);
  return (
    <>
      <div className="opening-palette" role="group" aria-label="Aperturas del sistema">
        {choices.map((choice) => (
          <button
            key={choice.id}
            className={`opening-choice opening-choice--named${choiceMatches(bay, choice) ? " is-active" : ""}`}
            type="button"
            disabled={disabled}
            aria-pressed={choiceMatches(bay, choice)}
            onMouseEnter={() => onPreview(choicePatch(choice))}
            onMouseLeave={() => onPreview(null)}
            onFocus={() => onPreview(choicePatch(choice))}
            onBlur={() => onPreview(null)}
            onClick={() => {
              onPreview(null);
              onPick(choicePatch(choice));
            }}
          >
            <svg viewBox="0 0 100 100" aria-hidden="true">
              <rect className="opening-choice__frame" x="4" y="4" width="92" height="92" />
              {choice.layout ? (
                choice.layout.leaves.map((leaf, index) => (
                  <g key={leaf.slot}>
                    <rect
                      className="opening-choice__frame"
                      x={4 + index * 46}
                      y="4"
                      width="46"
                      height="92"
                    />
                    <OpeningSymbol
                      opening={leaf.opening}
                      x={4 + index * 46}
                      y={4}
                      width={46}
                      height={92}
                    />
                    {leaf.opening.leaf_role === "ACTIVE" && (
                      <path data-handle="true" d={`M${index === 0 ? 47 : 53} 46v8`} />
                    )}
                  </g>
                ))
              ) : (
                <>
                  <OpeningSymbol opening={choice.opening} x={4} y={4} width={92} height={92} />
                  {choice.opening.movement !== "FIXED" && choice.opening.movement !== "SLIDE" && (
                    <path
                      data-handle="true"
                      d={
                        choice.opening.hinge_side === "LEFT"
                          ? "M90 46v8"
                          : choice.opening.hinge_side === "RIGHT"
                            ? "M10 46v8"
                            : choice.opening.hinge_side === "TOP"
                              ? "M46 90h8"
                              : "M46 10h8"
                      }
                    />
                  )}
                </>
              )}
            </svg>
            <span>{choice.label}</span>
          </button>
        ))}
      </div>
      {!choices.length && (
        <p className="assembly-hint">
          Sin dato: declara las capacidades con su fuente en Catálogo › Sistema.
        </p>
      )}
      <details className="opening-availability">
        <summary>Compatibilidad y fuente</summary>
        <p>
          Estas aperturas están respaldadas por las capacidades y los herrajes del catálogo. Una
          dirección o composición ausente necesita una fuente antes de ofrecerse.
        </p>
        <ul>
          {Array.from(new Set(choices.map((choice) => choice.source))).map((source) => (
            <li key={source}>{source}</li>
          ))}
        </ul>
      </details>
    </>
  );
}

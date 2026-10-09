import type { DesignOptions } from "../../api/generated/models";
import type { IntentNode } from "./intentEditing";
import { choiceMatches, choicePatch, openingChoices } from "./physicalOpenings";
import { OpeningSymbol } from "../../ui/OpeningSymbol";
import { Popover } from "../../ui/Overlays";
import { physicalNodeLabel } from "./physicalOpenings";
import { OPENING_OPTIONS } from "./openings";
import { t } from "../../i18n/es-CL";
import { dismissFloatingLayers } from "../../ui/floatingLayer";
import type { Opening } from "./intentEditing";
import { OpeningGlyph } from "./ProductFrontSvg";

/** Historical designs use the same palette in the bay and module inspectors. */
export function LegacyOpeningPalette({
  options,
  opening,
  disabled,
  onPick,
  unavailable,
}: {
  options?: DesignOptions;
  opening: Opening;
  disabled: boolean;
  onPick(opening: Opening): void;
  unavailable?: (opening: Opening) => string | undefined;
}): JSX.Element {
  return (
    <div className="opening-palette" role="group" aria-label={t("assembly.opening")}>
      {OPENING_OPTIONS.filter(
        ([value]) => !options?.system_family || options.compatible_openings.includes(value),
      ).map(([value, labelKey]) => {
        const reason = unavailable?.(value);
        return (
          <button
            key={value}
            type="button"
            className={`opening-choice opening-choice--named${opening === value ? " is-active" : ""}`}
            title={reason ?? t(labelKey)}
            aria-label={t(labelKey)}
            aria-pressed={opening === value}
            disabled={disabled || !!reason}
            onClick={() => onPick(value)}
          >
            <svg viewBox="0 0 100 100" aria-hidden="true">
              <rect className="opening-choice__frame" x={4} y={4} width={92} height={92} />
              <OpeningGlyph opening={value} x={4} y={4} w={92} h={92} />
            </svg>
            <span>{t(labelKey)}</span>
          </button>
        );
      })}
    </div>
  );
}

export function OpeningPalette({
  options,
  bay,
  disabled,
  onPick,
  onPreview,
  compact = false,
}: {
  options: DesignOptions;
  bay: IntentNode;
  disabled: boolean;
  onPick(patch: Partial<IntentNode>): void;
  onPreview(patch: Partial<IntentNode> | null): void;
  compact?: boolean;
}): JSX.Element {
  const choices = openingChoices(options);
  const content = (
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
              if (compact) dismissFloatingLayers();
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
  const currentLabel =
    physicalNodeLabel(bay) ??
    choices.find((choice) => choiceMatches(bay, choice))?.label ??
    t(OPENING_OPTIONS.find(([opening]) => opening === bay.opening_type)?.[1] ?? "intent.fixed");
  return compact ? (
    <Popover
      label="Elegir apertura"
      trigger={
        <button
          className="editor-opening-trigger"
          type="button"
          aria-label={`Elegir apertura · ${currentLabel}`}
          disabled={disabled}
        >
          <span>Apertura</span>
          <span>{currentLabel}</span>
        </button>
      }
    >
      {content}
    </Popover>
  ) : (
    content
  );
}

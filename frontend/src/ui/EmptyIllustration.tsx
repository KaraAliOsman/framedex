import "./EmptyIllustration.css";

export type EmptyIllustrationKind = "positions" | "cut-plan" | "sheet" | "connection";

/** Unmeasured drawing: ghost dimensions deliberately carry no numeric value. */
export function EmptyIllustration({
  kind = "sheet",
}: {
  kind?: EmptyIllustrationKind;
}): JSX.Element {
  return (
    <svg className="ui-empty-illustration" viewBox="0 0 192 96" aria-hidden="true">
      <path className="ui-empty-illustration__paper" d="M16 8H168L176 16V88H16Z" />
      {kind === "positions" ? (
        <>
          <path className="ui-empty-illustration__member" d="M64 24H128V72H64ZM68 28H124V68H68Z" />
          <path
            className="ui-empty-illustration__ghost"
            d="M64 20V16M128 20V16M64 18H128M60 22L68 14M124 22L132 14M132 24H140M132 72H140M138 24V72M134 28L142 20M134 76L142 68"
          />
        </>
      ) : kind === "cut-plan" ? (
        <>
          <path className="ui-empty-illustration__member" d="M32 40H160V56H32Z" />
          <path
            className="ui-empty-illustration__ghost"
            d="M32 32V24M160 32V24M32 28H160M28 32L36 24M156 32L164 24M56 36V60M96 36V60M136 36V60"
          />
        </>
      ) : kind === "connection" ? (
        <>
          <path className="ui-empty-illustration__member" d="M48 32H80V64H48ZM112 32H144V64H112Z" />
          <path className="ui-empty-illustration__ghost" d="M80 48H92M100 48H112M92 40L100 56" />
        </>
      ) : (
        <>
          <path className="ui-empty-illustration__member" d="M52 28H116L124 36V72H52Z" />
          <path
            className="ui-empty-illustration__ghost"
            d="M60 40H108M60 48H108M60 56H92M132 28H140M132 72H140M138 28V72M134 32L142 24M134 76L142 68"
          />
        </>
      )}
    </svg>
  );
}

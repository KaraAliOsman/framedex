import type { KeyboardEvent } from "react";

import { type DimensionAxis, useCanvasStore } from "./canvasStore";

type EditableDimensionProps = {
  axis: DimensionAxis;
  acceptedValue: string;
  label: string;
  x: number;
  y: number;
  width?: number;
  disabled: boolean;
  onCommit(axis: DimensionAxis, candidate: string): Promise<boolean>;
  onEditStart(): void;
};

export function EditableDimension({
  axis,
  acceptedValue,
  label,
  x,
  y,
  width = 190,
  disabled,
  onCommit,
  onEditStart,
}: EditableDimensionProps): JSX.Element {
  const draftDimension = useCanvasStore((state) => state.draftDimension);
  const setDraftDimension = useCanvasStore((state) => state.setDraftDimension);
  const isEditing = draftDimension?.axis === axis;
  const value = isEditing ? draftDimension.value : acceptedValue;

  function discard(): void {
    if (isEditing) setDraftDimension(null);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "Escape") {
      event.preventDefault();
      discard();
      event.currentTarget.blur();
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    void onCommit(axis, value);
  }

  return (
    <foreignObject x={x} y={y} width={width} height="42" className="dimension-editor">
      <label className="dimension-editor__label">
        <span className="visually-hidden">{label}</span>
        <input
          aria-label={label}
          data-axis={axis}
          disabled={disabled}
          inputMode="decimal"
          value={value}
          onBlur={discard}
          onChange={(event) => setDraftDimension({ axis, value: event.target.value })}
          onFocus={() => {
            onEditStart();
            setDraftDimension({ axis, value: acceptedValue });
          }}
          onKeyDown={handleKeyDown}
        />
        <span aria-hidden="true">mm</span>
      </label>
    </foreignObject>
  );
}

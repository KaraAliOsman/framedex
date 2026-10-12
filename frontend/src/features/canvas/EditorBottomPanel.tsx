import { useId, useState, type ReactNode } from "react";
import { EditorFlyout } from "./EditorFlyout";

/** Footer disclosures share the editor's single operational-layer registry. */
export function EditorBottomPanel({ title, children }: { title: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((current) => !current)}
      >
        {title}
      </button>
      {open && (
        <EditorFlyout
          id={id}
          title={title}
          onClose={() => setOpen(false)}
          className="editor-bottom-panel"
        >
          {children}
        </EditorFlyout>
      )}
    </div>
  );
}

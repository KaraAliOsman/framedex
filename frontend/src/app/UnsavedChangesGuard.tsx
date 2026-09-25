import { useContext, useEffect, useId } from "react";
import { UNSAFE_DataRouterContext, useBlocker } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { Dialog } from "../ui";

import { registerDirtySource } from "./shellUtils";

// The production application uses a data router so browser Back and internal
// navigation pass through the same guard as links.
export function UnsavedChangesGuard({
  dirty,
  message,
}: {
  dirty: boolean;
  message: string;
}): JSX.Element | null {
  const router = useContext(UNSAFE_DataRouterContext);
  const sourceId = useId();
  useEffect(() => (dirty ? registerDirtySource(sourceId) : undefined), [dirty, sourceId]);
  useEffect(() => {
    if (!dirty) return;
    const leave = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", leave);
    return () => window.removeEventListener("beforeunload", leave);
  }, [dirty]);
  return router ? <RouteGuard dirty={dirty} message={message} /> : null;
}

function RouteGuard({ dirty, message }: { dirty: boolean; message: string }): JSX.Element | null {
  const blocker = useBlocker(dirty);
  if (blocker.state !== "blocked") return null;
  return (
    <Dialog
      footer={
        <>
          <button onClick={() => blocker.reset()} type="button">
            {t("ui.cancel")}
          </button>
          <button
            className="ui-button--primary"
            data-primary
            onClick={() => blocker.proceed()}
            type="button"
          >
            {t("ui.confirm")}
          </button>
        </>
      }
      onClose={() => blocker.reset()}
      title={message}
      width="s"
    />
  );
}

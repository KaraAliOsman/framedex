import { useContext, useEffect } from "react";
import { UNSAFE_DataRouterContext, useBlocker } from "react-router-dom";

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

function RouteGuard({ dirty, message }: { dirty: boolean; message: string }): null {
  const blocker = useBlocker(dirty);
  useEffect(() => {
    if (blocker.state !== "blocked") return;
    if (window.confirm(message)) blocker.proceed();
    else blocker.reset();
  }, [blocker, message]);
  return null;
}

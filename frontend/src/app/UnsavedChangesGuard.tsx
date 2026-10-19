import { useContext, useEffect, useId, useState } from "react";
import { UNSAFE_DataRouterContext, useBlocker, type Location } from "react-router-dom";

import { t } from "../i18n/es-CL";
import { Dialog } from "../ui";

import { consumeNavigationBypass, registerDirtySource } from "./shellUtils";

type NextLocation = Pick<Location, "pathname" | "search">;

// The production application uses a data router so browser Back and internal
// navigation pass through the same guard as links.
export function UnsavedChangesGuard({
  dirty,
  message,
  allow,
  onSave,
  onDiscard,
}: {
  dirty: boolean;
  message: string;
  /** Navigations that keep the same work/session pass without asking
   * (e.g. Mesa ↔ Estudio ↔ wide editor of the same position). */
  allow?: (next: NextLocation) => boolean;
  /** With a save action the dialog offers Guardar / Descartar / Cancelar.
   * Resolve true only after the server confirmed the save. */
  onSave?: () => Promise<boolean>;
  onDiscard?: () => void;
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
  return router ? (
    <RouteGuard
      dirty={dirty}
      message={message}
      allow={allow}
      onSave={onSave}
      onDiscard={onDiscard}
    />
  ) : null;
}

function RouteGuard({
  dirty,
  message,
  allow,
  onSave,
  onDiscard,
}: {
  dirty: boolean;
  message: string;
  allow?: (next: NextLocation) => boolean;
  onSave?: () => Promise<boolean>;
  onDiscard?: () => void;
}): JSX.Element | null {
  const [saving, setSaving] = useState(false);
  const [failed, setFailed] = useState(false);
  // Function form so the bypass is evaluated per navigation attempt, and the
  // one-shot consume cannot strand: the immediate guarded transition uses it.
  const blocker = useBlocker(
    ({ nextLocation }) => dirty && !(allow?.(nextLocation) ?? false) && !consumeNavigationBypass(),
  );
  if (blocker.state !== "blocked") return null;
  const cancel = () => {
    setFailed(false);
    blocker.reset();
  };
  if (!onSave)
    return (
      <Dialog
        footer={
          <>
            <button onClick={cancel} type="button">
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
        onClose={cancel}
        title={message}
        width="s"
      />
    );
  return (
    <Dialog
      footer={
        <>
          <button onClick={cancel} type="button" disabled={saving}>
            {t("ui.cancel")}
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => {
              onDiscard?.();
              blocker.proceed();
            }}
          >
            Descartar cambios
          </button>
          <button
            className="ui-button--primary"
            data-primary
            type="button"
            disabled={saving}
            onClick={() => {
              setSaving(true);
              setFailed(false);
              void onSave()
                .then((saved) => {
                  // Navigate only after the server confirmed the save.
                  if (saved) blocker.proceed();
                  else setFailed(true);
                })
                .finally(() => setSaving(false));
            }}
          >
            {saving ? "Guardando…" : "Guardar y continuar"}
          </button>
        </>
      }
      onClose={cancel}
      title={message}
      width="s"
    >
      {failed ? (
        <p role="alert">
          No se pudo guardar. Tus cambios siguen en el editor; revisa el aviso junto a Guardar.
        </p>
      ) : (
        <p>Guarda la ventana, descarta sus cambios o vuelve al editor.</p>
      )}
    </Dialog>
  );
}

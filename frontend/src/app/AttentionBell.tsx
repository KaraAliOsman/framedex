import { Icon } from "../ui/Icon";
import { useState } from "react";
import { Link } from "react-router-dom";
import { DateOnly, Loading } from "../ui";
import { useAuthSession } from "../auth/AuthSessionProvider";
import { useDismiss } from "./shellUtils";
import { useToday } from "./useToday";
import { consequenceLabels } from "./todayLabels";

/** The bell and Hoy observe one tenant/user/role query; viewing a notification
 * never resolves or acknowledges a consequential domain action. */
export function AttentionBell(): JSX.Element | null {
  const org = useAuthSession().me?.active_organization;
  const query = useToday();
  const [open, setOpen] = useState(false);
  const rootRef = useDismiss<HTMLDivElement>(open, () => setOpen(false));
  if (!org) return null;
  const actions = query.data?.actions ?? [];
  return (
    <div className="attention-bell" ref={rootRef}>
      <button
        type="button"
        className="topbar-button topbar-button--icon"
        aria-expanded={open}
        aria-label="Atención pendiente"
        title="Atención pendiente"
        onClick={() => {
          if (!open) {
            window.dispatchEvent(new Event("dekopen:shell-overlay"));
            void query.refetch();
          }
          setOpen((value) => !value);
        }}
      >
        <Icon name="bell" />
        {actions.length > 0 && (
          <span className="attention-bell__badge ui-value">{actions.length}</span>
        )}
      </button>
      {open && (
        <div
          className="shell-menu shell-menu--right attention-menu"
          aria-label="Atención pendiente"
        >
          <p className="shell-menu__title">Atención pendiente</p>
          {query.isPending ? (
            <Loading label="Consultando pendientes" />
          ) : query.isError ? (
            <div role="alert">
              <p>No se pudieron consultar los pendientes.</p>
              <button type="button" onClick={() => void query.refetch()}>
                Reintentar
              </button>
            </div>
          ) : actions.length === 0 ? (
            <p className="shell-menu__meta">Todo al día</p>
          ) : (
            <ul>
              {actions.slice(0, 8).map((item) => (
                <li key={item.key}>
                  <Link
                    className="shell-menu__item attention-menu__item"
                    to={item.href}
                    onClick={() => setOpen(false)}
                  >
                    <span className="ui-value">{item.entity_code}</span>
                    <strong>{item.title}</strong>
                    <span>
                      {consequenceLabels[item.consequence]}
                      {item.due_on && (
                        <>
                          {" "}
                          · <DateOnly value={item.due_on} />
                        </>
                      )}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <Link className="shell-menu__all" to="/dashboard" onClick={() => setOpen(false)}>
            Ver todos los pendientes
          </Link>
        </div>
      )}
    </div>
  );
}

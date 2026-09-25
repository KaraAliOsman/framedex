import { useEffect, useRef } from "react";

import type { RoleEnum } from "../api/generated/models";
import type { TranslationKey } from "../i18n/es-CL";

export const roleLabel: Record<RoleEnum, TranslationKey> = {
  OWNER: "shell.role.owner",
  ESTIMATOR: "shell.role.estimator",
  WORKSHOP_MANAGER: "shell.role.workshopManager",
  INSTALLER: "shell.role.installer",
};

/** Dismiss a floating menu on outside click or Escape — shared by the org
 * switcher, project switcher and attention bell so they behave identically. */
export function useDismiss<T extends HTMLElement>(open: boolean, onClose: () => void) {
  const ref = useRef<T>(null);
  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent): void {
      if (ref.current !== null && !ref.current.contains(event.target as Node)) onClose();
    }
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);
  return ref;
}
export type ContextNavItem = { to: string; label: TranslationKey };

/** Context items share a path and differ only by query (Cola vs ?shortage=1):
 * a query target activates on an exact path+query match; the plain target
 * stays active unless a sibling claims the live query. */
export function contextItemActive(
  item: ContextNavItem,
  siblings: ContextNavItem[],
  pathname: string,
  search: string,
): boolean {
  const url = new URL(item.to, "http://shell.local");
  if (url.search) return url.pathname === pathname && url.search === search;
  if (url.pathname !== pathname) return false;
  return !siblings.some((sibling) => {
    const siblingUrl = new URL(sibling.to, "http://shell.local");
    return siblingUrl.search !== "" && siblingUrl.search === search;
  });
}

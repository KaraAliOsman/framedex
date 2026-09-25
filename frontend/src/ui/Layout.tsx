import { NavLink } from "react-router-dom";
import { type PropsWithChildren, type ReactNode } from "react";

/** Horizontal action bar — the only place surface-level buttons live. */
export function Toolbar({ children }: PropsWithChildren): JSX.Element {
  return <div className="ui-toolbar">{children}</div>;
}

export function ToolbarTitle({ children }: PropsWithChildren): JSX.Element {
  return <h1 className="ui-toolbar__title">{children}</h1>;
}

export function ToolbarSpacer(): JSX.Element {
  return <span className="ui-toolbar__spacer" />;
}

/** Second-level navigation inside a domain context (project tabs, production
 * sections). Renders as an accessible tab-strip of routes. */
export type ContextNavItem = {
  to: string;
  label: string;
  end?: boolean;
};

export function ContextNav({
  items,
  label,
}: {
  items: ContextNavItem[];
  label: string;
}): JSX.Element {
  if (items.length === 0) return <></>;
  return (
    <nav aria-label={label} className="ui-context-nav">
      {items.map((item) => (
        <NavLink className="ui-context-nav__link" end={item.end} key={item.to} to={item.to}>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

/** A pane inside a split workspace. Panes scroll independently; the
 * workspace never scrolls the document. */
export function SplitPane({
  aside,
  children,
  asideWidth = "m",
}: PropsWithChildren<{ aside: ReactNode; asideWidth?: "s" | "m" | "l" }>): JSX.Element {
  return (
    <div className={`ui-split ui-split--${asideWidth}`}>
      <div className="ui-split__main">{children}</div>
      <aside className="ui-split__aside">{aside}</aside>
    </div>
  );
}

import { Icon, type IconName } from "../ui/Icon";
const routes: Record<string, IconName> = {
  "/dashboard": "home",
  "/projects": "projects",
  "/clients": "people",
  "/quotes": "document",
  "/pricing/commercial": "price",
  "/catalogs/systems": "catalog",
  "/purchasing": "cart",
  "/inventory": "stock",
  "/production": "factory",
  "/assistant": "assistant",
  "/jobs": "history",
  "/analytics": "chart",
  "/settings/general": "settings",
};
export function RailIcon({ to }: { to: string }): JSX.Element | null {
  const name = routes[to];
  return name ? <Icon name={name} size={21} className="rail-item__icon" /> : null;
}

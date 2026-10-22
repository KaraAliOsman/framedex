import { Navigate, useLocation } from "react-router-dom";

export function LegacyQuotesRedirect(): JSX.Element {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  params.set("view", "quotes");
  return (
    <Navigate replace to={{ pathname: "/projects", search: `?${params}`, hash: location.hash }} />
  );
}

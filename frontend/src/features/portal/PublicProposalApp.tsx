import { lazy, Suspense, useEffect } from "react";
import { createBrowserRouter, Route, RouterProvider, Routes, useLocation } from "react-router-dom";
import { ConnectionBoundary, RecoveryPage } from "../../app/RecoveryPage";
import { RouteErrorBoundary } from "../../app/RouteErrorBoundary";
import { Loading } from "../../ui/Signature";
import { PortalQuotePage } from "./PortalQuotePage";

const PaymentReturnPage = lazy(async () => ({
  default: (await import("./PaymentReturnPage")).PaymentReturnPage,
}));
const FlowSimulationPage = lazy(async () => ({
  default: (await import("./FlowSimulationPage")).FlowSimulationPage,
}));

export function isPublicProposalPath(path: string): boolean {
  return (
    /^\/cotizacion\/[^/]+\/?$/.test(path) ||
    /^\/pago\/simulado\/[^/]+\/?$/.test(path) ||
    path === "/pago/retorno"
  );
}

/** The internal router and the lean public entry share one route definition. */
export function publicProposalRoutes(): JSX.Element {
  return (
    <>
      <Route path="/cotizacion/:token" element={<PortalQuotePage />} />
      <Route
        path="/pago/simulado/:linkId"
        element={
          <Suspense fallback={<Loading label="Consultando el cobro de prueba" />}>
            <FlowSimulationPage />
          </Suspense>
        }
      />
      <Route
        path="/pago/retorno"
        element={
          <Suspense fallback={<Loading label="Consultando el pago" />}>
            <PaymentReturnPage />
          </Suspense>
        }
      />
    </>
  );
}

function PublicRoutes(): JSX.Element {
  const { pathname } = useLocation();
  useEffect(() => {
    // Crossing into the staff application loads its real auth boundary.
    if (!isPublicProposalPath(pathname)) window.location.replace(window.location.href);
  }, [pathname]);
  return (
    <RouteErrorBoundary>
      <Routes>
        {publicProposalRoutes()}
        <Route path="*" element={<RecoveryPage kind="not-found" />} />
      </Routes>
    </RouteErrorBoundary>
  );
}

let router: ReturnType<typeof createBrowserRouter> | undefined;
export function PublicProposalApp(): JSX.Element {
  router ??= createBrowserRouter([{ path: "*", element: <PublicRoutes /> }]);
  return (
    <ConnectionBoundary>
      <RouterProvider router={router} />
    </ConnectionBoundary>
  );
}

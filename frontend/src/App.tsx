import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate, Route, RouterProvider, Routes } from "react-router-dom";

import { t } from "./i18n/es-CL";

import { AppShell } from "./app/AppShell";
import { RouteErrorBoundary } from "./app/RouteErrorBoundary";
import { ConnectionBoundary, RecoveryPage } from "./app/RecoveryPage";
import { DashboardPage } from "./app/DashboardPage";
import { JobsPage } from "./app/JobsPage";
import { SettingsPage } from "./app/SettingsPage";
import { AuthCallbackPage } from "./auth/AuthCallbackPage";
import { ReadyGuard, SessionGuard } from "./auth/AuthGuards";
import { useAuthSession } from "./auth/AuthSessionProvider";
import { LoginPage } from "./auth/LoginPage";
import { MfaPage } from "./auth/MfaPage";
import { SelectOrganizationPage } from "./auth/SelectOrganizationPage";
import { consumeReturnTo } from "./auth/returnTo";
import { LandingPage } from "./features/landing/LandingPage";
import { AboutPage } from "./brand/AboutPage";
import { homeFor } from "./app/navigation";

export const DEV_ONLY_ROUTE_PATHS = [
  "/projects/demo/positions/g1/edit",
  "/benchmark",
  "/dev/ui",
  "/dev/marca",
  "/dev/correos",
] as const;

export function visibleDevOnlyRoutePaths(
  env: Pick<ImportMetaEnv, "DEV"> = import.meta.env,
): readonly string[] {
  return env.DEV ? DEV_ONLY_ROUTE_PATHS : [];
}
const WalletPage = lazy(async () => ({
  default: (await import("./features/billing/WalletPage")).WalletPage,
}));
const BillingPage = lazy(async () => ({
  default: (await import("./features/billing/BillingPage")).BillingPage,
}));
const PricingPage = lazy(async () => {
  const module = await import("./features/pricing/PricingPage");
  return { default: module.PricingPage };
});
const CommercialPricingPage = lazy(async () => {
  const module = await import("./features/pricing/PricingPage");
  return { default: module.CommercialPricingPage };
});

const CanvasEditor2DView = lazy(async () => {
  const module = await import("./features/canvas/CanvasEditor2DView");
  return { default: module.CanvasEditor2DView };
});

const ProjectPages = lazy(async () => ({
  default: (await import("./features/projects/ProjectPages")).ProjectPages,
}));
const ClientsPage = lazy(async () => ({
  default: (await import("./features/projects/ClientsPage")).ClientsPage,
}));
const CatalogPage = lazy(async () => ({
  default: (await import("./features/catalogs/CatalogPage")).CatalogPage,
}));
const SheetFormatsPage = lazy(async () => ({
  default: (await import("./features/catalogs/SheetFormatsPage")).SheetFormatsPage,
}));
const AssistantWorkspacePage = lazy(async () => ({
  default: (await import("./features/assistant/AssistantWorkspacePage")).AssistantWorkspacePage,
}));
const ProjectPositionEditor = lazy(async () => ({
  default: (await import("./features/projects/ProjectPositionEditor")).ProjectPositionEditor,
}));
const OnboardingPage = lazy(async () => ({
  default: (await import("./features/onboarding/OnboardingPage")).OnboardingPage,
}));

function ProjectSurface({ editor = false }: { editor?: boolean }): JSX.Element {
  return (
    <ReadyGuard>
      <AppShell>
        <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
          {editor ? <ProjectPositionEditor /> : <ProjectPages />}
        </Suspense>
      </AppShell>
    </ReadyGuard>
  );
}

const PurchasingPage = lazy(async () => {
  const module = await import("./features/purchasing/PurchasingPage");
  return { default: module.PurchasingPage };
});
const InventoryPage = lazy(async () => ({
  default: (await import("./features/purchasing/InventoryPage")).InventoryPage,
}));
const QuotationsPage = lazy(async () => ({
  default: (await import("./features/quotations/QuotationsPage")).QuotationsPage,
}));

const ProductionPage = lazy(async () => {
  const module = await import("./features/production/ProductionPage");
  return { default: module.ProductionPage };
});

const PortalQuotePage = lazy(async () => {
  const module = await import("./features/portal/PortalQuotePage");
  return { default: module.PortalQuotePage };
});
const PaymentReturnPage = lazy(async () => {
  const module = await import("./features/portal/PaymentReturnPage");
  return { default: module.PaymentReturnPage };
});
const FlowSimulationPage = lazy(async () => {
  const module = await import("./features/portal/FlowSimulationPage");
  return { default: module.FlowSimulationPage };
});
const BenchmarkPage = lazy(async () => {
  const module = await import("./features/benchmark/BenchmarkPage");
  return { default: module.BenchmarkPage };
});
const UiPage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/UiPage")).UiPage }))
  : null;
const BrandPage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/BrandPage")).BrandPage }))
  : null;
const MailExamplesPage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/MailExamplesPage")).MailExamplesPage }))
  : null;

function HomeRedirect(): JSX.Element {
  const auth = useAuthSession();
  if (auth.status === "loading" || auth.status === "resolving") {
    return <p role="status">{t("auth.resolving")}</p>;
  }
  if (auth.status === "mfa_required") return <Navigate to="/auth/mfa" replace />;
  if (auth.status === "organization_required") {
    return <Navigate to="/select-organization" replace />;
  }
  if (auth.status === "ready") {
    // The operator starts at the station; other roles start with their work.
    const home = homeFor(auth.me?.active_organization?.role);
    // A magic link can land on `/` instead of /auth/callback when the site
    // URL differs from the requested origin — still honor the stashed
    // destination rather than dropping it on the dashboard.
    return <Navigate to={consumeReturnTo(home)} replace />;
  }
  // Anonymous visitors get the public product presentation, not a bare login.
  return <LandingPage />;
}

/** Hoy authorizes its projection for all five roles. The operator's default
 * entry still opens the station; an explicit Inicio link opens their queue. */
function DashboardRoute(): JSX.Element {
  return (
    <AppShell>
      <DashboardPage />
    </AppShell>
  );
}

export function AppRoutes(): JSX.Element {
  return (
    <RouteErrorBoundary>
      <Routes>
        <Route
          path="/settings/billing"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("wallet.loading")}</p>}>
                  <BillingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/settings/wallet"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("wallet.loading")}</p>}>
                  <WalletPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="/projects/:id" element={<ProjectSurface />} />
        <Route path="/projects/:id/positions/new" element={<ProjectSurface editor />} />
        <Route
          path="/projects/:id/pricing"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
                  <CommercialPricingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        {visibleDevOnlyRoutePaths().length > 0 && (
          <>
            {BrandPage ? (
              <Route
                path="/dev/marca"
                element={
                  <Suspense fallback={<p role="status">Cargando marca</p>}>
                    <BrandPage />
                  </Suspense>
                }
              />
            ) : null}
            {MailExamplesPage ? (
              <Route
                path="/dev/correos"
                element={
                  <ReadyGuard>
                    <Suspense fallback={<p role="status">Cargando correos</p>}>
                      <MailExamplesPage />
                    </Suspense>
                  </ReadyGuard>
                }
              />
            ) : null}
            {UiPage ? (
              <Route
                path="/dev/ui"
                element={
                  <ReadyGuard>
                    <Suspense fallback={<p role="status">Cargando el manual de componentes</p>}>
                      <UiPage />
                    </Suspense>
                  </ReadyGuard>
                }
              />
            ) : null}
            <Route
              path="/projects/demo/positions/g1/edit"
              element={
                <ReadyGuard>
                  <AppShell>
                    <Suspense fallback={<p role="status">{t("canvas.loading")}</p>}>
                      <CanvasEditor2DView demoRoute />
                    </Suspense>
                  </AppShell>
                </ReadyGuard>
              }
            />
            <Route
              path="/benchmark"
              element={
                <Suspense fallback={<p role="status" />}>
                  <BenchmarkPage />
                </Suspense>
              }
            />
          </>
        )}
        <Route
          path="/pricing/commercial"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("pricing.loading")}</p>}>
                  <CommercialPricingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/pricing/cost-lists"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("pricing.loading")}</p>}>
                  <PricingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="/" element={<HomeRedirect />} />
        <Route
          path="/about"
          element={
            <ReadyGuard>
              <AboutPage />
            </ReadyGuard>
          }
        />
        <Route
          path="/cotizacion/:token"
          element={
            <Suspense fallback={<p role="status">{t("portal.loading")}</p>}>
              <PortalQuotePage />
            </Suspense>
          }
        />
        <Route
          path="/pago/simulado/:linkId"
          element={
            <Suspense fallback={<p role="status">Consultando el cobro de prueba</p>}>
              <FlowSimulationPage />
            </Suspense>
          }
        />
        <Route
          path="/pago/retorno"
          element={
            <Suspense fallback={<p role="status" />}>
              <PaymentReturnPage />
            </Suspense>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route
          path="/auth/mfa"
          element={
            <SessionGuard>
              <MfaPage />
            </SessionGuard>
          }
        />
        <Route
          path="/select-organization"
          element={
            <SessionGuard>
              <SelectOrganizationPage />
            </SessionGuard>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ReadyGuard>
              <DashboardRoute />
            </ReadyGuard>
          }
        />
        <Route
          path="/clients/:id?"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("clients.loading")}</p>}>
                  <ClientsPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/jobs"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("jobs.title")}</p>}>
                  <JobsPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/purchasing"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("purchasing.loading")}</p>}>
                  <PurchasingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/production"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("production.loading")}</p>}>
                  <ProductionPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/projects/:id/positions/:posId/edit"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
                  <ProjectPositionEditor />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="/projects" element={<ProjectSurface />} />
        <Route path="/catalogs" element={<Navigate to="/catalogs/systems" replace />} />
        <Route
          path="/catalogs/sheet-formats"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">Cargando formatos de lámina…</p>}>
                  <SheetFormatsPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/assistant"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
                  <AssistantWorkspacePage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/catalogs/systems"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
                  <CatalogPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/onboarding"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">{t("onboarding.loading")}</p>}>
                  <OnboardingPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/settings/general"
          element={
            <ReadyGuard>
              <AppShell>
                <SettingsPage />
              </AppShell>
            </ReadyGuard>
          }
        />
        {/* Keep general settings and inventory entry addresses usable. */}
        <Route path="/settings" element={<Navigate to="/settings/general" replace />} />
        <Route
          path="/inventory"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">Cargando inventario…</p>}>
                  <InventoryPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/quotes"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<p role="status">Cargando cotizaciones…</p>}>
                  <QuotationsPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="*" element={<RecoveryPage kind="not-found" />} />
      </Routes>
    </RouteErrorBoundary>
  );
}

const router = createBrowserRouter([{ path: "*", element: <AppRoutes /> }]);

export function App(): JSX.Element {
  return (
    <ConnectionBoundary>
      <RouterProvider router={router} />
    </ConnectionBoundary>
  );
}

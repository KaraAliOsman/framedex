import { lazy, Suspense, type PropsWithChildren } from "react";
import { createBrowserRouter, Navigate, Route, RouterProvider, Routes } from "react-router-dom";

import { t } from "./i18n/es-CL";

import { RouteErrorBoundary } from "./app/RouteErrorBoundary";
import { ConnectionBoundary, RecoveryPage } from "./app/RecoveryPage";
import { AuthCallbackPage } from "./auth/AuthCallbackPage";
import { InvitationPage } from "./auth/InvitationPage";
import { ReadyGuard, SessionGuard } from "./auth/AuthGuards";
import { useAuthSession } from "./auth/AuthSessionProvider";
import { LoginPage } from "./auth/LoginPage";
import { MfaPage } from "./auth/MfaPage";
import { SelectOrganizationPage } from "./auth/SelectOrganizationPage";
import { consumeReturnTo } from "./auth/returnTo";
import { homeFor } from "./app/navigation";
import { Loading } from "./ui/Signature";
import { publicProposalRoutes } from "./features/portal/PublicProposalApp";

// Public proposals should not fetch the estimator's shell, assistant and
// settings before they can show the manufacturer's document.
const LazyAppShell = lazy(async () => ({ default: (await import("./app/AppShell")).AppShell }));
const DashboardPage = lazy(async () => ({
  default: (await import("./app/DashboardPage")).DashboardPage,
}));
const JobsPage = lazy(async () => ({ default: (await import("./app/JobsPage")).JobsPage }));
const AnalyticsPage = lazy(async () => ({
  default: (await import("./features/analytics/AnalyticsPage")).AnalyticsPage,
}));
const FieldPage = lazy(async () => ({
  default: (await import("./features/field/FieldPage")).FieldPage,
}));
const SettingsPage = lazy(async () => ({
  default: (await import("./app/SettingsPage")).SettingsPage,
}));
const AdvancedFeatures = lazy(async () => ({
  default: (await import("./app/AdvancedFeatures")).AdvancedFeatures,
}));
const LazyLandingPage = lazy(async () => ({
  default: (await import("./features/landing/LandingPage")).LandingPage,
}));
const LazyAboutPage = lazy(async () => ({
  default: (await import("./brand/AboutPage")).AboutPage,
}));

function LandingPage(): JSX.Element {
  return (
    <Suspense fallback={<Loading label="Cargando el inicio" />}>
      <LazyLandingPage />
    </Suspense>
  );
}
function AboutPage(): JSX.Element {
  return (
    <Suspense fallback={<Loading label="Cargando datos de la aplicación" />}>
      <LazyAboutPage />
    </Suspense>
  );
}

function AppShell({ children }: PropsWithChildren): JSX.Element {
  return (
    <Suspense fallback={<Loading label="Cargando su espacio de trabajo" />}>
      <LazyAppShell>{children}</LazyAppShell>
    </Suspense>
  );
}

export const DEV_ONLY_ROUTE_PATHS = import.meta.env.DEV
  ? ([
      "/projects/demo/positions/g1/edit",
      "/benchmark",
      "/dev/ui",
      "/dev/marca",
      "/dev/correos",
      "/dev/tabla",
      "/dev/prueba-serie",
      "/dev/precios-proveedor",
      "/dev/lectura-manual",
    ] as const)
  : [];

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
  default: (await import("./features/catalogs/SeriesCatalogPage")).SeriesCatalogPage,
}));
const QuotationsPage = lazy(async () => ({
  default: (await import("./features/quotations/QuotationsPage")).QuotationsPage,
}));
const FinishSamplesPage = lazy(async () => ({
  default: (await import("./features/catalogs/FinishSamplesPage")).FinishSamplesPage,
}));
const SheetFormatsPage = lazy(async () => ({
  default: (await import("./features/catalogs/SheetFormatsPage")).SheetFormatsPage,
}));
const AssistantWorkspacePage = lazy(async () => ({
  default: (await import("./features/assistant/AssistantWorkspacePage")).AssistantWorkspacePage,
}));
const OnboardingPage = lazy(async () => ({
  default: (await import("./features/onboarding/OnboardingPage")).OnboardingPage,
}));

/** One shell and one work instance for every route of the same work: the
 * collection (Mesa), Estudio and the wide editor are presentations of the
 * same ProjectPages tree, so opening/closing the editor never remounts the
 * shell, the visited forms or the editing session. */
function ProjectSurface(): JSX.Element {
  return (
    <ReadyGuard>
      <AppShell>
        <Suspense fallback={<p role="status">{t("projects.loading")}</p>}>
          <ProjectPages />
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

const ProductionPage = lazy(async () => {
  const module = await import("./features/production/ProductionPage");
  return { default: module.ProductionPage };
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
const EditableTablePage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/EditableTablePage")).EditableTablePage }))
  : null;
const SeriesTrialPage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/SeriesTrialPage")).SeriesTrialPage }))
  : null;
const SupplierPricesPage = import.meta.env.DEV
  ? lazy(async () => ({ default: (await import("./dev/SupplierPricesPage")).SupplierPricesPage }))
  : null;
const CatalogDoubleReadPage = import.meta.env.DEV
  ? lazy(async () => ({
      default: (await import("./dev/CatalogDoubleReadPage")).CatalogDoubleReadPage,
    }))
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
    // Everyone starts at Hoy; role-specific work remains directly reachable.
    const home = homeFor(auth.me?.active_organization?.role);
    // A magic link can land on `/` instead of /auth/callback when the site
    // URL differs from the requested origin — still honor the stashed
    // destination rather than dropping it on the dashboard.
    return <Navigate to={consumeReturnTo(home)} replace />;
  }
  // Anonymous visitors get the public product presentation, not a bare login.
  return <LandingPage />;
}

/** Hoy authorizes its projection for all five roles. */
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
        <Route path="/projects/:id" element={<ProjectSurface />}>
          <Route path="positions/new" element={null} />
          <Route path="positions/:posId/edit" element={null} />
        </Route>
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
        {import.meta.env.DEV && visibleDevOnlyRoutePaths().length > 0 && (
          <>
            {CatalogDoubleReadPage ? (
              <Route
                path="/dev/lectura-manual"
                element={
                  <Suspense fallback={<Loading label="Cargando las lecturas" />}>
                    <CatalogDoubleReadPage />
                  </Suspense>
                }
              />
            ) : null}
            {SupplierPricesPage ? (
              <Route
                path="/dev/precios-proveedor"
                element={
                  <Suspense fallback={<Loading label="Cargando precios" />}>
                    <SupplierPricesPage />
                  </Suspense>
                }
              />
            ) : null}
            {SeriesTrialPage ? (
              <Route
                path="/dev/prueba-serie"
                element={
                  <Suspense fallback={<Loading label="Cargando el despiece" />}>
                    <SeriesTrialPage />
                  </Suspense>
                }
              />
            ) : null}
            {EditableTablePage ? (
              <Route
                path="/dev/tabla"
                element={
                  <Suspense fallback={<Loading label="Cargando la tabla" />}>
                    <EditableTablePage />
                  </Suspense>
                }
              />
            ) : null}
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
          path="/analytics"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<Loading label="Cargando Informes" />}>
                  <AnalyticsPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route
          path="/about"
          element={
            <ReadyGuard>
              <AboutPage />
            </ReadyGuard>
          }
        />
        {publicProposalRoutes()}
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
          path="/field"
          element={
            <Suspense fallback={<Loading label="Cargando Terreno" />}>
              <FieldPage />
            </Suspense>
          }
        />
        <Route
          path="/dispatch"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<Loading label="Cargando despacho y postventa" />}>
                  <FieldPage office />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="/projects" element={<ProjectSurface />} />
        <Route path="/catalogs" element={<Navigate to="/catalogs/systems" replace />} />
        <Route
          path="/catalogs/finish-samples"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<Loading label="Cargando muestras" />}>
                  <FinishSamplesPage />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
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
          path="/settings/advanced"
          element={
            <ReadyGuard>
              <AppShell>
                <Suspense fallback={<Loading label="Cargando funciones avanzadas" />}>
                  <AdvancedFeatures />
                </Suspense>
              </AppShell>
            </ReadyGuard>
          }
        />
        <Route path="/invitation" element={<InvitationPage />} />
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

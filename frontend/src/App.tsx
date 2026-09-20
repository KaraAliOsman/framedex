import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate, Route, RouterProvider, Routes } from "react-router-dom";

import { t } from "./i18n/es-CL";

import { AppShell } from "./app/AppShell";
import { DashboardPage } from "./app/DashboardPage";
import { PlaceholderPage } from "./app/PlaceholderPage";
import { AuthCallbackPage } from "./auth/AuthCallbackPage";
import { ReadyGuard, SessionGuard } from "./auth/AuthGuards";
import { useAuthSession } from "./auth/AuthSessionProvider";
import { LoginPage } from "./auth/LoginPage";
import { MfaPage } from "./auth/MfaPage";
import { SelectOrganizationPage } from "./auth/SelectOrganizationPage";
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
const CatalogPage = lazy(async () => ({
  default: (await import("./features/catalogs/CatalogPage")).CatalogPage,
}));
const ProjectPositionEditor = lazy(async () => ({
  default: (await import("./features/projects/ProjectPositionEditor")).ProjectPositionEditor,
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

function ProtectedPage({ title, description }: { title: string; description: string }) {
  return (
    <ReadyGuard>
      <AppShell>
        <PlaceholderPage title={title} description={description} />
      </AppShell>
    </ReadyGuard>
  );
}

function HomeRedirect(): JSX.Element {
  const auth = useAuthSession();
  if (auth.status === "loading" || auth.status === "resolving") {
    return <p role="status">{t("auth.resolving")}</p>;
  }
  if (auth.status === "mfa_required") return <Navigate to="/auth/mfa" replace />;
  if (auth.status === "organization_required") {
    return <Navigate to="/select-organization" replace />;
  }
  return <Navigate to={auth.status === "ready" ? "/dashboard" : "/login"} replace />;
}

export function AppRoutes(): JSX.Element {
  return (
    <Routes>
      <Route path="/projects/:id" element={<ProjectSurface />} />
      <Route path="/projects/:id/positions/new" element={<ProjectSurface editor />} />
      <Route
        path="/projects/:id/pricing"
        element={
          <ReadyGuard>
            <AppShell>
              <Suspense fallback={<p>{t("projects.loading")}</p>}>
                <CommercialPricingPage />
              </Suspense>
            </AppShell>
          </ReadyGuard>
        }
      />
      <Route
        path="/projects/demo/positions/g1/edit"
        element={
          <ReadyGuard>
            <AppShell>
              <Suspense fallback={<p>{t("canvas.loading")}</p>}>
                <CanvasEditor2DView demoRoute />
              </Suspense>
            </AppShell>
          </ReadyGuard>
        }
      />
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
            <AppShell>
              <DashboardPage />
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
        path="/settings/general"
        element={
          <ProtectedPage title={t("page.settings")} description={t("page.settingsDescription")} />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const router = createBrowserRouter([{ path: "*", element: <AppRoutes /> }]);

export function App(): JSX.Element {
  return <RouterProvider router={router} />;
}

import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

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

const CanvasEditor2DView = lazy(async () => {
  const module = await import("./features/canvas/CanvasEditor2DView");
  return { default: module.CanvasEditor2DView };
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
        path="/projects/:id/positions/:posId/edit"
        element={
          <ReadyGuard>
            <AppShell>
              <Suspense fallback={<p role="status">{t("canvas.loading")}</p>}>
                <CanvasEditor2DView />
              </Suspense>
            </AppShell>
          </ReadyGuard>
        }
      />
      <Route
        path="/projects"
        element={
          <ProtectedPage title={t("page.projects")} description={t("page.projectsDescription")} />
        }
      />
      <Route
        path="/catalogs/systems"
        element={
          <ProtectedPage title={t("page.systems")} description={t("page.systemsDescription")} />
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

export function App(): JSX.Element {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

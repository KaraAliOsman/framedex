import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";

import { PublicProposalApp, isPublicProposalPath } from "./features/portal/PublicProposalApp";
import { Loading } from "./ui/Signature";
import "./index.css";
import "./styles/tokens.css";
import { applyAppBrand } from "./brand/head";
import { ConfirmProvider, ToastProvider } from "./ui";
import "./ui/ui.css";

const container = document.getElementById("root");
if (container === null) throw new Error("Frontend root element is missing");

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Route re-mounts shouldn't instantly re-hit the API — most reads
      // stay accurate within 30 s and mutations invalidate explicitly.
      staleTime: 30_000,
    },
  },
});

// One light theme for the whole product (constitution §3.1).
if (!isPublicProposalPath(window.location.pathname)) applyAppBrand("light");

const PrivateApplication = lazy(() => import("./PrivateApplication"));

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfirmProvider>
        <ToastProvider>
          <Suspense fallback={<Loading label="Cargando su espacio de trabajo" />}>
            {isPublicProposalPath(window.location.pathname) ? (
              <PublicProposalApp />
            ) : (
              <PrivateApplication />
            )}
          </Suspense>
        </ToastProvider>
      </ConfirmProvider>
    </QueryClientProvider>
  </StrictMode>,
);

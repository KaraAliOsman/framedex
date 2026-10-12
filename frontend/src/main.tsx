import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";

import { PublicProposalApp, isPublicProposalPath } from "./features/portal/PublicProposalApp";
import { DimLoader } from "./ui/Signature";
import "./index.css";
import "./styles/tokens.css";
import { ThemeProvider } from "./theme/ThemeProvider";
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

const PrivateApplication = lazy(() => import("./PrivateApplication"));

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ConfirmProvider>
          <ToastProvider>
            <Suspense fallback={<DimLoader label="Cargando su espacio de trabajo" />}>
              {isPublicProposalPath(window.location.pathname) ? (
                <PublicProposalApp />
              ) : (
                <PrivateApplication />
              )}
            </Suspense>
          </ToastProvider>
        </ConfirmProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);

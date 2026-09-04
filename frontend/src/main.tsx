import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { AuthSessionProvider } from "./auth/AuthSessionProvider";
import "./index.css";
import "./styles/tokens.css";
import { ThemeProvider } from "./theme/ThemeProvider";

const container = document.getElementById("root");
if (container === null) throw new Error("Frontend root element is missing");

const queryClient = new QueryClient();

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthSessionProvider>
          <App />
        </AuthSessionProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);

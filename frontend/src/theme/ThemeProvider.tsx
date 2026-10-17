import { createContext, type PropsWithChildren, useContext, useEffect } from "react";
import { applyAppBrand } from "../brand/head";

export type Theme = "light" | "dark";

const ThemeContext = createContext<{ theme: Theme } | null>(null);
const appearance = { theme: "light" as const };

export function ThemeProvider({ children }: PropsWithChildren): JSX.Element {
  document.documentElement.dataset.theme = "light";
  useEffect(() => {
    if (!window.location.pathname.startsWith("/cotizacion/")) applyAppBrand("light");
  }, []);
  return <ThemeContext.Provider value={appearance}>{children}</ThemeContext.Provider>;
}

export function useTheme(): { theme: Theme } {
  const context = useContext(ThemeContext);
  if (context === null) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}

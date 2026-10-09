import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";

import { telemetry } from "../telemetry/telemetry";
import { applyAppBrand } from "../brand/head";

export type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme(): void;
};

type ThemeState = ThemeContextValue & { setSurfaceDefault(theme: Theme): void };

const ThemeContext = createContext<ThemeState | null>(null);

function initialTheme(): Theme {
  const stored = window.localStorage.getItem("dekopen.theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: PropsWithChildren): JSX.Element {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const setSurfaceDefault = useCallback((next: Theme) => {
    const stored = window.localStorage.getItem("dekopen.theme");
    if (stored !== "light" && stored !== "dark") setTheme(next);
  }, []);
  document.documentElement.dataset.theme = theme;
  useEffect(() => {
    if (!window.location.pathname.startsWith("/cotizacion/")) applyAppBrand(theme);
  }, [theme]);

  const value = useMemo<ThemeState>(
    () => ({
      theme,
      setSurfaceDefault,
      toggleTheme() {
        const next = theme === "light" ? "dark" : "light";
        window.localStorage.setItem("dekopen.theme", next);
        document.documentElement.dataset.theme = next;
        telemetry.capture("theme_changed", { theme: next });
        setTheme(next);
      },
    }),
    [theme, setSurfaceDefault],
  );
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(surfaceDefault?: Theme): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === null) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  const { setSurfaceDefault } = context;
  useLayoutEffect(() => {
    if (surfaceDefault) setSurfaceDefault(surfaceDefault);
  }, [setSurfaceDefault, surfaceDefault]);
  return context;
}

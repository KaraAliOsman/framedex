import { createContext, type PropsWithChildren, useContext, useMemo, useState } from "react";

import { telemetry } from "../telemetry/telemetry";

export type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme(): void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function initialTheme(): Theme {
  const stored = window.localStorage.getItem("dekopen.theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: PropsWithChildren): JSX.Element {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  document.documentElement.dataset.theme = theme;

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      toggleTheme() {
        const next = theme === "light" ? "dark" : "light";
        window.localStorage.setItem("dekopen.theme", next);
        document.documentElement.dataset.theme = next;
        telemetry.capture("theme_changed", { theme: next });
        setTheme(next);
      },
    }),
    [theme],
  );
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === null) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}

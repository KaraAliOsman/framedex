import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThemeProvider, useTheme, type Theme } from "./ThemeProvider";

function Surface({ defaultTheme }: { defaultTheme: Theme }) {
  const { theme, toggleTheme } = useTheme(defaultTheme);
  return (
    <button type="button" onClick={toggleTheme}>
      {theme}
    </button>
  );
}

describe("surface appearance", () => {
  it("starts workshop dark without storing a preference, then toggles on the first click", () => {
    const { rerender } = render(
      <ThemeProvider>
        <Surface defaultTheme="dark" />
      </ThemeProvider>,
    );
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("dekopen.theme")).toBeNull();
    rerender(
      <ThemeProvider>
        <Surface defaultTheme="light" />
      </ThemeProvider>,
    );
    expect(document.documentElement.dataset.theme).toBe("light");
    rerender(
      <ThemeProvider>
        <Surface defaultTheme="dark" />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "dark" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("dekopen.theme")).toBe("light");
  });

  it("keeps an explicit light preference when entering workshop and toggles to dark", () => {
    localStorage.setItem("dekopen.theme", "light");
    render(
      <ThemeProvider>
        <Surface defaultTheme="dark" />
      </ThemeProvider>,
    );
    expect(document.documentElement.dataset.theme).toBe("light");
    fireEvent.click(screen.getByRole("button", { name: "light" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("dekopen.theme")).toBe("dark");
  });
});

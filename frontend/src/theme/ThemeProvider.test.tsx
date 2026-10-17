import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThemeProvider, useTheme } from "./ThemeProvider";

function Surface() {
  const { theme } = useTheme();
  return <p>{theme}</p>;
}

describe("surface appearance", () => {
  it("uses the same light appearance when a previous session stored dark", () => {
    localStorage.setItem("dekopen.theme", "dark");
    render(
      <ThemeProvider>
        <Surface />
      </ThemeProvider>,
    );
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(screen.getByText("light")).toBeVisible();
  });
});

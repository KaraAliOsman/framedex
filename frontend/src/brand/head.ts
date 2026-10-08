export function applyAppBrand(theme: "light" | "dark"): void {
  document
    .querySelector<HTMLLinkElement>('link[rel="icon"][type="image/svg+xml"]')
    ?.setAttribute("href", `/favicon-${theme}.svg`);
  document
    .querySelector<HTMLLinkElement>('link[rel="icon"][type="image/png"]')
    ?.setAttribute("href", `/icon-${theme}-32.png`);
  document
    .querySelector<HTMLLinkElement>('link[rel="apple-touch-icon"]')
    ?.setAttribute("href", `/icon-${theme}-180.png`);
  const color = getComputedStyle(document.documentElement)
    .getPropertyValue("--interactive-fill")
    .trim();
  if (color) document.querySelector('meta[name="theme-color"]')?.setAttribute("content", color);
}

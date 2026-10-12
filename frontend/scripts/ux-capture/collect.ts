import type { Page } from "@playwright/test";
import { detectPresentationFindings, type Observation } from "./presentation.ts";

export async function collectPresentationFindings(
  page: Page,
  workshop: boolean,
  selector = "*",
): Promise<{ kind: string; sample: string }[]> {
  const observations: Observation[] = await page.evaluate((selector) => {
    function visible(element: Element): boolean {
      const style = window.getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return (
        style.visibility !== "hidden" && style.display !== "none" && box.width > 0 && box.height > 0
      );
    }
    function effectiveBackground(element: Element): string {
      const layers: number[][] = [];
      for (let current: Element | null = element; current; current = current.parentElement) {
        const color =
          getComputedStyle(current)
            .backgroundColor.match(/[\d.]+/g)
            ?.map(Number) ?? [];
        if (color.length >= 3) layers.push([color[0]!, color[1]!, color[2]!, color[3] ?? 1]);
      }
      let rgb = [255, 255, 255];
      for (const layer of layers.reverse())
        rgb = rgb.map((value, index) => layer[index]! * layer[3]! + value * (1 - layer[3]!));
      return `rgb(${rgb.join(", ")})`;
    }
    const probe = document.createElement("div");
    probe.style.display = "none";
    document.body.append(probe);
    const allowedShadows = ["--e1", "--e2", "--e3", "--sheet", "--focus-ring"].map((token) => {
      probe.style.boxShadow = `var(${token})`;
      return getComputedStyle(probe).boxShadow;
    });
    probe.remove();
    const observations: Observation[] = [];
    for (const element of Array.from(document.body.querySelectorAll(selector))) {
      if (!visible(element)) continue;
      const style = getComputedStyle(element);
      const text = Array.from(element.childNodes)
        .filter((node) => node.nodeType === Node.TEXT_NODE)
        .map((node) => node.textContent)
        .join("")
        .trim();
      const box = element.getBoundingClientRect();
      const interactive = element.matches("button,a,input,select,textarea,[role='button']");
      let hasEffect = element.matches(
        "a[href]:not([href='']):not([href='#']),input,select,textarea,summary",
      );
      const events = element.matches("button[type='submit']")
        ? ["onClick", "onSubmit"]
        : ["onClick", "onPointerDown", "onKeyDown"];
      for (let current: Element | null = element; current; current = current.parentElement) {
        const propsKey = Object.keys(current).find((key) => key.startsWith("__reactProps$"));
        const props = propsKey
          ? (current as unknown as Record<string, Record<string, unknown>>)[propsKey]
          : undefined;
        if (
          events.some((name) => typeof props?.[name] === "function") ||
          current.hasAttribute("onclick")
        )
          hasEffect = true;
      }
      const region = element.closest("[data-region],form,aside,section,dialog") ?? document.body;
      observations.push({
        sample: `${element.tagName.toLowerCase()}.${element.getAttribute("class") ?? ""} ${(element.getAttribute("aria-label") ?? text).slice(0, 100)}`,
        fontSize: parseFloat(style.fontSize),
        radius: Math.max(
          ...[
            style.borderTopLeftRadius,
            style.borderTopRightRadius,
            style.borderBottomLeftRadius,
            style.borderBottomRightRadius,
          ].map(parseFloat),
        ),
        shadow: style.boxShadow,
        allowedShadows,
        backgroundImage: style.backgroundImage,
        filter: style.filter,
        backdropFilter: style.backdropFilter,
        textColor: style.color,
        backgroundColor: effectiveBackground(element),
        hasText: text.length > 0,
        largeText:
          parseFloat(style.fontSize) >= 24 ||
          (parseFloat(style.fontSize) >= 18.667 && parseInt(style.fontWeight) >= 600),
        interactive,
        disabled: element.matches(":disabled,[aria-disabled='true']"),
        hasEffect,
        width: box.width,
        height: box.height,
        statusDot: element.hasAttribute("data-status-dot"),
        primary: element.matches(".ui-button--primary,[data-variant='primary']"),
        region:
          region.getAttribute("data-region") ??
          region.id ??
          region.getAttribute("class") ??
          region.tagName,
      });
    }
    return observations;
  }, selector);
  return detectPresentationFindings(observations, workshop);
}

const layers: HTMLElement[] = [];
const original = new Map<HTMLElement, { inert: boolean; hidden: string | null }>();
let observer: MutationObserver | null = null;

function refresh() {
  const top = layers.at(-1);
  for (const child of document.body.children) {
    if (!(child instanceof HTMLElement)) continue;
    if (!original.has(child))
      original.set(child, { inert: child.inert, hidden: child.getAttribute("aria-hidden") });
    const saved = original.get(child)!;
    child.inert = top && child !== top ? true : saved.inert;
    if (top && child !== top) child.setAttribute("aria-hidden", "true");
    else if (saved.hidden === null) child.removeAttribute("aria-hidden");
    else child.setAttribute("aria-hidden", saved.hidden);
  }
}

export function isTopDialog(overlay: HTMLElement | null | undefined): boolean {
  return layers.at(-1) === overlay;
}

/** Keep background content out of keyboard and screen-reader navigation while modal. */
export function isolateDialog(overlay: HTMLElement): () => void {
  layers.push(overlay);
  refresh();
  if (!observer) {
    observer = new MutationObserver(refresh);
    observer.observe(document.body, { childList: true });
  }
  return () => {
    const index = layers.indexOf(overlay);
    if (index >= 0) layers.splice(index, 1);
    refresh();
    if (!layers.length) {
      observer?.disconnect();
      observer = null;
      original.clear();
    }
  };
}

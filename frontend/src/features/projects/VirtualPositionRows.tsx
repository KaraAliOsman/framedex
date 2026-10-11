import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";

export type PositionRowEntry = { key: string; estimate: number; content: ReactNode };

/** Variable-height rows keep long site names, warnings and grouped grid cards
 * visible. Windowing changes the mounted range, never the stored selection. */
export function VirtualPositionRows({
  rows,
  virtual,
  scrollTo,
}: {
  rows: PositionRowEntry[];
  virtual: boolean;
  scrollTo: { key: string; epoch: number } | null;
}): JSX.Element {
  const viewport = useRef<HTMLDivElement>(null);
  const heights = useRef(new Map<string, number>());
  const [revision, setRevision] = useState(0);
  const [scroll, setScroll] = useState(0);
  const [height, setHeight] = useState(480);
  const layout = useMemo(() => {
    let offset = 0;
    return rows.map((row) => {
      const size = heights.current.get(row.key) ?? row.estimate;
      const entry = { ...row, offset, size };
      offset += size;
      return entry;
    });
  }, [rows, revision]);
  const total = layout.length
    ? layout[layout.length - 1]!.offset + layout[layout.length - 1]!.size
    : 0;
  let first = virtual ? layout.findIndex((row) => row.offset + row.size > scroll) : 0;
  if (first < 0) first = Math.max(0, rows.length - 1);
  first = Math.max(0, first - 2);
  let last = virtual ? layout.findIndex((row) => row.offset >= scroll + height) : rows.length;
  if (last < 0) last = rows.length;
  last = Math.min(rows.length, last + 2);
  useLayoutEffect(() => {
    const host = viewport.current;
    if (!host) return;
    const measure = () => setHeight(host.clientHeight || 480);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);
  useLayoutEffect(() => {
    const host = viewport.current;
    if (!host) return;
    const observer = new ResizeObserver((entries) => {
      let changed = false;
      for (const entry of entries) {
        const element = entry.target as HTMLElement;
        const key = element.dataset.rowKey;
        const size = element.getBoundingClientRect().height;
        if (key && size > 0 && heights.current.get(key) !== size) {
          heights.current.set(key, size);
          changed = true;
        }
      }
      if (changed) setRevision((value) => value + 1);
    });
    host.querySelectorAll<HTMLElement>("[data-row-key]").forEach((row) => observer.observe(row));
    return () => observer.disconnect();
  }, [first, last, rows]);
  useLayoutEffect(() => {
    if (!scrollTo || !virtual || !viewport.current) return;
    const target = layout.find((row) => row.key === scrollTo.key);
    if (!target) return;
    if (
      target.offset < viewport.current.scrollTop ||
      target.offset + target.size > viewport.current.scrollTop + height
    ) {
      viewport.current.scrollTop = target.offset;
      setScroll(target.offset);
    }
  }, [scrollTo, virtual, layout, height]);
  return (
    <div
      className="project-positions-viewport"
      ref={viewport}
      data-virtual={virtual || undefined}
      onScroll={(event) => setScroll(event.currentTarget.scrollTop)}
    >
      {virtual && <div aria-hidden style={{ height: layout[first]?.offset ?? 0 }} />}
      {layout.slice(first, last).map((row) => (
        <div key={row.key} data-row-key={row.key}>
          {row.content}
        </div>
      ))}
      {virtual && (
        <div aria-hidden style={{ height: Math.max(0, total - (layout[last]?.offset ?? total)) }} />
      )}
    </div>
  );
}

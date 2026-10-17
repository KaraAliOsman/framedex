import type { CSSProperties } from "react";

/** One optical grid for controls; labels carry their meaning. */
const shapes = {
  home: (
    <>
      <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" />
    </>
  ),
  projects: (
    <>
      <path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
      <path d="M7 12h10M7 16h6" />
    </>
  ),
  window: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="M12 3v18M4 12h16" />
    </>
  ),
  people: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2 21v-2a7 7 0 0 1 14 0v2M16 4a3.5 3.5 0 0 1 0 7M22 21v-2a7 7 0 0 0-4-6" />
    </>
  ),
  document: (
    <>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z" />
      <path d="M14 3v6h6M8 13h8M8 17h5" />
    </>
  ),
  catalog: (
    <>
      <rect x="3" y="4" width="5" height="16" rx="1" />
      <rect x="8" y="4" width="5" height="16" rx="1" />
      <path d="m15 5 4-1 3 15-4 1Z" />
    </>
  ),
  price: (
    <>
      <path d="m20 13-9 9-9-9V3h10Z" />
      <circle cx="7" cy="8" r="1" />
    </>
  ),
  cart: (
    <>
      <path d="M2 3h3l3 13h11l3-10H6" />
      <circle cx="10" cy="21" r="1" />
      <circle cx="18" cy="21" r="1" />
    </>
  ),
  stock: (
    <>
      <path d="m3 7 9-4 9 4v11l-9 4-9-4Z" />
      <path d="m3 7 9 4 9-4M12 11v11M7 5l9 4" />
    </>
  ),
  factory: (
    <>
      <path d="M3 21V10l6 3V7l7 4V3h5v18ZM7 17h1M12 17h1M17 17h1" />
    </>
  ),
  assistant: (
    <>
      <path d="M6 18V8a4 4 0 0 1 4-4h8M18 6v10a4 4 0 0 1-4 4H6M9 12h6" />
      <circle cx="18" cy="4" r="1" fill="currentColor" stroke="none" />
    </>
  ),
  history: (
    <>
      <path d="M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v5l3 2" />
    </>
  ),
  chart: (
    <>
      <path d="M3 3v18h18M7 16v-5M12 16V6M17 16V9" />
    </>
  ),
  settings: (
    <>
      <path d="M4 6h16M4 12h16M4 18h16" />
      <rect x="7" y="4" width="3" height="4" rx="1" fill="var(--surface-panel)" />
      <rect x="14" y="10" width="3" height="4" rx="1" fill="var(--surface-panel)" />
      <rect x="8" y="16" width="3" height="4" rx="1" fill="var(--surface-panel)" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  up: <path d="M12 20V4m-6 6 6-6 6 6" />,
  back: <path d="M20 12H4m6-6-6 6 6 6" />,
  chevron: <path d="m9 5 7 7-7 7" />,
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  upload: (
    <>
      <path d="M12 16V3m-5 5 5-5 5 5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" />
    </>
  ),
  attach: <path d="m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9" />,
  check: <path d="m5 12 4 4L19 6" />,
  edit: (
    <>
      <path d="m15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-4-4L5 15Z" />
    </>
  ),
  layers: (
    <>
      <path d="m3 8 9-5 9 5-9 5ZM3 13l9 5 9-5M3 18l9 5 9-5" />
    </>
  ),
  split_v: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="M12 3v18" />
    </>
  ),
  split_h: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="1" />
      <path d="M3 12h18" />
    </>
  ),
  opening: (
    <>
      <path d="M4 3h16v18H4Z" />
      <path d="m4 3 16 9L4 21" />
    </>
  ),
  glass: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="m6 10 5-5M13 19l5-5" />
    </>
  ),
  select: <path d="m5 3 15 9-7 2-3 7Z" />,
  ruler: (
    <>
      <path d="M3 7h18v10H3ZM7 7v4M12 7v6M17 7v4" />
    </>
  ),
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 9a3 3 0 1 1 5 2c-2 1-2 2-2 3M12 17h.01" />
    </>
  ),
  expand: <path d="M9 3H3v6M15 3h6v6M3 15v6h6M21 15v6h-6" />,
  panel: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M14 4v16" />
    </>
  ),
  more: (
    <>
      <circle cx="5" cy="12" r="1" fill="currentColor" />
      <circle cx="12" cy="12" r="1" fill="currentColor" />
      <circle cx="19" cy="12" r="1" fill="currentColor" />
    </>
  ),
} as const;

export type IconName = keyof typeof shapes;
export function Icon({
  name,
  size = 20,
  className,
  style,
}: {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}): JSX.Element {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      style={style}
    >
      {shapes[name]}
    </svg>
  );
}

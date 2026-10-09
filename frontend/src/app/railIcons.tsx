/** Shared 24px, 1.5px monoline vocabulary for the workflow navigation. */
const paths = {
  dashboard: (
    <>
      <path d="M4 4h16v16H4zM8 8h8M8 12h8M8 16h5" />
    </>
  ),
  projects: <path d="M3 5h18v14H3zM12 5v14M3 12h18" />,
  clients: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-2c0-3 3-5 8-5s8 2 8 5v2" />
    </>
  ),
  quotes: <path d="M5 3h11l3 3v15H5zM9 9h6M9 13h6M9 17h4" />,
  prices: <path d="M3 6h18v14H3zM3 10h18M7 16h5" />,
  catalog: <path d="M3 3h7v18H3zM10 3h8l3 18h-8z" />,
  purchasing: (
    <>
      <path d="M3 4h3l2 12h11l2-8H7" />
      <circle cx="10" cy="20" r="1" />
      <circle cx="18" cy="20" r="1" />
    </>
  ),
  inventory: <path d="M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18" />,
  production: <path d="M3 21V9l6 4V7l6 4V3h6v18zM7 17h2M12 17h2M17 17h2" />,
  assistant: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 10v3M16 10v3M9 17h6" />
    </>
  ),
  jobs: <path d="M4 5h16M4 12h16M4 19h10" />,
  settings: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2" />
    </>
  ),
};
const routes: Record<string, keyof typeof paths> = {
  "/dashboard": "dashboard",
  "/projects": "projects",
  "/clients": "clients",
  "/quotes": "quotes",
  "/pricing/commercial": "prices",
  "/catalogs/systems": "catalog",
  "/purchasing": "purchasing",
  "/inventory": "inventory",
  "/production": "production",
  "/assistant": "assistant",
  "/jobs": "jobs",
  "/settings/general": "settings",
};
export function RailIcon({ to }: { to: string }): JSX.Element | null {
  const key = routes[to];
  if (!key) return null;
  return (
    <svg
      aria-hidden="true"
      className="rail-item__icon"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="square"
      strokeLinejoin="miter"
    >
      {paths[key]}
    </svg>
  );
}

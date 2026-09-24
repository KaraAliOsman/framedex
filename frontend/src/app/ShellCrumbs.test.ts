import { describe, expect, it } from "vitest";

import { crumbsFor } from "./ShellCrumbs";

describe("crumbsFor", () => {
  it("names rail destinations as the single crumb", () => {
    expect(crumbsFor("/dashboard", null, null)).toEqual([{ label: "Panel" }]);
    expect(crumbsFor("/production", null, null)).toEqual([{ label: "Producción" }]);
    expect(crumbsFor("/clients", null, null)).toEqual([{ label: "Clientes" }]);
    expect(crumbsFor("/catalogs/systems", null, null)).toEqual([
      { label: "Catálogos" },
      { label: "Sistemas" },
    ]);
  });

  it("walks rail → project → position leaf", () => {
    const crumbs = crumbsFor("/projects/p1/positions/x9/edit", "Casa García", "Dormitorio");
    expect(crumbs).toEqual([
      { label: "Proyectos", to: "/projects" },
      { label: "Casa García", to: "/projects/p1" },
      { label: "Dormitorio" },
    ]);
  });

  it("falls back honestly when the name or tag is missing", () => {
    expect(crumbsFor("/projects/p1", null, null)).toEqual([
      { label: "Proyectos", to: "/projects" },
      { label: "Proyecto" },
    ]);
    expect(crumbsFor("/projects/p1/positions/x9/edit", null, null)[2]).toEqual({
      label: "Vano",
    });
  });

  it("keeps the commercial-pricing deep link inside Precios, never the rail", () => {
    expect(crumbsFor("/pricing/commercial", null, null)).toEqual([
      { label: "Precios" },
      { label: "Cotización comercial" },
    ]);
  });
});

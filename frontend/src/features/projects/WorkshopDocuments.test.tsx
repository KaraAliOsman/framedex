import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { ProjectResponse } from "../../api/generated/models";
import { WorkshopDocuments, releasableVersion } from "./WorkshopDocuments";

afterEach(cleanup);

const project = (production_allowed: boolean) =>
  ({
    id: "p",
    current_revision: "REV-A",
    accepted_version_id: null,
    versions: [{ id: "v-a", revision_code: "REV-A", production_allowed }],
  }) as unknown as ProjectResponse;

describe("workshop documents", () => {
  it("offers the four print documents of a releasable revision", () => {
    render(<WorkshopDocuments project={project(true)} orgId="org" />);
    const section = screen.getByRole("region", { name: "Documentos para el taller" });
    for (const name of [
      /Orden de trabajo/,
      /Optimización de corte/,
      /Informe de vidrios/,
      /Listado de montaje/,
    ])
      expect(section.querySelector("button") && screen.getByRole("button", { name })).toBeTruthy();
  });

  it("stays out of the way while the work is quote-only", () => {
    expect(releasableVersion(project(false))).toBeNull();
    render(<WorkshopDocuments project={project(false)} orgId="org" />);
    expect(screen.queryByRole("region", { name: "Documentos para el taller" })).toBeNull();
  });
});

import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ArtifactDetail } from "./ArtifactDetail";

it("shows the current project-operation draft using its grounded position design", () => {
  render(
    <ArtifactDetail
      artifact={{
        kind: "project_draft",
        payload: {
          positions: [
            {
              id: "7dc75b24-97e8-4541-acb2-874b68b95688",
              position_index: 3,
              location_tag: "Dormitorio",
              quantity: 4,
              design: { nominal_width_mm: "2400.00", nominal_height_mm: "1800.00" },
            },
          ],
        },
      }}
    />,
  );
  expect(screen.getByText("Posición 3")).toBeTruthy();
  expect(screen.getByText("Dormitorio")).toBeTruthy();
  const dimensions = screen.getByText(/2\u2009400 × 1\u2009800/, { normalizer: (value) => value });
  expect(dimensions.className).toBe("ui-value");
  expect(dimensions.textContent).toBe("2\u2009400 × 1\u2009800 mm");
  expect(screen.getByText("4", { selector: ".ui-value" }).textContent).toBe("4 un.");
  expect(document.body.textContent).not.toContain("7dc75b24");
  expect(document.body.textContent).not.toContain("—");
});

it("keeps historical drafts readable with their actual measures and translated state", () => {
  render(
    <ArtifactDetail
      artifact={{
        kind: "project_draft",
        payload: {
          positions: [
            {
              label: "Ventana cocina",
              width_mm: "1000",
              height_mm: "800",
              quantity: 1,
              opening_type: "TURN_LEFT",
              state: "ready",
            },
          ],
        },
      }}
    />,
  );
  expect(screen.getByText("Ventana cocina")).toBeTruthy();
  expect(screen.getByText("Listo")).toBeTruthy();
  expect(screen.getByText(/Abatible izquierda/)).toBeTruthy();
  expect(screen.getByText(/1\u2009000 × 800/, { normalizer: (value) => value }).textContent).toBe(
    "1\u2009000 × 800 mm",
  );
});

it("does not manufacture zero prices for absent draft authority", () => {
  render(<ArtifactDetail artifact={{ kind: "quote_draft", payload: { totals: { net: null } } }} />);
  expect(screen.getByText("Sin dato")).toBeTruthy();
  expect(screen.getByText(/No hay un precio aplicado\./)).toBeTruthy();
  expect(document.body.textContent).not.toContain("$0");
});

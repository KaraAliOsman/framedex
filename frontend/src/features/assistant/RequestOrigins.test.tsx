import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";

import type { AiAgentStep } from "../../api/generated/models";
import { RequestOrigins } from "./RequestOrigins";

const REQUEST =
  "Hola, 2 ventanas oscilobatientes para el living de 1,20 por 1,40, una para el dormitorio de 1,20 x 1,00. Todo en PVC blanco.";
const living = "2 ventanas oscilobatientes para el living de 1,20 por 1,40";
const bedroom = "una para el dormitorio de 1,20 x 1,00";

function step(extra: Partial<AiAgentStep> = {}): AiAgentStep {
  return {
    kind: "project_ops",
    label: "Ventanas del mensaje",
    sources: [{ kind: "request", text: REQUEST }],
    origins: [
      {
        position_id: "a",
        location: "Living",
        source: 0,
        start: REQUEST.indexOf(living),
        end: REQUEST.indexOf(living) + living.length,
        quote: living,
      },
      {
        position_id: "b",
        location: "Dormitorio",
        source: 0,
        start: REQUEST.indexOf(bedroom),
        end: REQUEST.indexOf(bedroom) + bedroom.length,
        quote: bedroom,
      },
    ],
    assumptions: [
      {
        field: "opening",
        value: "Oscilobatiente izquierda",
        source: "agent",
        location: "Dormitorio",
        reason: "El mensaje no dice cómo abre.",
      },
      {
        field: "series",
        value: "PRO6004 · Proline",
        source: "usual",
        locations: ["Living", "Dormitorio"],
      },
    ],
    ...extra,
  };
}

it("marks each cited phrase in the request and numbers it like its window", () => {
  render(<RequestOrigins step={step()} />);
  const region = screen.getByRole("region", { name: "Origen de las ventanas" });
  const marks = region.querySelectorAll("mark");
  expect([...marks].map((mark) => mark.dataset.window)).toEqual(["1", "2"]);
  expect(marks[0]?.textContent).toBe(`${living}1`);
  const windows = within(screen.getByRole("list", { name: "Ventanas y su frase" })).getAllByRole(
    "listitem",
  );
  expect(windows[1]?.textContent).toContain(`Dormitorio · «${bedroom}»`);
});

it("asks to confirm what the agent chose and groups the company's usual values", () => {
  render(<RequestOrigins step={step()} />);
  const note = screen.getByRole("note");
  expect(note.textContent).toContain("1 supuesto que conviene confirmar");
  expect(note.textContent).toContain(
    "Dormitorio · Apertura: Oscilobatiente izquierda — El mensaje no dice cómo abre.",
  );
  expect(screen.getByText(/Lo habitual de tu empresa: serie PRO6004 · Proline/)).toBeTruthy();
});

it("renders nothing for a window change without a request origin", () => {
  const { container } = render(<RequestOrigins step={step({ origins: [] })} />);
  expect(container.innerHTML).toBe("");
});

import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AdvancedRecipesEditor } from "./AdvancedRecipesEditor";
import type { Capability } from "../canvas/physicalOpenings";

function Authoring(): JSX.Element {
  const [capability, setCapability] = useState<Capability>({
    movement: "LIFT_SLIDE",
    use: "WINDOW",
    direction: "INWARD",
    leaf_role: "SINGLE",
    fixed_in_sash: false,
    hinge_sides: ["NONE"],
    source: "Fixture de escritura, sin certificación",
    hardware_kit_skus: [],
    handle_rule: null,
    advanced_recipes: [],
  });
  return (
    <AdvancedRecipesEditor
      capability={capability}
      onChange={(advanced_recipes) => setCapability({ ...capability, advanced_recipes })}
    />
  );
}

function start(): void {
  render(<Authoring />);
  fireEvent.click(screen.getByRole("button", { name: "Agregar esquema desde fuente" }));
  fireEvent.click(screen.getByRole("button", { name: "Agregar panel desde fuente" }));
}

describe("exact sourced recipe authoring", () => {
  it("preserves every intermediate fractional keystroke and all sourced digits on blur", () => {
    start();
    const input = screen.getByLabelText("Proporción exacta del vano");
    const value = "0.333333333333333333333333333333333333";
    for (let end = 1; end <= value.length; end++) {
      fireEvent.change(input, { target: { value: value.slice(0, end) } });
      expect(input).toHaveValue(value.slice(0, end));
    }
    fireEvent.blur(input);
    expect(input).toHaveValue(value);
  });

  it("keeps a negative sign and accepts comma decimals without rounding", () => {
    start();
    const input = screen.getByLabelText("Retiro izquierdo · mm");
    for (const value of ["-", "-2", "-2,", "-2,500000000000000001"]) {
      fireEvent.change(input, { target: { value } });
      expect(input).toHaveValue(value);
    }
    fireEvent.blur(input);
    expect(input).toHaveValue("-2.500000000000000001");
  });

  it("explains an incomplete value on blur without clearing it or substituting zero", () => {
    start();
    const input = screen.getByLabelText("Fracción exacta del recorrido");
    fireEvent.change(input, { target: { value: "0." } });
    fireEvent.blur(input);
    expect(input).toHaveValue("0.");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("El valor escrito se conserva");
    fireEvent.change(input, { target: { value: "0.5" } });
    fireEvent.blur(input);
    expect(input).toHaveValue("0.5");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

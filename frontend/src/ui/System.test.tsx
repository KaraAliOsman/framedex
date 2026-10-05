import { fireEvent, render, screen } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import {
  Combobox,
  DataTable,
  EntityCode,
  Field,
  NumberField,
  OpeningGlyph,
  Popover,
  Button,
  ValidatedForm,
  validators,
} from "./index";

beforeAll(() =>
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  ),
);
describe("domain controls", () => {
  it.each(["2400", "2 400", "2.400", "1249,5"])("commits exact decimal input %s", (input) => {
    const commit = vi.fn();
    render(
      <Field label="Ancho">
        <NumberField value="" onValueChange={commit} decimals={1} suffix="mm" />
      </Field>,
    );
    const control = screen.getByLabelText("Ancho");
    fireEvent.focus(control);
    fireEvent.change(control, { target: { value: input } });
    fireEvent.blur(control);
    expect(commit).toHaveBeenLastCalledWith(input === "1249,5" ? "1249.5" : "2400");
  });
  it("rejects excessive precision without committing a float", () => {
    const commit = vi.fn();
    render(
      <Field label="Monto">
        <NumberField value="" onValueChange={commit} decimals={0} />
      </Field>,
    );
    fireEvent.focus(screen.getByLabelText("Monto"));
    fireEvent.change(screen.getByLabelText("Monto"), { target: { value: "12,5" } });
    fireEvent.blur(screen.getByLabelText("Monto"));
    expect(commit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("hasta 0 decimales");
    expect(screen.getByLabelText("Monto")).toHaveAttribute("aria-invalid", "true");
  });
  it("keeps a backend fraction unambiguous when focusing an exact input", () => {
    const commit = vi.fn();
    render(<NumberField aria-label="UF" value="1.249" decimals={4} onValueChange={commit} />);
    const input = screen.getByLabelText("UF");
    fireEvent.focus(input);
    expect(input).toHaveValue("1,249");
    fireEvent.change(input, { target: { value: "1,2491" } });
    expect(commit).toHaveBeenCalledWith("1.2491");
  });
  it("searches accented options and skips disabled choices by keyboard", () => {
    function Choice(): JSX.Element {
      const [value, setValue] = useState("");
      return (
        <Combobox
          label="Apertura"
          value={value}
          onValueChange={setValue}
          options={[
            { value: "x", label: "Sin autoridad", disabled: true },
            { value: "tilt", label: "Oscilobatiente" },
            { value: "slide", label: "Corredera" },
          ]}
        />
      );
    }
    render(<Choice />);
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "corre" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(input).toHaveValue("Corredera");
    expect(input).toHaveAttribute("aria-expanded", "false");
  });
  it("offers manual copy when the clipboard rejects", async () => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    render(<EntityCode code="PR-2026-001" kind="proyecto" />);
    fireEvent.click(screen.getByRole("button"));
    expect(await screen.findByLabelText("Código de proyecto para copiar")).toHaveValue(
      "PR-2026-001",
    );
  });
});

describe("Spanish validation edge", () => {
  it("prevents submit, announces errors and focuses the first invalid field", () => {
    const submit = vi.fn((event) => event.preventDefault());
    render(
      <ValidatedForm onSubmit={submit}>
        <label>
          Correo
          <input name="email" type="email" required />
        </label>
        <button type="submit">Guardar</button>
      </ValidatedForm>,
    );
    fireEvent.submit(screen.getByRole("button").closest("form")!);
    expect(submit).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Correo")).toHaveFocus();
    expect(screen.getByLabelText("Correo")).toHaveAccessibleName("Correo");
    expect(screen.getByLabelText("Correo")).toHaveAccessibleDescription("Completa este campo.");
    fireEvent.submit(screen.getByRole("button", { name: "Guardar" }).closest("form")!);
    expect(screen.getByLabelText("Correo")).toHaveAccessibleName("Correo");
    expect(screen.getByRole("alert")).toHaveTextContent("Completa este campo");
    expect(screen.getByRole("button", { name: "Guardar" }).closest("form")).toHaveAttribute(
      "novalidate",
    );
  });
  it("allows optional empty email and never shares checkbox consent", () => {
    const submit = vi.fn((event) => event.preventDefault());
    render(
      <ValidatedForm onSubmit={submit}>
        <label>
          Correo
          <input type="email" />
        </label>
        <label>
          Confirmación
          <input type="checkbox" required />
        </label>
        <input type="checkbox" defaultChecked aria-label="Otra opción" />
        <button type="submit">Guardar</button>
      </ValidatedForm>,
    );
    const form = screen.getByRole("button").closest("form")!;
    fireEvent.submit(form);
    expect(submit).not.toHaveBeenCalled();
    fireEvent.click(screen.getByLabelText("Confirmación"));
    fireEvent.submit(form);
    expect(submit).toHaveBeenCalledOnce();
  });
  it("uses the shared modulo-11 RUT validator", () => {
    expect(validators.rut("76.123.456-0")).toBeNull();
    expect(validators.rut("76.123.456-1")).toContain("dígito verificador");
  });
});

describe("tables and opening grammar", () => {
  it("sorts decimal strings beyond IEEE precision and filters without changing them", () => {
    const rows = [
      { id: "high", value: "9007199254740993" },
      { id: "low", value: "9007199254740992" },
    ];
    render(
      <DataTable
        rows={rows}
        rowKey={(row) => row.id}
        label="piezas"
        emptyReason="Sin piezas"
        columns={[{ id: "amount", label: "Monto", value: (row) => row.value, numeric: true }]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Monto" }));
    expect(screen.getAllByRole("row")[1]?.textContent).toBe(
      "9\u2009007\u2009199\u2009254\u2009740\u2009992",
    );
    fireEvent.change(screen.getByLabelText("Filtrar piezas"), { target: { value: "0993" } });
    expect(screen.getAllByRole("row")).toHaveLength(2);
  });
  it("virtualizes above 200 rows without discarding selection", () => {
    const changed = vi.fn();
    const rows = Array.from({ length: 400 }, (_, index) => ({
      id: `row-${index}`,
      value: String(index),
    }));
    render(
      <DataTable
        rows={rows}
        rowKey={(row) => row.id}
        label="piezas"
        emptyReason="Sin piezas"
        columns={[{ id: "qty", label: "Cantidad", value: (row) => row.value, numeric: true }]}
        onSelectionChange={changed}
        selectionActions={() => <Button onClick={() => undefined}>Revisar</Button>}
      />,
    );
    expect(screen.getAllByRole("row").length).toBeLessThan(60);
    fireEvent.click(screen.getByLabelText("Seleccionar fila 1"));
    expect(changed).toHaveBeenCalledWith(["row-0"]);
    expect(screen.getByRole("status")).toHaveTextContent("1 seleccionadas");
  });
  it("draws the vertex toward the handle and mirrors outside view", () => {
    const { container, rerender } = render(<OpeningGlyph type="TURN_LEFT" />);
    expect(container.querySelector('[data-symbol="turn"]')).toHaveAttribute("d", "M5 5L19 12L5 19");
    expect(container.querySelector("[data-handle]")).toHaveAttribute("d", "M20 11v3");
    rerender(<OpeningGlyph type="TURN_LEFT" view="exterior" />);
    expect(container.querySelector('[data-symbol="turn"]')).toHaveAttribute(
      "d",
      "M19 5L5 12L19 19",
    );
    expect(container.querySelector('[data-symbol="turn"]')).toHaveAttribute(
      "stroke-dasharray",
      "3 2",
    );
  });
  it("keeps sliding symbols parallel to the track and declares the view", () => {
    const { container } = render(<OpeningGlyph type="SLIDING_2L" />);
    expect(screen.getByRole("img")).toHaveAccessibleName(/Vista interior/);
    expect(container.querySelector('[data-symbol="turn"]')).toBeNull();
    expect(container.querySelector("[data-handle]")).toBeNull();
  });
  it("dismisses the previous operational layer and restores keyboard focus", () => {
    render(
      <>
        <Popover label="Uno" trigger={<Button>Uno</Button>}>
          <p>Primero</p>
        </Popover>
        <Popover label="Dos" trigger={<Button>Dos</Button>}>
          <p>Segundo</p>
        </Popover>
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Uno" }));
    fireEvent.click(screen.getByRole("button", { name: "Dos" }));
    expect(screen.queryByText("Primero")).toBeNull();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("Segundo")).toBeNull();
    expect(screen.getByRole("button", { name: "Dos" })).toHaveFocus();
  });
});

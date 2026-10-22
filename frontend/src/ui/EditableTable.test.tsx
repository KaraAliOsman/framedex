import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EditableTable, type EditableRow, type TableChange } from "./EditableTable";

afterEach(cleanup);
const columns = [{ id: "value", label: "Valor", kind: "decimal" as const, precision: 4, min: "0" }];
const fixtures = (length = 5): EditableRow[] =>
  Array.from({ length }, (_, index) => ({
    id: `rule-${index}`,
    label: `Regla ${index + 1}`,
    values: { value: "3.0000" },
  }));

function setup({
  rows = fixtures(),
  save = vi.fn<(changes: TableChange[]) => Promise<void>>().mockResolvedValue(undefined),
  readOnly = false,
  pageSize = 50,
} = {}) {
  function Harness() {
    const [current, setCurrent] = useState(rows);
    return (
      <EditableTable
        label="Reglas"
        columns={columns}
        rows={current}
        readOnly={readOnly}
        pageSize={pageSize}
        onSave={async (changes) => {
          await save(changes);
          setCurrent((previous) =>
            previous.map((row) => ({
              ...row,
              values: {
                ...row.values,
                ...Object.fromEntries(
                  changes
                    .filter((item) => item.rowId === row.id)
                    .map((item) => [item.columnId, item.value]),
                ),
              },
            })),
          );
        }}
      />
    );
  }
  render(<Harness />);
  return save;
}

function paste(text: string, input = screen.getByRole("textbox", { name: "Regla 1 · Valor" })) {
  fireEvent.paste(input, { clipboardData: { getData: () => text } });
}

describe("EditableTable", () => {
  it("saves five Excel rows atomically and preserves all four decimals and large integers", async () => {
    const save = setup();
    paste("1,2345\r\n2,0001\r\n9007199254740993,1234\r\n0\r\n5,4321\r\n");
    expect(save).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![0].map((item) => item.value)).toEqual([
      "1.2345",
      "2.0001",
      "9007199254740993.1234",
      "0",
      "5.4321",
    ]);
    await screen.findByText("Guardado");
    expect(screen.getByRole("textbox", { name: "Regla 3 · Valor" })).toHaveValue(
      "9007199254740993,1234",
    );
  });

  it("keeps an invalid batch local until the failing cell is corrected", async () => {
    const save = setup();
    paste("1,2345\n-4\n3,44444");
    expect(screen.getByText("Usa un valor de al menos 0.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Regla 3 · Valor" })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: "Regla 2 · Valor" }), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Regla 3 · Valor" }), {
      target: { value: "3,4444" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![0]).toHaveLength(3);
  });

  it("validates a pasted column using each row's actual nullability, scale and bounds", async () => {
    const rows = fixtures(3).map((row, index) => ({
      ...row,
      cellOptions: {
        value:
          index === 0
            ? { precision: 2, nullable: false, min: "0", max: "99.99" }
            : index === 1
              ? { precision: 4, nullable: true, min: "0.0001", max: "9999.9999" }
              : { precision: 2, nullable: true, min: "0" },
      },
    }));
    const save = setup({ rows });
    paste("100\n1,2345\n");
    expect(screen.getByText("Usa un valor de hasta 99,99.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Regla 2 · Valor" })).not.toHaveAttribute(
      "aria-invalid",
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Regla 1 · Valor" }), {
      target: { value: "" },
    });
    expect(screen.getByText("Completa este valor.")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Regla 1 · Valor" }), {
      target: { value: "0" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Regla 3 · Valor" }), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![0].map((change) => change.value)).toEqual(["0", "1.2345", null]);
  });

  it("refuses a block that would overflow without partially overwriting cells", () => {
    const save = setup();
    paste("1\t2\n3\t4");
    expect(screen.getByRole("alert")).toHaveTextContent("El bloque no cabe");
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveValue("3,0000");
    expect(save).not.toHaveBeenCalled();
  });

  it("undoes a pending paste locally, then undoes a saved batch with a new write", async () => {
    const save = setup();
    paste("5,1234\n6,1234");
    fireEvent.click(screen.getByRole("button", { name: "Deshacer" }));
    expect(save).not.toHaveBeenCalled();
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveValue("3,0000");
    paste("5,1234\n6,1234");
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("Guardado");
    fireEvent.click(screen.getByRole("button", { name: "Deshacer" }));
    await waitFor(() => expect(save).toHaveBeenCalledTimes(2));
    expect(save.mock.calls[1]![0].map((item) => item.value)).toEqual(["3.0000", "3.0000"]);
    await screen.findByText("Guardado");
    expect(screen.getByRole("button", { name: "Deshacer" })).toBeDisabled();
  });

  it("retains changes after a conflict and retries only on a human action", async () => {
    const save = vi
      .fn<(changes: TableChange[]) => Promise<void>>()
      .mockRejectedValueOnce(new Error("La serie cambió. Revisa los cambios antes de guardar."))
      .mockResolvedValue(undefined);
    setup({ save });
    paste("4,5");
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("La serie cambió");
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveValue("4,5");
    expect(save).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("Guardado");
    expect(save).toHaveBeenCalledTimes(2);
  });

  it("moves by arrow and Tab across pagination and restores the cell with Escape", async () => {
    setup({ pageSize: 2 });
    const first = screen.getByRole("textbox", { name: "Regla 1 · Valor" });
    first.focus();
    fireEvent.change(first, { target: { value: "8,25" } });
    fireEvent.keyDown(first, { key: "Escape" });
    expect(first).toHaveValue("3,0000");
    fireEvent.keyDown(first, { key: "ArrowDown" });
    const second = screen.getByRole("textbox", { name: "Regla 2 · Valor" });
    await waitFor(() => expect(second).toHaveFocus());
    fireEvent.keyDown(second, { key: "Tab" });
    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Regla 3 · Valor" })).toHaveFocus(),
    );
    expect(screen.queryByRole("textbox", { name: "Regla 1 · Valor" })).not.toBeInTheDocument();
  });

  it("pastes from the keyboard-accessible dialog and preserves zero distinct from empty", () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: "Pegar desde Excel" }));
    fireEvent.change(screen.getByLabelText("Copia las celdas en Excel y pégalas aquí."), {
      target: { value: "0\n" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Pegar bloque" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveValue("0");
  });

  it("keeps consultation access read-only and renders only one page of 300 profiles", () => {
    setup({ rows: fixtures(300), readOnly: true });
    expect(screen.getAllByRole("textbox")).toHaveLength(50);
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveAttribute("readonly");
    expect(screen.queryByRole("button", { name: "Guardar cambios" })).not.toBeInTheDocument();
    expect(screen.getByText("1–50 de 300")).toBeInTheDocument();
  });

  it("opens the page containing a requested pending cell and focuses it", async () => {
    render(
      <EditableTable
        label="Reglas"
        columns={columns}
        rows={fixtures(300)}
        onSave={async () => undefined}
        focusRequest={{ rowId: "rule-249", columnId: "value" }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Regla 250 · Valor" })).toHaveFocus(),
    );
    expect(screen.getByText("201–250 de 300")).toBeInTheDocument();
  });

  it("keeps the new page reachable with Tab after using pagination buttons", () => {
    setup({ pageSize: 2 });
    screen.getByRole("textbox", { name: "Regla 1 · Valor" }).focus();
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByRole("textbox", { name: "Regla 3 · Valor" })).toHaveAttribute(
      "tabindex",
      "0",
    );
    expect(screen.getByRole("textbox", { name: "Regla 4 · Valor" })).toHaveAttribute(
      "tabindex",
      "-1",
    );
  });

  it("starts a dialog paste in the first editable column without overwriting its label", () => {
    render(
      <EditableTable
        label="Reglas"
        columns={[{ id: "applies", label: "Se aplica a", readOnly: true }, ...columns]}
        rows={[{ id: "one", label: "Holgura", values: { applies: "Marco", value: "3.00" } }]}
        onSave={async () => undefined}
      />,
    );
    expect(screen.getByRole("textbox", { name: "Holgura · Valor" })).toHaveAttribute(
      "tabindex",
      "0",
    );
    fireEvent.click(screen.getByRole("button", { name: "Pegar desde Excel" }));
    fireEvent.change(screen.getByLabelText("Copia las celdas en Excel y pégalas aquí."), {
      target: { value: "4,25" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Pegar bloque" }));
    expect(screen.getByRole("textbox", { name: "Holgura · Valor" })).toHaveValue("4,25");
    expect(screen.getByRole("textbox", { name: "Holgura · Se aplica a" })).toHaveValue("Marco");
  });

  it("refuses to undo over a different current value received from the server", async () => {
    const save = vi.fn<(changes: TableChange[]) => Promise<void>>().mockResolvedValue(undefined);
    const { rerender } = render(
      <EditableTable label="Reglas" columns={columns} rows={fixtures(1)} onSave={save} />,
    );
    paste("4,00");
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("Guardado");
    rerender(
      <EditableTable
        label="Reglas"
        columns={columns}
        rows={[{ ...fixtures(1)[0]!, values: { value: "8.00" } }]}
        onSave={save}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Deshacer" }));
    expect(save).toHaveBeenCalledOnce();
    expect(screen.getByRole("alert")).toHaveTextContent("La celda cambió después de tu edición");
    expect(screen.getByRole("textbox", { name: "Regla 1 · Valor" })).toHaveValue("8,00");
  });
});

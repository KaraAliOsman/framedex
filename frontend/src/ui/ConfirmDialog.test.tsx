import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmProvider, useConfirm } from "./ConfirmDialog";

function TwoConfirms({ first, second }: { first: () => void; second: () => void }): JSX.Element {
  const confirm = useConfirm();
  return (
    <>
      <button onClick={() => void confirm({ title: "Primera" }).then(first)}>primero</button>
      <button onClick={() => void confirm({ title: "Segunda" }).then(second)}>segundo</button>
    </>
  );
}

describe("ConfirmProvider queue", () => {
  it("does not strand the first caller when a second confirm opens over it", async () => {
    const first = vi.fn();
    const second = vi.fn();
    render(
      <ConfirmProvider>
        <TwoConfirms first={first} second={second} />
      </ConfirmProvider>,
    );
    fireEvent.click(screen.getByText("primero"));
    fireEvent.click(screen.getByText("segundo"));

    // The first dialog still owns the surface; the second waits its turn.
    expect(await screen.findByText("Primera")).toBeInTheDocument();
    expect(second).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    await waitFor(() => expect(first).toHaveBeenCalledWith(true));
    expect(await screen.findByText("Segunda")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    await waitFor(() => expect(second).toHaveBeenCalledWith(false));
  });
});

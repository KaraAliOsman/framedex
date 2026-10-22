import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { Dialog } from "./Dialog";

afterEach(cleanup);
it("keeps keyboard focus in the visible enabled step and makes the scroll body reachable", () => {
  render(
    <Dialog title="Alta por pasos" onClose={() => {}}>
      <button>Continuar</button>
      <section hidden>
        <button>Publicar paso oculto</button>
      </section>
      <fieldset disabled>
        <button>Guardar paso bloqueado</button>
      </fieldset>
    </Dialog>,
  );
  const close = screen.getByRole("button", { name: "Cerrar" });
  close.focus();
  fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
  expect(screen.getByRole("button", { name: "Continuar" })).toHaveFocus();
  fireEvent.keyDown(document, { key: "Tab" });
  expect(close).toHaveFocus();
  expect(document.querySelector(".ui-dialog__body")).toHaveAttribute("tabindex", "0");
});

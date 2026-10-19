import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { ApiError, apiFetchBlob } from "../../api/apiMutator";
import { QuickPdfMenu } from "./QuickPdfMenu";

vi.mock("../../api/apiMutator", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/apiMutator")>();
  return { ...actual, apiFetchBlob: vi.fn() };
});

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  URL.createObjectURL = vi.fn(() => "blob:draft");
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test("every document is one click away and needs no previous step", async () => {
  vi.mocked(apiFetchBlob).mockResolvedValue({
    blob: new Blob(["%PDF"], { type: "application/pdf" }),
    filename: "hoja-de-corte-borrador.pdf",
  });
  render(<QuickPdfMenu projectId="work-1" orgId="org-a" />);
  fireEvent.click(screen.getByRole("button", { name: "Sacar PDF" }));
  expect(screen.getByText(/Con un nombre y una ventana/)).toBeInTheDocument();
  for (const label of ["Cotización borrador", "Hoja de corte", "Plano de ventanas", "Materiales"])
    expect(screen.getByRole("menuitem", { name: new RegExp(label) })).toBeEnabled();

  fireEvent.click(screen.getByRole("menuitem", { name: /Hoja de corte/ }));
  await screen.findByRole("link", { name: "Abrir hoja de corte" });
  const [url, options] = vi.mocked(apiFetchBlob).mock.calls[0]!;
  expect(url).toContain("/documents/projects/work-1/quick-draft/");
  expect(JSON.parse(String(options?.body))).toEqual({ document: "CUT" });
  expect(new Headers(options?.headers).get("X-Organization-ID")).toBe("org-a");
});

test("a refusal explains itself next to the button", async () => {
  vi.mocked(apiFetchBlob).mockRejectedValue(
    new ApiError(422, {
      error: { code: "revision_not_available", detail: "Esta obra ya tiene una versión emitida." },
    }),
  );
  render(<QuickPdfMenu projectId="work-1" orgId="org-a" />);
  fireEvent.click(screen.getByRole("button", { name: "Sacar PDF" }));
  fireEvent.click(screen.getByRole("menuitem", { name: /Plano de ventanas/ }));
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent("Esta obra ya tiene una versión emitida."),
  );
});

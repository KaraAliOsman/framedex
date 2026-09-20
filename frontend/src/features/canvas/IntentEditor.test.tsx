import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { engineCalculate, engineLayout } from "../../api/generated/dekopen";
import type { EngineCalculateResponse } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { useCanvasStore } from "./canvasStore";
import { IntentEditor } from "./IntentEditor";

vi.mock("../../api/generated/dekopen", () => ({
  engineLayout: vi.fn().mockResolvedValue({ status: 200, data: { nodes: [] } }),
  engineCalculate: vi.fn(),
}));

const calculate = vi.mocked(engineCalculate);
const response: Awaited<ReturnType<typeof engineCalculate>> = {
  status: 200,
  headers: new Headers(),
  data: {
    profile_cuts: [],
    reinforcements: [],
    glasses: [],
    hardware_items: [],
    panels: [],
    leaf_weights: [],
    calculation_hash: `sha256:${"0".repeat(64)}`,
  } satisfies EngineCalculateResponse,
};

beforeEach(() => {
  calculate.mockReset();
  useCanvasStore.getState().reset();
  useCanvasStore.getState().setSystemId("system-a");
});

function editWidth(value: string): void {
  fireEvent.change(screen.getByLabelText(t("intent.width")), {
    target: { value },
  });
  fireEvent.click(
    screen.getByRole("button", {
      name: t("intent.applyDimensions"),
    }),
  );
}

it("commits only after engine accepts and submits exact decimal strings", async () => {
  calculate.mockResolvedValue(response);
  const onCalculated = vi.fn();
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{}}
      onCalculated={onCalculated}
    />,
  );

  editWidth("1200,25");

  await waitFor(() => expect(onCalculated).toHaveBeenCalledOnce());
  expect(calculate.mock.calls[0]?.[0]).toMatchObject({
    nominal_width_mm: "1200.25",
    nominal_height_mm: "1000.00",
  });
  expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1200.25");
});

it("keeps the accepted design when engine rejects", async () => {
  calculate.mockRejectedValue(new Error("raw technical error"));
  const before = useCanvasStore.getState().inputs;
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{}}
      onCalculated={vi.fn()}
    />,
  );

  editWidth("1200");

  await screen.findByRole("alert");
  expect(useCanvasStore.getState().inputs).toBe(before);
  expect(screen.queryByText("raw technical error")).toBeNull();
  expect(screen.getByRole("button", { name: t("intent.review") })).toBeVisible();
});

it("restores the accepted opening after a rejected opening change", async () => {
  calculate.mockRejectedValue(new Error("opening rejected"));
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{}}
      onCalculated={vi.fn()}
    />,
  );

  fireEvent.change(screen.getByLabelText(t("intent.opening")), {
    target: { value: "TURN_RIGHT" },
  });

  await screen.findByRole("alert");
  expect(screen.getByLabelText(t("intent.opening"))).toHaveValue("FIXED");
  expect(useCanvasStore.getState().inputs.parametricTree.opening_type).toBe("FIXED");
});

it("does not overwrite a new loaded design with a late response", async () => {
  let resolve!: (value: typeof response) => void;
  calculate.mockImplementation(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const onCalculated = vi.fn();
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{}}
      onCalculated={onCalculated}
    />,
  );

  editWidth("1200");
  act(() => useCanvasStore.getState().reset());
  await act(async () => resolve(response));

  expect(onCalculated).not.toHaveBeenCalled();
  expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1000.00");
  expect(screen.getByRole("alert")).toHaveTextContent(t("intent.stale"));
});

it("does not commit after the position editor unmounts", async () => {
  let resolve!: (value: typeof response) => void;
  calculate.mockImplementation(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const onCalculated = vi.fn();
  const view = render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{}}
      onCalculated={onCalculated}
    />,
  );

  editWidth("1200");
  view.unmount();
  await act(async () => resolve(response));

  expect(onCalculated).not.toHaveBeenCalled();
  expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1000.00");
});

it("only offers divisions backed by effective catalog articles", () => {
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{ SPLIT_V: { sku: "INTERNAL-SKU", name: "Poste vertical" } }}
      onCalculated={vi.fn()}
    />,
  );

  expect(
    screen.getByRole("button", {
      name: t("intent.vertical"),
    }),
  ).toBeDisabled();
  expect(
    screen.queryByRole("button", {
      name: new RegExp(t("intent.horizontal")),
    }),
  ).toBeNull();
  expect(screen.queryByText("INTERNAL-SKU")).toBeNull();
});

it("uses engine horizontal shortcut authority and validates the candidate", async () => {
  vi.mocked(engineLayout).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      calculation_hash: "sha256:" + "0".repeat(64),
      nodes: [
        {
          node_id: "g1",
          width_mm: "2000",
          height_mm: "1200",
          vertical: { half: "1000.00", one_third: "666.67", two_thirds: "1333.33" },
          horizontal: { half: "600.00", one_third: "400.00", two_thirds: "800.00" },
          child_weights: [],
        },
      ],
    },
  });
  calculate.mockResolvedValue(response);
  const onCalculated = vi.fn();
  render(
    <IntentEditor
      organizationId="org-a"
      onValidationChange={vi.fn()}
      mullions={{ SPLIT_H: { sku: "POST-H", name: "Travesano" } }}
      onCalculated={onCalculated}
    />,
  );
  const shortcut = screen.getByRole("button", {
    name: `${t("intent.horizontal")} \u00b7 ${t("intent.half")}`,
  });
  await waitFor(() => expect(shortcut).toBeEnabled());
  fireEvent.click(shortcut);
  await waitFor(() => expect(calculate).toHaveBeenCalled());
  expect(calculate.mock.calls[0]![0].parametric_tree).toMatchObject({
    type: "SPLIT_H",
    split_offset_mm: "600.00",
  });
});

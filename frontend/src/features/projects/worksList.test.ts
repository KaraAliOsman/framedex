import { describe, expect, it } from "vitest";
import type { ProjectResponse } from "../../api/generated/models";
import { filterWorks, pageOffset, workAmount } from "./worksList";

const work = (overrides: Partial<ProjectResponse> = {}): ProjectResponse => ({
  id: "1",
  code: "P-1",
  name: "Casa Ñuble",
  client_name: "Ana Pérez",
  status: "DRAFT",
  current_revision: "REV-B",
  total_price_net: "999",
  total_price_tax: "189.81",
  total_price_gross: "1188.81",
  currency: "CLP",
  pricing_current: false,
  current_pricing_operation_id: null,
  position_count: 500,
  updated_at: "2026-10-22T09:00:00Z",
  progress: { stage: "QUOTING", quoted_total: null, currency: null, reason: "Preparación" },
  ...overrides,
});

describe("works list", () => {
  it("uses the exact selected issued total over applied or old project totals", () => {
    expect(
      workAmount(
        work({
          status: "APPROVED",
          pricing_current: true,
          progress: {
            stage: "ACCEPTED",
            quoted_total: "99999999999999999999.9901",
            currency: "UF",
            reason: "Elegida",
          },
        }),
      ),
    ).toEqual({
      value: "99999999999999999999.9901",
      currency: "UF",
      origin: "Total de la cotización vigente",
    });
  });
  it("never presents a historical total as an unpriced successor's sale", () => {
    expect(workAmount(work())).toBeNull();
    expect(workAmount(work({ pricing_current: true }))).toEqual({
      value: "1188.81",
      currency: "CLP",
      origin: "Precio aplicado de esta revisión",
    });
  });
  it("keeps old status links exact, searches name/client/code and sorts before pagination", () => {
    const draft = work();
    const issued = work({ id: "2", code: "P-2", name: "Casa A", status: "QUOTED" });
    const items = [draft, issued];
    expect(filterWorks(items, " ANA PÉREZ ", "QUOTED", "name")).toEqual([issued]);
    expect(filterWorks(items, "casa", "", "name")).toEqual([issued, draft]);
    expect(filterWorks(items, "p-1", "", "updated")).toEqual([draft]);
    expect(items).toEqual([draft, issued]);
  });
  it.each([null, "-1", "NaN", "Infinity", "1.5", "9007199254740992"])(
    "rejects malformed offset %s",
    (offset) => {
      expect(pageOffset(offset)).toBe(0);
    },
  );
  it("normalizes an offset to its page without losing the last 50 of 500", () => {
    expect(pageOffset("499")).toBe(450);
    expect(pageOffset("50")).toBe(50);
  });
});

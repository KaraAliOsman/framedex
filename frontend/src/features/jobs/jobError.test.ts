import { expect, test } from "vitest";

import { jobErrorKey } from "./jobError";

test("account limits are named as such, never as a provider outage", () => {
  expect(jobErrorKey("ai_entitlement_required")).toBe("jobs.fail.plan");
  expect(jobErrorKey("insufficient_credits")).toBe("jobs.fail.credits");
  expect(jobErrorKey("ai_provider_timeout")).toBe("jobs.fail.provider");
  expect(jobErrorKey("ai_job_failed")).toBe("jobs.fail.generic");
});

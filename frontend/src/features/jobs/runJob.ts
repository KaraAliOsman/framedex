import { jobsEnqueue, jobsGet } from "../../api/generated/dekopen";
import type { JobEnqueueRequest, JobRun } from "../../api/generated/models";

const TERMINAL_STATES = new Set(["SUCCEEDED", "FAILED", "CANCELED"]);
const POLL_MS = 1200;
const TIMEOUT_MS = 180000;

export class JobFailedError extends Error {
  readonly job: JobRun;

  constructor(job: JobRun) {
    super(`job_${job.state.toLowerCase()}`);
    this.job = job;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Enqueue a durable job and poll until it reaches a terminal state.
 * Non-2xx responses reject inside apiMutator as ApiError. */
export async function runJob(
  request: JobEnqueueRequest,
  requestOptions: Parameters<typeof jobsEnqueue>[1],
  onUpdate?: (job: JobRun) => void,
): Promise<JobRun> {
  const enqueued = await jobsEnqueue(request, requestOptions);
  let job = enqueued.data;
  onUpdate?.(job);
  const deadline = Date.now() + TIMEOUT_MS;
  while (!TERMINAL_STATES.has(job.state) && Date.now() < deadline) {
    await sleep(POLL_MS);
    const polled = await jobsGet(job.id, requestOptions);
    job = polled.data;
    onUpdate?.(job);
  }
  if (job.state !== "SUCCEEDED") {
    throw new JobFailedError(job);
  }
  return job;
}

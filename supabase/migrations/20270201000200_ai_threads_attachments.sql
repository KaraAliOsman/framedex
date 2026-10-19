-- Dirección final 05 · copiloto global: hilos privados, adjuntos y política sellada.
--
-- ai_threads is the private conversation identity per organization/person.
-- A thread groups the existing durable jobs (Trabajo) and ask turns (Chat
-- legacy); transcripts, artifacts and outcomes stay where they already are.
-- The destination of a write belongs to each turn/job, never to the thread.
-- ai_attachments persists private files added from the popup composer with
-- hash, coverage and the extracted text parts that keep their origin
-- (página, hoja!celda, párrafo, línea). Nothing here grants a new spend path:
-- reading a file never debits by itself; the run keeps its existing
-- reservation and receipt.

CREATE TABLE IF NOT EXISTS public.ai_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'Conversación' CHECK (char_length(title) BETWEEN 1 AND 120),
  interaction_mode TEXT NOT NULL DEFAULT 'chat' CHECK (interaction_mode IN ('chat', 'work')),
  autonomy TEXT NOT NULL DEFAULT 'approve' CHECK (autonomy IN ('propose', 'approve', 'draft')),
  origin TEXT NOT NULL DEFAULT 'popup' CHECK (origin IN ('popup', 'legacy_job', 'legacy_ask')),
  -- Traceable link for migrated history: 'job:<uuid>' or 'ask:<surface>:<refs>'.
  legacy_key TEXT,
  archived_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ai_threads_legacy_key
  ON public.ai_threads (org_id, user_id, legacy_key) WHERE legacy_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS ai_threads_recent
  ON public.ai_threads (org_id, user_id, archived_at, last_activity_at DESC, id DESC);

ALTER TABLE public.ai_jobs ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES public.ai_threads(id) ON DELETE SET NULL;
ALTER TABLE public.ai_jobs ADD COLUMN IF NOT EXISTS interaction_mode TEXT
  CHECK (interaction_mode IS NULL OR interaction_mode IN ('chat', 'work'));
ALTER TABLE public.ai_jobs ADD COLUMN IF NOT EXISTS autonomy TEXT
  CHECK (autonomy IS NULL OR autonomy IN ('propose', 'approve', 'draft'));
ALTER TABLE public.ai_jobs ADD COLUMN IF NOT EXISTS receipt JSONB;
ALTER TABLE public.ai_ask_turns ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES public.ai_threads(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ai_jobs_thread ON public.ai_jobs (thread_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS ai_ask_turns_thread ON public.ai_ask_turns (thread_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS public.ai_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  thread_id UUID REFERENCES public.ai_threads(id) ON DELETE SET NULL,
  file_name TEXT NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 200),
  media_type TEXT NOT NULL CHECK (char_length(media_type) BETWEEN 1 AND 120),
  kind TEXT NOT NULL CHECK (kind IN ('PDF', 'IMAGE', 'XLSX', 'CSV', 'DOCX', 'TEXT')),
  byte_size BIGINT NOT NULL CHECK (byte_size > 0),
  file_sha256 CHAR(64) NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
  storage_path TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('READY', 'PARTIAL', 'UNREADABLE')),
  -- {parts:[{ref,text}], visual:[refs], coverage:{unit,total,processed,unprocessed[]}}
  extract JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (storage_path LIKE 'ai-attachments/' || org_id::text || '/%')
);
CREATE INDEX IF NOT EXISTS ai_attachments_owner ON public.ai_attachments (org_id, user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ai_attachments_thread ON public.ai_attachments (thread_id, created_at);

ALTER TABLE public.ai_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_attachments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ai_threads_select ON public.ai_threads;
CREATE POLICY ai_threads_select ON public.ai_threads FOR SELECT
  USING (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());
DROP POLICY IF EXISTS ai_threads_insert ON public.ai_threads;
CREATE POLICY ai_threads_insert ON public.ai_threads FOR INSERT TO ai_backend
  WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());
DROP POLICY IF EXISTS ai_threads_update ON public.ai_threads;
CREATE POLICY ai_threads_update ON public.ai_threads FOR UPDATE TO ai_backend
  USING (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid())
  WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());

DROP POLICY IF EXISTS ai_attachments_select ON public.ai_attachments;
CREATE POLICY ai_attachments_select ON public.ai_attachments FOR SELECT
  USING (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());
DROP POLICY IF EXISTS ai_attachments_insert ON public.ai_attachments;
CREATE POLICY ai_attachments_insert ON public.ai_attachments FOR INSERT TO ai_backend
  WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());
DROP POLICY IF EXISTS ai_attachments_update ON public.ai_attachments;
CREATE POLICY ai_attachments_update ON public.ai_attachments FOR UPDATE TO ai_backend
  USING (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid())
  WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND user_id = auth.uid());

-- Member-facing roles read their own rows; only the API (ai_backend) writes.
REVOKE ALL ON public.ai_threads, public.ai_attachments FROM anon, authenticated;
GRANT SELECT ON public.ai_threads, public.ai_attachments TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.ai_threads, public.ai_attachments TO ai_backend;
-- The new ai_jobs columns are written only through the API role.
GRANT UPDATE (thread_id, interaction_mode, autonomy, receipt) ON public.ai_jobs TO ai_backend;

-- Legacy history: every earlier job gets its own traceable thread; earlier
-- ask turns are grouped by their exact (person, surface, refs) — the same
-- identity the old dock used — never merged by heuristics. Idempotent: the
-- unique legacy_key and the NULL thread_id filters make re-runs no-ops.
INSERT INTO public.ai_threads (org_id, user_id, title, interaction_mode, autonomy, origin, legacy_key,
                               created_at, updated_at, last_activity_at)
SELECT j.org_id, j.user_id,
       left(coalesce(nullif(btrim(regexp_replace(j.goal, '\s+', ' ', 'g')), ''), 'Trabajo anterior'), 120),
       'work', 'propose', 'legacy_job', 'job:' || j.id::text,
       j.created_at, j.updated_at, coalesce(j.completed_at, j.updated_at, j.created_at)
FROM public.ai_jobs j
WHERE j.thread_id IS NULL
ON CONFLICT DO NOTHING;

UPDATE public.ai_jobs j SET thread_id = t.id
FROM public.ai_threads t
WHERE j.thread_id IS NULL AND t.org_id = j.org_id AND t.user_id = j.user_id
  AND t.legacy_key = 'job:' || j.id::text;

INSERT INTO public.ai_threads (org_id, user_id, title, interaction_mode, autonomy, origin, legacy_key,
                               created_at, updated_at, last_activity_at)
SELECT a.org_id, a.user_id,
       left(coalesce(nullif(btrim(regexp_replace(min(a.question), '\s+', ' ', 'g')), ''), 'Conversación anterior'), 120),
       'chat', 'propose', 'legacy_ask', 'ask:' || a.surface || ':' || md5(a.refs::text),
       min(a.created_at), max(a.created_at), max(a.created_at)
FROM public.ai_ask_turns a
WHERE a.thread_id IS NULL
GROUP BY a.org_id, a.user_id, a.surface, a.refs
ON CONFLICT DO NOTHING;

UPDATE public.ai_ask_turns a SET thread_id = t.id
FROM public.ai_threads t
WHERE a.thread_id IS NULL AND t.org_id = a.org_id AND t.user_id = a.user_id
  AND t.legacy_key = 'ask:' || a.surface || ':' || md5(a.refs::text);

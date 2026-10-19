-- The member project reader uses column-level SELECT grants. New project
-- defaults and quotation numbers need the same read access as project metadata;
-- existing tenant RLS and write policies continue to govern every row.
GRANT SELECT (design_defaults, commercial_number)
  ON public.projects TO authenticated;

-- project_versions.snapshot_json was added to the sealed-evidence payload but
-- never entered the shot-09 column-grant enumeration: reads of the version
-- snapshot (production trace, §11 forward chain) fail with SQLSTATE 42501 on
-- every correctly migrated DB. Grant it; pdf_storage_path stays ungranted —
-- internal object keys are only reachable through signed URLs.
GRANT SELECT (snapshot_json) ON public.project_versions TO authenticated;

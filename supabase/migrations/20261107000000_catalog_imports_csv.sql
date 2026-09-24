-- §6: supplier price lists also arrive as CSV — admit the kind end-to-end.
ALTER TABLE public.catalog_imports
    DROP CONSTRAINT catalog_imports_kind,
    ADD CONSTRAINT catalog_imports_kind CHECK (kind IN ('PDF', 'XLSX', 'CSV', 'IMAGE'));

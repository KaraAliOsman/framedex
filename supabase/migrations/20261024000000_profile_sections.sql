-- §15 catalog profile sections: an optional simplified technical cross-section
-- per profile article. NULL keeps the honest "no section declared" state; the
-- renderer then falls back to an explicitly approximate box.
ALTER TABLE public.profile_articles
    ADD COLUMN section JSONB;

COMMENT ON COLUMN public.profile_articles.section IS
    'Simplified technical cross-section ({source, polygon[], depth_mm, axes[], drawing_ref?}). POLYGON = declared simplified section; DXF_REFERENCE = shape from a manufacturer drawing. NULL = not declared.';

ALTER TABLE public.profile_articles
    ADD CONSTRAINT profile_articles_section_shape
    CHECK (
        section IS NULL
        OR (
            jsonb_typeof(section) = 'object'
            AND section ? 'source'
            AND section ? 'polygon'
            AND section ? 'depth_mm'
            AND jsonb_typeof(section->'polygon') = 'array'
            AND jsonb_array_length(section->'polygon') >= 3
        )
    );

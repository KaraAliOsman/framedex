-- §8 profile sections: declared interpretation facts (orientation, local
-- origin) join the section payload, and revision tracking becomes real
-- columns so a section change is an auditable row event. Stamps live outside
-- the JSONB — a stamp inside the payload would ride the value it audits.

ALTER TABLE public.profile_articles
    ADD COLUMN section_revision INT NOT NULL DEFAULT 1
        CHECK (section_revision >= 1),
    ADD COLUMN section_revised_at TIMESTAMPTZ,
    ADD COLUMN section_revised_by UUID;

COMMENT ON COLUMN public.profile_articles.section_revision IS
    'Monotonic counter bumped on every section geometry/provenance change.';
COMMENT ON COLUMN public.profile_articles.section_revised_at IS
    'Timestamp of the last section change (NULL = never set through the app).';
COMMENT ON COLUMN public.profile_articles.section_revised_by IS
    'Actor id of the last section change.';

-- Sections written before the keys existed are NOT backfilled: an UPDATE on
-- an article of a technically locked system trips the catalog freeze trigger
-- and would abort the whole migration on populated databases. Legacy rows
-- load with the declared defaults at read time (EXTERIOR_DOWN exterior face,
-- TOP_LEFT origin — serializer and engine defaults). The new shape CHECK is
-- therefore added NOT VALID: pre-existing rows stay untouched, every new or
-- updated section must declare orientation and local_origin.
ALTER TABLE public.profile_articles
    DROP CONSTRAINT profile_articles_section_shape;
ALTER TABLE public.profile_articles
    ADD CONSTRAINT profile_articles_section_shape
    CHECK (
        section IS NULL
        OR (
            jsonb_typeof(section) = 'object'
            AND section ? 'source'
            AND section ? 'polygon'
            AND section ? 'depth_mm'
            AND section ? 'orientation'
            AND section ? 'local_origin'
            AND jsonb_typeof(section->'polygon') = 'array'
            AND jsonb_array_length(section->'polygon') >= 3
            AND section->>'orientation' IN (
                'EXTERIOR_DOWN', 'EXTERIOR_UP', 'EXTERIOR_LEFT', 'EXTERIOR_RIGHT'
            )
            AND section->>'local_origin' IN (
                'TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_LEFT', 'BOTTOM_RIGHT', 'CENTROID'
            )
        )
    ) NOT VALID;

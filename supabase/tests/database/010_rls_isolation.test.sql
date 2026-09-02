BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;

SELECT plan(10);

INSERT INTO public.tenancy_organizations (id, name, tax_id)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'Tenant A', 'A-1'),
    ('22222222-2222-4222-8222-222222222222', 'Tenant B', 'B-1');

INSERT INTO public.tenancy_memberships (org_id, user_id, role)
VALUES
    (
        '11111111-1111-4111-8111-111111111111',
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        'OWNER'
    ),
    (
        '22222222-2222-4222-8222-222222222222',
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
        'OWNER'
    );

INSERT INTO public.projects (
    id,
    org_id,
    code,
    name,
    client_name,
    created_by
)
VALUES
    (
        '11111111-aaaa-4111-8111-111111111111',
        '11111111-1111-4111-8111-111111111111',
        'QUOTE-A',
        'Quote A',
        'Client A',
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
    ),
    (
        '22222222-bbbb-4222-8222-222222222222',
        '22222222-2222-4222-8222-222222222222',
        'QUOTE-B',
        'Quote B',
        'Client B',
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'
    );

INSERT INTO public.cost_lists (id, org_id, supplier_name, valid_from)
VALUES
    (
        '11111111-aaaa-4111-9111-111111111111',
        '11111111-1111-4111-8111-111111111111',
        'Supplier A',
        DATE '2026-09-01'
    ),
    (
        '22222222-bbbb-4222-9222-222222222222',
        '22222222-2222-4222-8222-222222222222',
        'Supplier B',
        DATE '2026-09-01'
    );

SET LOCAL ROLE authenticated;
SELECT set_config(
    'request.jwt.claims',
    '{"sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","role":"authenticated"}',
    TRUE
);
SELECT set_config(
    'request.jwt.claim.sub',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    TRUE
);

SELECT is(
    (SELECT count(*) FROM public.projects),
    1::BIGINT,
    'tenant A sees exactly its own quotation'
);
SELECT is(
    (SELECT count(*) FROM public.projects WHERE code = 'QUOTE-B'),
    0::BIGINT,
    'tenant A cannot read tenant B quotation'
);
SELECT is(
    (SELECT count(*) FROM public.cost_lists),
    1::BIGINT,
    'tenant A sees exactly its own cost list'
);
SELECT is(
    (SELECT count(*) FROM public.cost_lists WHERE supplier_name = 'Supplier B'),
    0::BIGINT,
    'tenant A cannot read tenant B costs'
);

WITH changed AS (
    UPDATE public.projects
    SET name = 'Cross-tenant mutation'
    WHERE code = 'QUOTE-B'
    RETURNING id
)
SELECT is(
    (SELECT count(*) FROM changed),
    0::BIGINT,
    'tenant A cannot update tenant B quotation'
);

SELECT throws_ok(
    $$
        INSERT INTO public.projects (org_id, code, name, client_name, created_by)
        VALUES (
            '22222222-2222-4222-8222-222222222222',
            'CROSS-TENANT',
            'Forbidden',
            'Forbidden',
            'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
        )
    $$,
    '42501',
    'new row violates row-level security policy for table "projects"',
    'tenant A cannot insert a tenant B quotation'
);

RESET ROLE;
SET LOCAL ROLE authenticated;
SELECT set_config(
    'request.jwt.claims',
    '{"sub":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb","role":"authenticated"}',
    TRUE
);
SELECT set_config(
    'request.jwt.claim.sub',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    TRUE
);

SELECT is(
    (SELECT count(*) FROM public.projects),
    1::BIGINT,
    'tenant B sees exactly its own quotation'
);
SELECT is(
    (SELECT count(*) FROM public.projects WHERE code = 'QUOTE-A'),
    0::BIGINT,
    'tenant B cannot read tenant A quotation'
);
SELECT is(
    (SELECT count(*) FROM public.cost_lists),
    1::BIGINT,
    'tenant B sees exactly its own cost list'
);
SELECT is(
    (SELECT count(*) FROM public.cost_lists WHERE supplier_name = 'Supplier A'),
    0::BIGINT,
    'tenant B cannot read tenant A costs'
);

RESET ROLE;
SELECT * FROM finish();
ROLLBACK;

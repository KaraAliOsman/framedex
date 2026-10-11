BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(16);

SELECT has_table(
    'public', 'clients',
    'clients table exists'
);
SELECT has_column(
    'public', 'clients', 'org_id',
    'org_id column exists'
);
SELECT col_is_fk(
    'public', 'clients', 'org_id',
    'org_id references tenancy_organizations'
);
SELECT has_column(
    'public', 'clients', 'is_active',
    'is_active column exists'
);
SELECT has_trigger(
    'public', 'clients', 'client_identity_guard',
    'canonical client identities are guarded, including privileged imports'
);
INSERT INTO public.tenancy_organizations(id, name, tax_id) VALUES
    ('13000000-0000-4000-8000-000000000001', 'Client identity A', 'TEST-130-A'),
    ('13000000-0000-4000-8000-000000000002', 'Client identity B', 'TEST-130-B');
INSERT INTO public.clients(id, org_id, name, rut, created_by) VALUES
    ('13000000-0000-4000-8000-000000000011', '13000000-0000-4000-8000-000000000001',
     'Original identity', '76543210-3', '13000000-0000-4000-8000-000000000099'),
    ('13000000-0000-4000-8000-000000000012', '13000000-0000-4000-8000-000000000001',
     'Merge destination', NULL, '13000000-0000-4000-8000-000000000099');
SELECT throws_ok($$
    INSERT INTO public.clients(org_id, name, rut, created_by) VALUES
        ('13000000-0000-4000-8000-000000000001', 'Duplicate identity', '76543210-3',
         '13000000-0000-4000-8000-000000000099')
$$, '23505', 'client_rut_conflict', 'exact duplicate is rejected inside the tenant');
SELECT throws_ok($$
    INSERT INTO public.clients(org_id, name, rut, created_by) VALUES
        ('13000000-0000-4000-8000-000000000001', 'Punctuated duplicate', '76.543.210-3',
         '13000000-0000-4000-8000-000000000099')
$$, '23505', 'client_rut_conflict', 'punctuation cannot bypass canonical uniqueness');
SELECT lives_ok($$
    INSERT INTO public.clients(org_id, name, rut, created_by) VALUES
        ('13000000-0000-4000-8000-000000000002', 'Separate tenant identity', '76.543.210-3',
         '13000000-0000-4000-8000-000000000099')
$$, 'the same RUT belongs to an independent identity in another tenant');
SELECT throws_ok($$
    UPDATE public.clients SET rut = '76.543.210-3'
    WHERE id = '13000000-0000-4000-8000-000000000012'
$$, '23505', 'client_rut_conflict', 'editing an existing master cannot introduce a duplicate');
SELECT lives_ok($$
    UPDATE public.clients SET merged_into_id = '13000000-0000-4000-8000-000000000012'
    WHERE id = '13000000-0000-4000-8000-000000000011';
    UPDATE public.clients SET rut = '76.543.210-3'
    WHERE id = '13000000-0000-4000-8000-000000000012'
$$, 'a merge preserves the alias while the destination adopts the canonical RUT');
SELECT is(
    (SELECT rut::text FROM public.clients WHERE id = '13000000-0000-4000-8000-000000000011'),
    '76543210-3', 'the historical alias keeps its original RUT'
);
SELECT throws_ok($$
    UPDATE public.clients SET name = 'Rewritten history'
    WHERE id = '13000000-0000-4000-8000-000000000011'
$$, 'P0001', 'client_merged_immutable', 'a historical alias cannot be rewritten');
SELECT has_column(
    'public', 'projects', 'client_id',
    'projects.client_id column exists'
);
SELECT col_is_fk(
    'public', 'projects', 'client_id',
    'projects.client_id references clients'
);
SELECT policies_are(
    'public', 'clients',
    ARRAY[
        'clients_member_insert',
        'clients_member_read',
        'clients_member_update'
    ],
    'exactly the member policies'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.clients'::regclass),
    'row level security is enabled'
);

SELECT * FROM finish();
ROLLBACK;

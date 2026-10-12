-- Created with Supabase CLI; ordered after the existing December baseline.
-- Enum additions commit before the authority migration uses the new roles.
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'SLIDING_SASH';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'INTERLOCK';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'RAIL';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'DOOR_SASH';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'FRAME_EXTENSION';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'SILL';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'COVER_TRIM';
ALTER TYPE public.profile_role ADD VALUE IF NOT EXISTS 'PLINTH';

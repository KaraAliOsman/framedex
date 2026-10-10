"""Read-only addresses of the immutable workshop policies used by readiness."""

import json
from decimal import Decimal

from dekopen_engine.manufacturing import (
    handle_policy_from_json, placement_policy_from_json, reinforcement_policy_from_json,
)
from pricing.repository import rows


def manufacturing_policy_facts(system_id, org_id):
    result = []
    for kind, table, label, parse in (
        ("placement", "manufacturing_placement_policies", "Colocación de perfiles y junquillos", placement_policy_from_json),
        ("handles", "handle_requirement_policies", "Manillas y referencias de montaje", handle_policy_from_json),
        ("reinforcement", "reinforcement_cut_policies", "Corte del refuerzo", reinforcement_policy_from_json),
    ):
        found = rows(f"SELECT id,org_id,version,authority::text FROM public.{table} "
                     "WHERE system_id=%s AND (org_id IS NULL OR org_id=%s) "
                     "ORDER BY version DESC,id LIMIT 1", [system_id, org_id])
        row = found[0] if found else None
        valid = False
        if row:
            try:
                parse(json.loads(row["authority"], parse_float=Decimal))
                valid = True
            except (KeyError, TypeError, ValueError):
                pass
        result.append({"kind": kind, "authority_table": table, "label": label,
                       "id": str(row["id"]) if row else None,
                       "version": row["version"] if row else None, "valid": valid,
                       "global_authority": bool(row and row["org_id"] is None)})
    return result

"""RLS-bound exact configuration; no rule defaults or geometry in the repository."""

from dataclasses import dataclass
from decimal import Decimal
import json
from uuid import UUID

from django.db import connection

from dekopen_engine.inspection_models import InspectorConfig, InspectorConfigurationError
from engine_api.cutting_repository import effective_scope
from engine_api.repository import _decimal


@dataclass(frozen=True)
class InspectorAuthorities:
    config: InspectorConfig
    chamber_clearance_mm: Decimal


class InspectorRepository:
    def load(self, system_id: UUID, org_id: UUID) -> InspectorAuthorities:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT chamber_clearance_mm FROM public.profile_systems
                   WHERE id=%s AND is_active AND (is_global OR org_id=%s)""", [system_id, org_id],
            )
            system = cursor.fetchone()
            if system is None or system[0] is None:
                raise InspectorConfigurationError("Inspector requires explicit chamber clearance")
            cursor.execute(
                """SELECT rule_id, params::text, org_id FROM public.inspector_rule_configs
                   WHERE system_id=%s AND is_active AND (org_id IS NULL OR org_id=%s)
                   ORDER BY rule_id,id""", [system_id, org_id],
            )
            rows = cursor.fetchall()
        raw: dict[str, object] = {}
        try:
            for number in range(1, 15):
                rule = f"R{number:02d}"
                effective = effective_scope([r for r in rows if r[0] == rule], org_id, 2)
                if len(effective) != 1:
                    raise InspectorConfigurationError("Exactly fourteen effective rule configs required")
                payload = effective[0][1]
                if not isinstance(payload, str):
                    raise InspectorConfigurationError("Expected raw configuration JSON text")
                raw[rule] = json.loads(payload, parse_float=Decimal, parse_int=Decimal)
            config = InspectorConfig.model_validate(raw)
        except (ValueError, TypeError) as error:
            raise InspectorConfigurationError("Malformed Inspector configuration") from error
        return InspectorAuthorities(config, _decimal(system[0]))

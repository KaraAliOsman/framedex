"""Machine adapter contract for CNC output (v1 08).

The verified output today is the engine's neutral interchange
(`neutral-ops-v1`: canonical JSON + flat CSV + manifest). A machine-specific
adapter translates that document for one controller family; it is only
registered with its specification and verified samples. Homologation needs
physical evidence on the machine and is never inferred from a file format.

Levels, in order: PREPARATION → NEUTRAL_INTERCHANGE → MACHINE_ADAPTER →
HOMOLOGATED → PLANT_OPERATION. The UI names the level that is actually
reached; nothing here sends a program to a machine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dekopen_engine.operations import NeutralOpsPostProcessor, PostProcessor

LEVELS = ("PREPARATION", "NEUTRAL_INTERCHANGE", "MACHINE_ADAPTER", "HOMOLOGATED", "PLANT_OPERATION")

LEVEL_LABELS = {
    "PREPARATION": "Preparación de operaciones",
    "NEUTRAL_INTERCHANGE": "Intercambio neutro",
    "MACHINE_ADAPTER": "Adaptador de máquina",
    "HOMOLOGATED": "Compatibilidad homologada",
    "PLANT_OPERATION": "Operación en planta",
}


@dataclass(frozen=True)
class AdapterContract:
    """What an adapter must declare before it can be offered for a machine."""

    processor_id: str
    controller_family: str
    level: str
    # Specification the adapter follows (controller manual, vendor format).
    specification: str
    # Verified sample programs (fixture names) the adapter reproduces byte for byte.
    verified_samples: tuple[str, ...] = field(default_factory=tuple)
    # Physical evidence (controlled run on the machine) — required for HOMOLOGATED.
    physical_evidence: str | None = None

    def __post_init__(self) -> None:
        if self.level not in LEVELS:
            raise ValueError("unknown adapter level")
        if self.level in ("MACHINE_ADAPTER", "HOMOLOGATED", "PLANT_OPERATION") and not self.verified_samples:
            raise ValueError("a machine adapter needs verified sample programs")
        if self.level in ("HOMOLOGATED", "PLANT_OPERATION") and not self.physical_evidence:
            raise ValueError("homologation needs physical evidence on the machine")


NEUTRAL = AdapterContract(
    processor_id=NeutralOpsPostProcessor.processor_id,
    controller_family="NEUTRAL",
    level="NEUTRAL_INTERCHANGE",
    specification="dekopen_ops_v1 (JSON canónico + CSV de operaciones + manifiesto)",
)

# Only adapters with specification and verified samples are registered here.
_REGISTRY: dict[str, tuple[AdapterContract, PostProcessor]] = {
    NEUTRAL.processor_id: (NEUTRAL, NeutralOpsPostProcessor()),
}


def contract_for(processor_id: str | None) -> AdapterContract | None:
    entry = _REGISTRY.get(str(processor_id or ""))
    return entry[0] if entry else None


def level_label(processor_id: str | None) -> str:
    contract = contract_for(processor_id)
    if contract is None:
        return "Adaptador sin implementar · se entrega intercambio neutro"
    return LEVEL_LABELS[contract.level]


def processor(processor_id: str) -> PostProcessor:
    entry = _REGISTRY.get(processor_id)
    if entry is None:
        raise LookupError("cnc_adapter_not_registered")
    return entry[1]

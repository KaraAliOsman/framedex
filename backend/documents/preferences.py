"""Document choices for new revisions; sealed snapshots never consult live settings."""

from copy import deepcopy
import json

ACCENTS = {"TEAL": "#075F5A", "TEAL_DARK": "#064440", "GRAPHITE": "#161C1F"}
PAPERS = {"LETTER": "letter portrait", "OFICIO": "216mm 330mm", "A4": "A4 portrait"}
DEFAULT_TERMS = {
    "payment_schedule": [
        {"label": "Al aprobar", "share": "0.50", "due_event": "APPROVAL"},
        {"label": "Contra entrega", "share": "0.50", "due_event": "DELIVERY"},
    ],
    "delivery_text": "", "installation_text": "", "exclusions": "",
    "warranty": "", "jurisdiction": "",
}
DEFAULT_PREFERENCES = {
    "paper": "LETTER", "accent": "TEAL", "legal_footer": "",
    "quotation_preview_minutes": 30,
    "quotation_valid_days": 15,
    "piece_label_paper": "LETTER",
    "remnant_destination": "Recepción de retazos",
    "remnant_age_days": 90,
    "commercial_terms": DEFAULT_TERMS,
}


def document_preferences(value: object) -> dict:
    if isinstance(value, str):
        value = json.loads(value)
    supplied = value if isinstance(value, dict) else {}
    result = {**deepcopy(DEFAULT_PREFERENCES), **supplied}
    if result["paper"] not in PAPERS:
        result["paper"] = "LETTER"
    if result["accent"] not in ACCENTS:
        result["accent"] = "TEAL"
    return result

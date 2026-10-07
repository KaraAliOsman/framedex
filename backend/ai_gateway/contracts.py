"""Wire structure; domain validators still validate every operation and claim."""

AGENT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["reply"],
    "properties": {
        "reply": {"type": "string", "maxLength": 20000},
        **{name: {"type": "array", "maxItems": 100, "items": {"type": "object"}}
           for name in ("steps", "plan", "claims")},
        **{name: {"type": "array", "maxItems": 100, "items": {"type": "string"}}
           for name in ("warnings", "questions")},
        "clarify": {"type": ["object", "null"]},
        "tool_calls": {"type": "array", "maxItems": 6, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "arguments"],
            "properties": {"name": {"type": "string"}, "arguments": {"type": "object"}},
        }},
    },
}

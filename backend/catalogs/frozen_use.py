"""Read an issued decision without consulting today's catalog."""


def manufacturing_pending(snapshot):
    output = {}
    for position in snapshot.get("positions", []):
        gate = position.get("catalog_authority_gate", {})
        pending = list(gate.get("workshop_pending", []))
        pending.extend(item for level in gate.get("usage", {}).get("levels", [])
            if level["level"] == "MANUFACTURABLE" for item in level["pending"])
        for item in pending:
            output[(item.get("row_id"), item["field"], item["rule"])] = item
    return list(output.values())

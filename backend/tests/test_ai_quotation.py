from ai_gateway.quotation import _missing_summary


def test_preparation_groups_repeated_work_without_losing_affected_positions():
    missing = [
        {"code": "documentary_inputs_unconfirmed", "detail": "Revisa la preparación.", "position_id": str(index)}
        for index in range(35)
    ]
    missing.append({"code": "pricing_not_applied", "detail": "Calcula el precio."})
    result = _missing_summary(missing)
    assert len(result) == 2
    assert result[0]["positions"] == [str(index) for index in range(35)]
    assert result[0]["detail"].endswith("(35 posiciones).")
    assert result[1]["detail"] == "Revisa y aplica el precio preparado."

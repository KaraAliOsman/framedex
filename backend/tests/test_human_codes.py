from documents.human import human_code, human_text


def test_codes_read_as_people_say_them():
    assert human_code("P-000044") == "N° 44"
    assert human_code("OT-000012", with_kind=True) == "OT N° 12"
    assert human_text("Su cotización · P-000044 · REV-A") == "Su cotización · Obra N° 44 · revisión A"
    assert human_text("Orden OC-000003 lista") == "Orden Compra N° 3 lista"
    assert human_text("PRO6004 · REVISADO") == "PRO6004 · REVISADO"

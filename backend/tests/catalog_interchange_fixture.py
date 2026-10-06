"""Provider-like ten-sheet fixture; every number has an explicit synthetic source."""
from catalogs.demo_fixture import manifest
from ingest.catalog_template import candidate

def catalog_rows():
    fixture = manifest()[0]
    params = fixture["params"]
    code = "PROVEEDOR-60"
    source = "Ficha de prueba, página 1 · sin certificación"
    raw = {**params, "system_code": code, "name": "Sistema de prueba 60", "chamber_count": 5,
           "version": 1, "is_active": True, "source": source}
    rows = [("Sistemas", raw)]
    for article in fixture["articles"]:
        rows.append(("Perfiles", {**article, "system_code": code, "source": source}))
        rows.append(("Roles y reglas de corte", {**article["cut_rule"], "system_code": code, "sku": article["sku"], "role": article["role"], "source": source}))
        if article["reinforcement_rule"]:
            rows.append(("Refuerzos", {**article["reinforcement_rule"], "system_code": code, "sku": article["sku"], "source": source}))
    for rule in params["dimensional_limits"]:
        rows.append(("Límites", {**rule, "system_code": code, "source": source}))
    rows.append(("Colores y SKU por color", {"system_code": code, "sku": fixture["articles"][0]["sku"], "finish": "WHITE", "commercial_sku": "COMPRA-MARCO-BLANCO", "physical_stock_identity": "MARCO-BLANCO", "source": source}))
    for glass in fixture["glasses"]:
        bead=params["glazing_bead_rules"]["24.00" if "16" in glass["glass_spec"] else "4.00"]
        rows.append(("Vidrios", {**glass, **{key:value for key,value in bead.items() if key!="bead_article"},
            "bead_sku":bead["bead_article"]["sku"], "system_code": code, "purchasing_sku": glass["sku"], "manufacturer_name": "Proveedor de prueba", "version": 1, "source": source}))
    for kit in params["available_hardware_kits"]:
        rows.append(("Herrajes", {**kit, "weight_kg": "2.50", "system_code": code, "is_active": True, "source": source}))
    rows.append(("Precios de costo", {"system_code": code, "sku": fixture["articles"][0]["sku"], "list_code": "PROVEEDOR-OCTUBRE", "supplier_name": "Proveedor de prueba", "currency": "CLP", "valid_from": "2026-10-01", "valid_to": None, "unit_cost": "14500.25", "item_type": "PROFILE", "unit": "BAR", "source": source}))
    rows.append(("Reglas de vidrio", {"code": "PRUEBA-PUERTA", "name": "Puerta · regla sintética", "zone": "DOOR", "required_classes": ["A", "B", "C"], "mandatory": False, "synthetic": True, "source": source}))
    return [candidate(sheet, values, key=f"r{index}", row=index + 5, method="MANUAL") for index, (sheet, values) in enumerate(rows)]

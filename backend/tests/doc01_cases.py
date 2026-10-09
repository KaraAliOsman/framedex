"""Synthetic DEMO geometry + engine prices, shared by PDF QA and regression tests."""

from dataclasses import asdict
from decimal import Decimal as D

from dekopen_engine import BayOpeningType, NodeType, ParametricNode, calculate_geometry
from dekopen_engine.commercial import CommercialLine, PricingMode, finish_lines, unit_price
from dekopen_engine.documentary_canonical import documentary_sha256_v1
from dekopen_engine.glass import exact_glass_area_m2
from documents.preferences import DEFAULT_PREFERENCES
from engine.tests.catalog import demo_60_params


def proposal_case(count: int, currency: str = "CLP", *, long_names=False, paper="LETTER") -> dict:
    params = demo_60_params()
    positions, priced_lines = [], []
    kinds = [("FIXED", "1200", "1400"), ("TILT_TURN_LEFT", "1000", "1400"),
             ("TURN_RIGHT", "800", "1200"), ("AWNING", "1000", "800"),
             ("SLIDING_2L", "2400", "1800"), ("FIXED", "600", "900")]
    details = []
    for index in range(1, count + 1):
        kind, width, height = kinds[(index - 1) % len(kinds)]
        node = ParametricNode(id=f"bay-{index}", type=NodeType.BAY, opening_type=BayOpeningType(kind),
            width_mm=D(width), height_mm=D(height), glass_spec="4-16-4", glass_thickness_mm=D("24"))
        bom = calculate_geometry(node, params)
        quantity = 3 if index % 3 == 0 else 1
        cost = D("60000") if currency == "CLP" else D("60.001")
        price = unit_price(PricingMode.COST_PLUS_MARGIN, cost=cost, margin=D("0.35"),
            area=exact_glass_area_m2(D(width), D(height)), width=D(width), height=D(height))
        discount = D("0.10")
        priced_lines.append(CommercialLine(index, quantity, cost, price, discount))
        details.append({"position_index": index, "quantity": quantity, "unit_price": str(price), "discount_pct": str(discount)})
        location = f"Piso {(index - 1) // 6 + 1} · Dormitorio {index} fachada norte"
        if long_names:
            location = (location + " · recinto del sector residencial con acceso desde patio interior y orientación hacia la calle de servicio " )[:120].ljust(120, "a")
        positions.append({"id": f"00000000-0000-4000-8000-{index:012d}", "position_index": index,
            "system_name": "DEMO 60 · referencia sintética", "is_demo": True,
            "location_tag": location, "width_mm": width, "height_mm": height,
            "quantity": quantity, "typology": kind, "discount_pct": str(discount),
            "color_interior": "WHITE", "color_exterior": "WHITE", "parametric_tree": node.model_dump(mode="json"),
            "bom": bom.model_dump(mode="json")})
    prices = finish_lines(priced_lines, currency, D("0.19"))
    for position, (index, net) in zip(positions, prices.lines, strict=True):
        assert position["position_index"] == index
        position["price_net"] = str(net)
    client = "Constructora Los Robles del Sur SpA"
    if long_names:
        client = (client + " y Asociación de Propietarios del Condominio Residencial Parque del Oriente Sector Norte Etapa Tres")[:120].ljust(120, "a")
    return {"revision": "REV-B", "sealed_at": "2026-10-08T15:30:00Z", "is_demo": True,
        "bom_hash": documentary_sha256_v1([item["bom"] for item in positions]),
        "organization": {"name": "Ventanas Los Robles SpA", "commercial_name": "Ventanas Los Robles",
            "tax_id": "77.123.456-0", "giro": "Fabricación de ventanas",
            "brand_address": "Los Robles 1800, Puerto Varas", "brand_phone": "+56 65 2345 678",
            "brand_email": "cotizaciones@example.test", "brand_schema": 1, "document_attribution": False,
            "document_preferences": {**DEFAULT_PREFERENCES, "paper": paper}},
        "project": {"code": "P-000123", "name": "Condominio Parque del Oriente", "client_name": client,
            "client_rut": "76.543.210-8", "client_address": "Avenida del Parque 1200, Puerto Varas",
            "client_comuna": "Puerto Varas", "client_email": "compras@example.test",
            "delivery_address": "Acceso norte de la obra, Avenida del Parque 1200",
            "currency": currency, "total_price_net": str(prices.project_net), "total_price_tax": str(prices.project_tax),
            "total_price_gross": str(prices.project_gross), "quotation_valid_until": "2026-10-23",
            "payment_terms": "Anticipo al aprobar y saldo contra entrega, según el calendario.",
            "commercial_terms": {"payment_schedule": [{"label": "Al aprobar", "share": "0.50"}, {"label": "Contra entrega", "share": "0.50"}],
                "delivery_text": "20 días hábiles desde la aprobación y confirmación de medidas.",
                "installation_text": "Instalación incluida en los vanos confirmados.",
                "exclusions": "No incluye reparación de muros ni terminaciones interiores.",
                "warranty": "Garantía según condiciones de fabricación adjuntas a esta revisión.",
                "jurisdiction": "Tribunales competentes de Puerto Varas."}},
        "positions": positions, "pricing": {"request": {"tax_rate_pct": "0.19"}, "result": {**asdict(prices), "line_detail": details}}}

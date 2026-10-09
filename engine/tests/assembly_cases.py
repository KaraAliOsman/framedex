"""P06 reviewed cases without modifying historical BOM goldens."""
from decimal import Decimal as D
import json
from typing import Any
from dekopen_engine.models import CouplerRule, EffectiveProfileArticle, ProfileRole, MaterialType
from dekopen_engine.product import ProductModel, evaluate_product
from dekopen_engine.snapshot import evaluation_payload
from engine.tests.catalog import demo_60_params


def joint_article(maximum: str = "60", minimum: str = "0", width: str = "0") -> EffectiveProfileArticle:
    return EffectiveProfileArticle(sku="FUENTE-ARTICULO",role=ProfileRole.COUPLER,material=MaterialType.PVC,
        face_width_mm=D("40"),welding_loss_mm=D("0"),reinforcement_gap_mm=None,weight_kg_m=D("0.9"),
        steel_weight_kg_m=None,coupling_rule=CouplerRule(min_angle_deg=D(minimum),max_angle_deg=D(maximum),
            development_mm=D(width),source="Fixture de autoridad revisada; sin certificación"))


def bow_model(angle: str = "22.5") -> ProductModel:
    return ProductModel.model_validate_json(json.dumps({"version":"product-v2","assembly":{"modules":[
        {"id":f"m{index+1}","width_mm":width,"height_mm":"1200","tree":{"id":f"b{index+1}","type":"BAY",
            "opening_type":"FIXED","glass_thickness_mm":"4","glass_spec":"4"}}
        for index,width in enumerate(["600","1200","600"])],"couplings":[
            {"id":f"c{index+1}","angle_deg":angle,"coupler_profile_sku":"FUENTE-ARTICULO"} for index in range(2)]}}))


def assembly_cases() -> dict[str, Any]:
    cases: dict[str, Any] = {}
    for name,angle,article in [("bow_22_5","22.5",joint_article()),("bow_45","45",joint_article()),
            ("rechazo_89","89",joint_article()),("bow_espaciado","22.5",joint_article(width="24"))]:
        result=evaluate_product(bow_model(angle),demo_60_params(),coupler_articles={article.sku:article})
        cases[name]={"status":result.status.value,"plan":evaluation_payload(result)["plan"],
            "measures":evaluation_payload(result).get("measures"),"issues":[issue.model_dump(mode="json") for issue in result.issues]}
    corner=bow_model("90")
    corner.assembly.modules=corner.assembly.modules[:2]
    corner.assembly.couplings=corner.assembly.couplings[:1]
    article=joint_article("90","90")
    result=evaluate_product(corner,demo_60_params(),coupler_articles={article.sku:article})
    cases["esquina_90"]={"status":result.status.value,"plan":evaluation_payload(result)["plan"],
        "measures":evaluation_payload(result).get("measures"),"issues":[issue.model_dump(mode="json") for issue in result.issues]}
    return cases

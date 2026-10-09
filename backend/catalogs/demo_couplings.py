"""Additive v7 synthetic joint authorities; v1-v6 remain unchanged."""

from copy import deepcopy

from backend.catalogs.demo_extras import extra_manifest

SOURCE = "Acopladores sintéticos DEKOPEN v7; semilla 20270113; sin certificación"


def coupling_manifest():
    records = deepcopy(extra_manifest())
    for record in records:
        code, params = record["code"], record["params"]
        record["version"] = 7
        record["name"] = record["name"].replace("extras v6", "acoples v7")
        for suffix, name, minimum, maximum, development, rate in (
                ("REGULABLE", "Acoplador regulable", "0.00", "60.00", "0.00", "24000"),
                ("ESQUINA", "Acoplador de esquina", "90.00", "90.00", "0.00", "28000")):
            sku = code+"-ACOPLE-"+suffix
            # This synthetic pivot shares the module front endpoints. Its
            # net developed contribution is explicitly zero; the depth wedge
            # and real vertical cut still exist and are priced from the BOM.
            article = {"sku": sku, "name": name+" · DEMO", "role": "COUPLER", "material": params["material"],
                "face_width_mm": "40.00", "commercial_length_mm": "6000.00", "welding_loss_mm": "0.00",
                "reinforcement_gap_mm": None, "weight_kg_m": "0.9000", "steel_weight_kg_m": None,
                "reinforcement_sku": None, "reinforcement_rule": None,
                "cut_rule": {"angle_degrees": 90, "welding_loss_per_end_mm": "0.00", "joint_deduction_per_end_mm": "0.00",
                    "meeting_deduction_mm": "0.00", "cut_step_mm": "0.01", "rounding": "UP", "source": SOURCE},
                "coupling_rule": {"min_angle_deg":minimum, "max_angle_deg":maximum,
                    "development_mm":development, "source":SOURCE}}
            if params['material']=='PVC':
                steel='REF-'+sku
                article.update({'reinforcement_sku':steel,'reinforcement_gap_mm':'40.00','steel_weight_kg_m':'1.1000',
                    'reinforcement_rule':{'reinforcement_sku':steel,'reinforcement_type':'Acero galvanizado · DEMO',
                        'minimum_length_mm':'0.00','required_finishes':[],'required_non_white':True,'cut_deduction_mm':'40.00',
                        'screws_per_m':'2.0000','screw_sku':code+'-TORNILLO-REF','screw_weight_kg':'0.005000','source':SOURCE}})
                record['prices'].append({'sku':'COMPRA-'+steel,'unit':'BAR','unit_cost':'12000'})
            record["articles"].append(article)
            record["prices"].append({"sku":"COMPRA-"+sku,"unit":"BAR","unit_cost":rate})
            for combination in params["finish_authority"]["combinations"]:
                finish = combination["code"]
                commercial = "COMPRA-V7-"+sku+"-"+finish
                record["finish_bindings"].append({"sku":sku,"finish":finish,"commercial_sku":commercial})
                params["finish_profile_skus"][finish][sku] = commercial
                record["prices"].append({"sku":commercial,"unit":"BAR","unit_cost":rate})
    return records

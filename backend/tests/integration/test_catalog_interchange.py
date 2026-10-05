"""Human publication, rollback and RLS against the real catalog."""
from uuid import UUID, uuid4
import json
import pytest
from django.db import DatabaseError, transaction
from authentication.errors import ContractAPIException
from authentication.rls import catalog_backend
from backend.tests.catalog_interchange_fixture import catalog_rows
from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from catalogs import service
from ingest import catalog_review, catalog_service
from pricing.repository import one, rows, json_text

pytestmark = pytest.mark.rls_integration

def imported(org, actor, candidates=None):
    values = catalog_rows() if candidates is None else candidates
    row_id = uuid4()
    one("INSERT INTO public.catalog_imports(id,org_id,file_name,kind,storage_path,created_by,status,candidates,contains_costs) VALUES(%s,%s,'proveedor.csv','CSV',%s,%s,'REVIEW_READY',%s::jsonb,TRUE) RETURNING id",
        [row_id,org,f"catalog-imports/{org}/{row_id}/proveedor.csv",actor,json_text(values)])
    return row_id, [{"key":entry["key"],"values":entry["values"]} for entry in values]

def test_nine_sheet_publication_atomic_provenance_and_undo(documentary_tenant):
    org,_,users,_ = documentary_tenant
    actor = users["OWNER"]
    import_id, items = imported(org,actor)
    with as_user(actor):
        diff = catalog_review.preview(org_id=org,import_id=import_id,items=items)
        assert not diff["errors"], diff["errors"]
        assert not rows("SELECT id FROM public.profile_systems WHERE org_id=%s AND code='PROVEEDOR-60'",[org])
        with pytest.raises(ContractAPIException) as caught:
            catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token="sha256:"+"0"*64)
        assert caught.value.contract_code == "catalog_review_stale"
        assert not rows("SELECT id FROM public.profile_systems WHERE org_id=%s AND code='PROVEEDOR-60'",[org])
        published = catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        assert not published["errors"]
        system = service.list_rows(service.SYSTEMS,org)
        authority = next(item for item in system if item["code"]=="PROVEEDOR-60")
        assert authority["system_family"]=="CASEMENT"
        assert str(authority["technical_reviewed_by"])==str(actor)
        assert authority["data_provenance"]=="IMPORT" and not authority["review_pending"]
        articles = service.list_rows(service.ARTICLES,org,authority["id"])
        assert len(articles)==7
        frame = next(item for item in articles if item["role"]=="FRAME")
        assert frame["cut_rule"]["source"].startswith("Ficha de prueba")
        assert frame["reinforcement_rule"]["screws_per_m"]==4
        attestations=rows("SELECT source_document,review_state,reviewed_by FROM public.catalog_parameter_evidence WHERE org_id=%s AND row_id=%s",[org,frame["id"]])
        assert len(attestations)>=20 and all(row["review_state"]=="REVIEWED" and row["reviewed_by"]==actor for row in attestations)
        replay=catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        assert replay["created"]==published["created"]
        undone=catalog_review.undo_publication(org_id=org,actor_id=actor,import_id=import_id)
        assert undone["import"]["status"]=="UNDONE"
        assert not rows("SELECT id FROM public.profile_systems WHERE org_id=%s AND code='PROVEEDOR-60' AND is_active",[org])
        assert not rows("SELECT id FROM public.profile_articles WHERE org_id=%s",[org])
        assert not rows("SELECT id FROM public.glass_purchase_mappings WHERE org_id=%s",[org])
        assert not rows("SELECT id FROM public.cost_lists WHERE org_id=%s AND is_active",[org])
        assert len(rows("SELECT id FROM public.catalog_import_publications WHERE import_id=%s",[import_id]))==2
        with catalog_backend():
            history=rows("SELECT id FROM public.glass_purchase_mappings WHERE org_id=%s",[org])
            assert history
            assert len(rows("SELECT mapping_id FROM public.catalog_glass_retractions WHERE org_id=%s",[org]))==len(history)
            with pytest.raises(DatabaseError), transaction.atomic():
                one("UPDATE public.glass_purchase_mappings SET id=id WHERE id=%s RETURNING id",[history[0]["id"]])

def test_no_bypass_and_error_prevents_every_write(documentary_tenant):
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    import_id,items=imported(org,actor)
    items[0]["values"]["depth_mm"]=None
    with as_user(actor):
        diff=catalog_review.preview(org_id=org,import_id=import_id,items=items)
        assert diff["errors"]
        result=catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        assert result["errors"] and not result["created"]
        assert not rows("SELECT id FROM public.profile_systems WHERE org_id=%s",[org])
        with pytest.raises(ContractAPIException) as caught:
            catalog_service.confirm_catalog_import(org_id=org,actor_id=actor,import_id=import_id,system_id=uuid4(),items=[])
        assert caught.value.contract_code=="catalog_diff_required"

def test_import_and_cost_proposals_are_scoped_by_tenant_and_role(documentary_tenant):
    org,other,users,foreign=documentary_tenant
    import_id,_=imported(org,users["OWNER"])
    with as_user(foreign):
        assert not rows("SELECT id FROM public.catalog_imports WHERE id=%s",[import_id])
        with pytest.raises(catalog_service.CatalogImportError):
            catalog_service.get_catalog_import(org_id=other,import_id=import_id)
    with as_user(users["ESTIMATOR"]):
        assert not rows("SELECT candidates FROM public.catalog_imports WHERE id=%s",[import_id])
    with as_user(users["WORKSHOP_MANAGER"]):
        assert len(rows("SELECT id FROM public.catalog_imports WHERE id=%s",[import_id]))==1
        diff=catalog_review.preview(org_id=org,import_id=import_id,items=[{"key":row["key"],"values":row["values"]} for row in catalog_rows()])
        assert any("Solo el dueño" in error["message"] for error in diff["errors"])

def test_undo_rejects_later_authority_edit(documentary_tenant):
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    import_id,items=imported(org,actor,[row for row in catalog_rows() if row["sheet"]=="Sistemas"])
    with as_user(actor):
        diff=catalog_review.preview(org_id=org,import_id=import_id,items=items)
        published=catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        system_id=UUID(published["created"][0]["row_id"])
        current=service.retrieve(service.SYSTEMS,org,system_id)
        service.update(service.SYSTEMS,org,system_id,{"name":"Revisado después"},expected_revision='"'+current["revision"]+'"',actor_id=actor)
        with pytest.raises(ContractAPIException) as caught:
            with transaction.atomic():
                catalog_review.undo_publication(org_id=org,actor_id=actor,import_id=import_id)
        assert caught.value.contract_code=="catalog_undo_stale"
        assert service.retrieve(service.SYSTEMS,org,system_id)["name"]=="Revisado después"


def test_approved_correction_is_visible_without_overwriting_original(documentary_tenant):
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    import_id,items=imported(org,actor,[row for row in catalog_rows() if row["sheet"]=="Sistemas"])
    items[0]["values"]["depth_mm"]="62.25"
    with as_user(actor):
        diff=catalog_review.preview(org_id=org,import_id=import_id,items=items)
        published=catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        candidate=published["import"]["candidates"][0]
        assert candidate["values"]["depth_mm"]=="62.25"
        assert candidate["fields"]["depth_mm"]["method"]=="HUMAN_CORRECTION"
        assert catalog_service.get_catalog_import(org_id=org,import_id=import_id)["import"]["candidates"]==published["import"]["candidates"]
        original=rows("SELECT candidates FROM public.catalog_imports WHERE id=%s",[import_id])[0]["candidates"]
        if isinstance(original,str):
            original=json.loads(original)
        assert original[0]["values"]["depth_mm"]=="60.00"


def test_used_glass_authority_cannot_be_retired_even_by_internal_role(documentary_tenant):
    from projects.service import create_project, save_position
    from decimal import Decimal
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    import_id,items=imported(org,actor,[row for row in catalog_rows() if row["sheet"]!="Precios de costo"])
    with as_user(actor):
        diff=catalog_review.preview(org_id=org,import_id=import_id,items=items)
        published=catalog_review.publish(org_id=org,actor_id=actor,import_id=import_id,items=items,review_token=diff["review_token"])
        system_id=UUID(next(row["row_id"] for row in published["created"] if row["table"]=="profile_systems"))
        project=create_project(org,actor,{"name":"Catálogo utilizado"})
        save_position(org,UUID(str(project["id"])),{"location_tag":"Ventana", "quantity":1, "design":{
            "system_id":system_id,"nominal_width_mm":Decimal("1000"),"nominal_height_mm":Decimal("1000"),"color":"WHITE",
            "parametric_tree":{"type":"BAY","id":"b1","opening_type":"FIXED","glass_thickness_mm":"24.00","glass_spec":"4-16-4","children":[]}}})
        mapping=next(row for row in published["created"] if row["table"]=="glass_purchase_mappings")
        with catalog_backend():
            with pytest.raises(DatabaseError,match="catalog_authority_referenced"), transaction.atomic():
                one("INSERT INTO public.catalog_glass_retractions(mapping_id,org_id,import_id,actor_id) VALUES(%s,%s,%s,%s) RETURNING mapping_id",
                    [mapping["row_id"],org,import_id,actor])
        assert catalog_service.get_catalog_import(org_id=org,import_id=import_id)["import"]["status"]=="CONFIRMED"
        assert rows("SELECT id FROM public.glass_purchase_mappings WHERE id=%s",[mapping["row_id"]])

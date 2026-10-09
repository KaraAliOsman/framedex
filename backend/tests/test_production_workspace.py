"""Privacy projections and explicit quality decisions over existing contracts."""
from contextlib import nullcontext
from unittest.mock import patch
from uuid import uuid4

import pytest

from documents.repository import DocumentaryError
from production import quality, service
from production.serializers import StepTransitionRequestSerializer


def test_block_on_fail_is_opt_in_and_rejects_unrelated_actions():
    check = {"check": "Escuadra", "expected": "0.00 mm", "actual": "1.00 mm", "result": "FAIL"}
    default = StepTransitionRequestSerializer(data={"action": "QC_CHECK", "qc_check": check})
    assert default.is_valid() and default.validated_data["block_on_fail"] is False
    blocked = StepTransitionRequestSerializer(data={"action": "QC_CHECK", "qc_check": check, "block_on_fail": True})
    assert blocked.is_valid() and blocked.validated_data["block_on_fail"] is True
    invalid = StepTransitionRequestSerializer(data={"action": "NOTE", "note": "test", "block_on_fail": True})
    assert not invalid.is_valid()


def test_operator_queue_never_contains_later_steps_or_other_stations():
    org, user, order = uuid4(), uuid4(), uuid4()
    steps = [dict(id="first",order_id=order,sequence=1,code="CUT",label="Corte",status="READY",note=None,order_code="OT-1",work_center_code="SAW",work_center_name="Sierra"),
             dict(id="second",order_id=order,sequence=2,code="QC",label="Calidad",status="READY",note=None,order_code="OT-1",work_center_code="QC",work_center_name="Calidad")]
    with patch("production.service.rows",return_value=steps), patch("production.stations.operator_station",return_value={"selected_code":"QC"}):
        report=service.station_queue(org_id=org,actor_id=user,actor_role="OPERATOR")
    assert report["selected_code"] == "QC"
    assert all(s["code"] == "QC" and not s["entries"] for s in report["stations"])
    with patch("production.service.rows",return_value=steps), patch("production.stations.operator_station",return_value={"selected_code":"CUT"}):
        report=service.station_queue(org_id=org,actor_id=user,actor_role="OPERATOR")
    assert [e["step_id"] for s in report["stations"] for e in s["entries"]] == ["first"]


def test_quality_retry_returns_existing_remake_without_a_second_transition():
    remake=uuid4()
    with patch("production.quality.transaction.atomic",return_value=nullcontext()), patch("production.quality.documentary_backend",return_value=nullcontext()), \
         patch("production.quality.one",return_value={"id":uuid4()}), patch("production.quality.rows",return_value=[{"id":remake}]), \
         patch("production.quality.service.get_work_order",return_value={"id":str(remake)}), patch("production.quality.service.transition_step") as transition:
        result=quality.reject_and_remake(org_id=uuid4(),order_id=uuid4(),actor_id=uuid4(),actor_role="WORKSHOP_MANAGER",confirmed=True,operation_key=uuid4(),note="Escuadra rechazada",item_code="P01-U01-M01")
    assert result["id"] == str(remake)
    transition.assert_not_called()


@pytest.mark.parametrize("role,confirmed",[("OPERATOR",True),("WORKSHOP_MANAGER",False)])
def test_quality_requires_supervisor_and_explicit_human_confirmation(role,confirmed):
    with pytest.raises(DocumentaryError):
        quality.reject_and_remake(org_id=uuid4(),order_id=uuid4(),actor_id=uuid4(),actor_role=role,confirmed=confirmed,operation_key=uuid4(),note="Escuadra rechazada",item_code="")

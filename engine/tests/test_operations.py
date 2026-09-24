"""§7 machine-neutral manufacturing operations — authority-bound derivation."""

from decimal import Decimal


from dekopen_engine.cutting import (
    CutMaterial,
    CutPiece,
    CuttingProfile,
    StockRule,
    optimize_cut,
)
from dekopen_engine.manufacturing import (
    HandleLocationFactV1,
    ManufacturingFactsV1,
    PhysicalMemberFactV1,
    PhysicalMemberIdentityV1,
    VerticalReference,
)
from dekopen_engine.manufacturing_trace import Axis, TracePointV1
from dekopen_engine.models import MaterialType, ProfileRole
from dekopen_engine.operations import (
    NEUTRAL_MACHINE_PROFILE,
    CoordinateSystem,
    NeutralOpsPostProcessor,
    OperationKind,
    operations_from_plan,
    ops_document,
)


def _piece(pid: str, length: str, role: str = "FRAME") -> CutPiece:
    return CutPiece(
        piece_id=pid,
        source_kind="PROFILE",
        workshop_sku="WS-P1",
        material=CutMaterial.PVC,
        color="BLANCO",
        length_mm=Decimal(length),
        role=role,
        unit_index=1,
        angle_left=Decimal("90"),
        angle_right=Decimal("90"),
    )


def _stock() -> StockRule:
    return StockRule(
        stock_authority_id="auth-1",
        workshop_sku="WS-P1",
        commercial_sku="MARCO-60",
        manufacturer_name="DEMO",
        supplier_name=None,
        purchase_unit="BAR",
        material=CutMaterial.PVC,
        color="BLANCO",
        stock_length_mm=Decimal("6000"),
    )


def _profile() -> CuttingProfile:
    return CuttingProfile(
        id="cp-1", code="STD", kerf_mm=Decimal("5"), head_trim_mm=Decimal("10"),
        tail_trim_mm=Decimal("10"),
    )


def _member(role: ProfileRole, span: str, overlap: str = "0") -> PhysicalMemberFactV1:
    span_d = Decimal(span)
    cut = span_d + Decimal(overlap) * 2
    return PhysicalMemberFactV1(
        member_id="a" * 64,
        semantic_member_id="mem-1",
        identity=PhysicalMemberIdentityV1(
            position_id="pos-1", position_index=1, repetition_index=1,
            topology_path="root/split/leaf", assembly="A", leaf_slot=None,
            role=role, physical_member_slot="m1",
        ),
        bay_id="bay-1", leaf_id=None, workshop_sku="WS-P1",
        material=MaterialType.PVC, cut_length_mm=cut,
        angle_left=Decimal("90"), angle_right=Decimal("90"),
        axis=Axis.VERTICAL,
        start=TracePointV1(x_mm=Decimal("500"), y_mm=Decimal("0")),
        end=TracePointV1(x_mm=Decimal("500"), y_mm=span_d),
    )


def _unit(**kwargs: object) -> ManufacturingFactsV1:
    data: dict[str, object] = {
        "position_id": "pos-1", "position_index": 1, "repetition_index": 1,
        "nominal_width_mm": Decimal("1000"), "nominal_height_mm": Decimal("1200"),
        "placement_policy_id": "pp", "placement_policy_version": 1,
        "handle_policy_id": "hp", "handle_policy_version": 2,
        "reinforcement_policy_id": "rp", "reinforcement_policy_version": 1,
        "reinforcements": [], "leaves": [], "infills": [],
        "relationships": [], "members": [], "handles": [],
    }
    data.update(kwargs)
    return ManufacturingFactsV1.model_validate(data)


def _handle() -> HandleLocationFactV1:
    return HandleLocationFactV1(
        handle_id="b" * 64, position_id="pos-1", position_index=1,
        repetition_index=1, bay_id="bay-1", leaf_id="leaf-1",
        handle_domain_slot="main", host_member_id="a" * 64,
        point=TracePointV1(x_mm=Decimal("80"), y_mm=Decimal("1050")),
        requested_height_mm=Decimal("1050"),
        vertical_reference=VerticalReference.LEAF_BOTTOM,
        policy_id="hp-1", policy_version=3,
    )


def test_saw_ops_cover_every_piece_boundary() -> None:
    plan = optimize_cut(
        [_piece("p1", "2000"), _piece("p2", "1500")],
        [_stock()], _profile(),
    )
    assert len(plan.workshop_cut_plan) == 1
    ops = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[]
    )
    saw = [op for op in ops if op.kind == OperationKind.SAW_CUT]
    # head trim + 2 piece-end cuts + tail trim
    assert len(saw) == 4
    xs = [op.x_mm for op in saw]
    assert xs == [
        Decimal("10"),           # head trim
        Decimal("2010"),         # p1 end: 10 + 2000
        Decimal("3515"),         # p2 end: 10 + 2000 + 5 + 1500
        Decimal("5990"),         # tail trim: 6000 - 10
    ]
    # interior cut carries both face angles
    interior = saw[1]
    assert interior.angle_left_deg == Decimal("90")
    assert interior.detail["piece_id"] == "p1"
    assert interior.detail["next_piece_id"] == "p2"


def test_saw_ops_carry_angles() -> None:
    piece = _piece("p1", "2000")
    piece.angle_left = Decimal("45")
    piece.angle_right = Decimal("45")
    plan = optimize_cut([piece], [_stock()], _profile())
    ops = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[]
    )
    piece_cut = [op for op in ops if op.detail.get("piece_id") == "p1"][0]
    assert piece_cut.angle_left_deg == Decimal("45")


def test_no_ops_without_authority_kinds() -> None:
    """Kinds with no authority (drainage, hinges…) emit nothing."""
    plan = optimize_cut([_piece("p1", "2000")], [_stock()], _profile())
    ops = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[]
    )
    kinds = {op.kind for op in ops}
    assert OperationKind.DRAINAGE not in kinds
    assert OperationKind.HINGE_PREP not in kinds
    doc = ops_document(ops, order_code="OT-1")
    unemitted = doc["unemitted_kinds"]
    assert isinstance(unemitted, list) and "DRAINAGE" in unemitted
    assert doc["counts_by_kind"] == {"SAW_CUT": 3}


def test_handle_prep_from_facts() -> None:
    unit = _unit(members=[_member(ProfileRole.FRAME, "1200")], handles=[_handle()])
    ops = operations_from_plan(bars=[], fact_units=[unit])
    handle_ops = [op for op in ops if op.kind == OperationKind.HANDLE_PREP]
    assert len(handle_ops) == 1
    op = handle_ops[0]
    assert op.host == "a" * 64
    assert op.x_mm == Decimal("80") and op.y_mm == Decimal("1050")
    assert op.basis == "handle_requirement_policy:hp-1@3"
    assert op.coordinate_system == CoordinateSystem.MEMBER_PLAN


def test_end_machining_only_with_overlap_authority() -> None:
    member = _member(ProfileRole.MULLION_V, "1180", overlap="15")
    ops = operations_from_plan(
        bars=[], fact_units=[_unit(members=[member])]
    )
    end_ops = [op for op in ops if op.kind == OperationKind.END_MACHINING]
    assert len(end_ops) == 2  # both ends
    assert all(op.depth_mm == Decimal("15") for op in end_ops)
    assert {op.detail["edge"] for op in end_ops} == {"START", "END"}


def test_end_machining_absent_without_overlap() -> None:
    member = _member(ProfileRole.MULLION_V, "1180", overlap="0")
    ops = operations_from_plan(
        bars=[], fact_units=[_unit(members=[member])]
    )
    assert not [op for op in ops if op.kind == OperationKind.END_MACHINING]


def test_end_machining_only_on_mullions() -> None:
    member = _member(ProfileRole.FRAME, "1180", overlap="15")
    ops = operations_from_plan(
        bars=[], fact_units=[_unit(members=[member])]
    )
    assert not [op for op in ops if op.kind == OperationKind.END_MACHINING]


def test_determinism_and_ids() -> None:
    plan = optimize_cut([_piece("p1", "2000"), _piece("p2", "1500")],
                        [_stock()], _profile())
    unit = _unit(members=[_member(ProfileRole.MULLION_V, "1180", "15")],
                 handles=[_handle()])
    ops_a = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[unit])
    ops_b = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[unit])
    assert [op.operation_id for op in ops_a] == [op.operation_id for op in ops_b]
    assert len({op.operation_id for op in ops_a}) == len(ops_a)


def test_postprocessor_renders_deterministically() -> None:
    plan = optimize_cut([_piece("p1", "2000")], [_stock()], _profile())
    ops = operations_from_plan(
        bars=plan.workshop_cut_plan, fact_units=[])
    doc = ops_document(ops, order_code="OT-1", plan_seed="abc")
    files_a = NeutralOpsPostProcessor().render(doc)
    files_b = NeutralOpsPostProcessor().render(doc)
    assert files_a == files_b
    assert "operations.json" in files_a and "operations.csv" in files_a
    csv_lines = files_a["operations.csv"].strip().split("\n")
    assert len(csv_lines) == len(ops) + 1
    assert "SAW_CUT" in csv_lines[1]
    # machine profile declares the neutral target explicitly
    machine = doc["machine"]
    assert isinstance(machine, dict)
    assert machine["controller_family"] == "NEUTRAL"
    assert machine == NEUTRAL_MACHINE_PROFILE.model_dump(mode="json")

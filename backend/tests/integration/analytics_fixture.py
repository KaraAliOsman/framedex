"""SQL-only oracle for P24, isolated and labelled DEMO.

Historical snapshots are seeded as PRE_SHOT09; no issued fixture is rewritten.
Only setup suspends domain triggers, never constraints, RLS or test execution.
The cost reports themselves use the production service and its guards.
"""

from datetime import date
from uuid import uuid4
from django.db import connection
from documents.repository import one, json_text, documentary_backend
from analytics import reports
from backend.tests.integration.test_shot09_documentary import as_user

START, END = date(2026, 10, 1), date(2026, 10, 31)


def snapshot(position, estimator, *, net="900", cost="500", typology="FIXED"):
    components = [("profiles", "400"), ("waste", "40"), ("labor", "50"), ("installation", "10")]
    cascade = {
        "net": net,
        "cost": cost,
        "steps": [{"key": k, "amount": v} for k, v in components]
        + [{"key": "discount", "amount": "-100"}],
    }
    return {
        "project": {
            "currency": "CLP",
            "total_price_net": net,
            "total_price_gross": str(int(net) * 119 // 100),
        },
        "positions": [
            {"id": str(position), "position_index": 1, "typology": typology, "is_demo": True}
        ],
        "pricing": {
            "requested_by": str(estimator),
            "applied_total_cost_net": cost,
            "result": {
                "workspace": {
                    "cascade": cascade,
                    "positions": [{"position_index": 1, "cascade": cascade}],
                }
            },
        },
    }


def seed_analytics(org, users):
    owner, manager = users["OWNER"], users["WORKSHOP_MANAGER"]
    projects, versions, positions, orders, movements, steps, visits = [], [], [], [], [], [], []
    # This isolated historical oracle cannot be constructed by rewriting a seal.
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL session_replication_role=replica")
    try:
        for index, (net, typology) in enumerate(
            (("1000", "FIXED"), ("1000", "FIXED"), ("200", "SLIDING_2L")), 1
        ):
            p, pos, version = uuid4(), uuid4(), uuid4()
            projects.append(p)
            positions.append(pos)
            versions.append(version)
            one(
                "INSERT INTO public.projects(id,org_id,code,name,client_name,created_by,status,current_revision) VALUES(%s,%s,%s,%s,'Cliente del oráculo',%s,%s,%s) RETURNING id",
                [
                    p,
                    org,
                    f"P-ORACULO-{index}",
                    f"Oráculo de analítica {index} · DEMO",
                    owner,
                    "APPROVED" if index == 1 else "QUOTED",
                    "REV-B" if index == 1 else "REV-A",
                ],
            )
            one(
                "INSERT INTO public.project_versions(id,org_id,project_id,revision_code,snapshot_json,emitted_by,emitted_at,authority_version) VALUES(%s,%s,%s,'REV-A',%s::jsonb,%s,'2026-10-10 12:00Z','PRE_SHOT09') RETURNING id",
                [
                    version,
                    org,
                    p,
                    json_text(snapshot(pos, users["ESTIMATOR"], net=net, typology=typology)),
                    owner,
                ],
            )
        chosen = uuid4()
        one(
            "INSERT INTO public.project_versions(id,org_id,project_id,revision_code,snapshot_json,emitted_by,emitted_at,authority_version) VALUES(%s,%s,%s,'REV-B',%s::jsonb,%s,'2026-10-11 12:00Z','PRE_SHOT09') RETURNING id",
            [
                chosen,
                org,
                projects[0],
                json_text(snapshot(positions[0], users["ESTIMATOR"])),
                owner,
            ],
        )
        for index, kind, decided in [
            (0, "APPROVED", "2026-10-12 12:00Z"),
            (1, "DECLINED", "2026-10-13 12:00Z"),
        ]:
            approval = uuid4()
            one(
                "INSERT INTO public.customer_approvals(id,org_id,project_id,project_version_id,token_hash,status,decided_at,decided_note,expires_at,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,'Precio','2026-11-01',%s) RETURNING id",
                [
                    approval,
                    org,
                    projects[index],
                    versions[index],
                    uuid4().hex * 2,
                    kind,
                    decided,
                    owner,
                ],
            )
            one(
                "INSERT INTO public.quote_decisions(org_id,project_id,offering_version_id,selected_version_id,approval_id,kind,decided_at,offering_sha256,selected_sha256,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id",
                [
                    org,
                    projects[index],
                    versions[index],
                    chosen if index == 0 else versions[index],
                    approval,
                    kind,
                    decided,
                    "a" * 64,
                    "b" * 64,
                    json_text(
                        {"note": "Precio", "private_signature": "No debe llegar a analítica"}
                    ),
                ],
            )
        item = one(
            "INSERT INTO public.inventory_items(org_id,sku,name,category,unit) VALUES(%s,'PERFIL-ORACULO','Perfil del oráculo · DEMO','PROFILE','M') RETURNING id",
            [org],
        )["id"]
        for index, (qty, stock, loss, useful, finished) in enumerate(
            (
                ("42", "6000", "300", "5400", "2026-10-12 18:00Z"),
                ("3", "3000", "400", "2500", "2026-10-13 18:00Z"),
            )
        ):
            order = uuid4()
            orders.append(order)
            payload = {
                "position_id": str(positions[0]),
                "optimization": {
                    "bars": {
                        "metrics": {"process_waste_mm": loss, "unplaced": 0},
                        "workshop_cut_plan": [
                            {"stock_length_mm": stock, "productive_length_mm": useful}
                        ],
                    }
                },
            }
            if index:
                payload.update(remake_of=str(orders[0]), remake_reason={"note": "Error de corte"})
            one(
                "INSERT INTO public.orders(id,org_id,project_id,project_version_id,order_code,order_type,status,payload_json,expected_at,created_at) VALUES(%s,%s,%s,%s,%s,'WORKSHOP_OT','COMPLETED',%s::jsonb,'2026-10-12','2026-10-11 12:00Z') RETURNING id",
                [order, org, projects[0], chosen, f"OT-ORACULO-{index + 1}", json_text(payload)],
            )
            movement = one(
                "INSERT INTO public.inventory_movements(org_id,item_id,movement_type,quantity,order_id,note) VALUES(%s,%s,'CONSUMPTION',%s,%s,'Medición real del oráculo') RETURNING id",
                [org, item, qty, order],
            )["id"]
            movements.append(movement)
            step = one(
                "INSERT INTO public.production_steps(org_id,order_id,sequence,code,label,status,started_at,finished_at) VALUES(%s,%s,1,'CUT','Corte','DONE','2026-10-11 12:00Z',%s) RETURNING id",
                [org, order, "2026-10-11 13:00Z" if not index else "2026-10-11 15:00Z"],
            )["id"]
            steps.append(step)
            one(
                "INSERT INTO public.production_step_events(org_id,order_id,event,created_at) VALUES(%s,%s,'WO_COMPLETED',%s) RETURNING id",
                [org, order, finished],
            )
        remnant = one(
            "INSERT INTO public.inventory_remnants(org_id,kind,stock_authority_id,length_mm,status,consumed_order_id,origin,notes) VALUES(%s,'BAR',%s,1000,'CONSUMED',%s,'MANUAL','Oráculo DEMO con valor cero declarado') RETURNING id",
            [org, uuid4(), orders[1]],
        )["id"]
        for index, received in enumerate(("2026-10-12 18:00Z", "2026-10-14 18:00Z")):
            visit = uuid4()
            visits.append(visit)
            one(
                "INSERT INTO public.field_visits(id,org_id,project_id,project_version_id,assigned_to,code,kind,planned_on,team,context_json,status,created_by) VALUES(%s,%s,%s,%s,%s,%s,'INSTALLATION','2026-10-12','Oráculo',%s::jsonb,'CLOSED',%s) RETURNING id",
                [
                    visit,
                    org,
                    projects[0],
                    chosen,
                    users["INSTALLER"],
                    f"VIS-ORACULO-{index + 1}",
                    json_text(
                        {
                            "units": [
                                {
                                    "position_id": str(positions[0]),
                                    "unit_index": index + 1,
                                    "typology": "FIXED",
                                }
                            ]
                        }
                    ),
                    manager,
                ],
            )
            one(
                "INSERT INTO public.field_events(org_id,visit_id,sequence,kind,payload_json,actor_id,created_at) VALUES(%s,%s,1,'RECEIVE','{}',%s,%s) RETURNING id",
                [org, visit, users["INSTALLER"], received],
            )
        for index, (kind, status) in enumerate(
            (("WARRANTY", "OPEN"), ("WARRANTY", "CLOSED"), ("DAMAGE", "OPEN"))
        ):
            one(
                "INSERT INTO public.field_incidents(org_id,visit_id,position_id,code,kind,unit_index,description,evidence_json,status,created_by,created_at) VALUES(%s,%s,%s,%s,%s,1,'Caso del oráculo','{}',%s,%s,'2026-10-15 12:00Z') RETURNING id",
                [org, visits[0], positions[0], f"INC-ORACULO-{index + 1}", kind, status, manager],
            )
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL session_replication_role=origin")
    with as_user(manager), documentary_backend():
        for index, order in enumerate(orders):
            current = reports.order_read(org, order)
            body = report_body(current)
            body["materials"] = [
                {
                    "id": m["id"],
                    "unit_cost": "0" if m["kind"] == "REMNANT" else "10",
                    "waste_quantity": "0"
                    if m["kind"] == "REMNANT"
                    else "3"
                    if not index
                    else "0.5",
                }
                for m in current["materials"]
            ]
            body["labor"] = [
                {"id": s["id"], "hours": "3" if not index else "0.5", "hourly_rate": "20"}
                for s in current["labor"]
            ]
            body["other_cost"] = "20" if not index else "0"
            body["bars"] = {
                "input_mm": "6000" if not index else "3000",
                "productive_mm": "5400" if not index else "2600",
                "waste_mm": "300",
                "reusable_mm": "300" if not index else "100",
                "complete": True,
            }
            reports.save_report(org, manager, order, body)
    return {
        "projects": projects,
        "versions": versions,
        "chosen": chosen,
        "positions": positions,
        "orders": orders,
        "movements": movements,
        "steps": steps,
        "remnant": remnant,
        "visits": visits,
    }


def report_body(current):
    return {
        "request_key": uuid4(),
        "expected_revision": current["revision"],
        "source_fingerprint": current["source_fingerprint"],
        "currency": "CLP",
        "source": "Oráculo manual P24 · DEMO, tarifas y horas declaradas",
        "reason": "Cierre de aceptación aislado",
        "materials": [
            {k: m[k] for k in ("id", "unit_cost", "waste_quantity")} for m in current["materials"]
        ],
        "labor": [{k: s[k] for k in ("id", "hours", "hourly_rate")} for s in current["labor"]],
        "other_cost": current["other_cost"],
        "reusable_credit": "0",
        "closed": True,
        "bars": current["bars"],
        "confirmed": True,
    }

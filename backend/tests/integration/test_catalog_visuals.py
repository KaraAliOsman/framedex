"""Private visual samples exercise the actual tenant/role/immutability boundary."""
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection, transaction
from PIL import Image
import pytest

from authentication.rls import authenticated_rls_context, catalog_backend
from backend.tests.integration.test_shot10_catalog_api import client_for, set_role
from backend.tests.integration.test_rls_context_integration import real_rows as real_rows

pytestmark = pytest.mark.rls_integration


@pytest.fixture(autouse=True)
def database_access(django_db_blocker):
    with django_db_blocker.unblock(), transaction.atomic():
        yield
        transaction.set_rollback(True)


@pytest.fixture
def stored(monkeypatch):
    objects = {}

    class Storage:
        def upload_immutable(self, path, content, content_type):
            assert content_type == "image/webp"
            assert path not in objects
            objects[path] = content

        def signed_url(self, path, seconds):
            assert seconds == 900
            return f"https://samples.example.test/{path}"

        def delete_object(self, path):
            objects.pop(path, None)

    monkeypatch.setattr("catalogs.visuals.SupabaseDocumentStorage", Storage)
    return objects


def article_for(system):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id,sku FROM public.profile_articles WHERE system_id=%s ORDER BY id LIMIT 1", [system])
        return cursor.fetchone()


def upload(rows, system, article, *, user="A", org="A"):
    output = BytesIO()
    Image.new("RGB", (32, 16), "brown").save(output, format="PNG")
    return client_for(rows, user=user, org=org).post("/api/v1/catalogs/visuals/", {
        "system_id": str(system), "kind": "PROFILE", "target_key": str(article),
        "file": SimpleUploadedFile("material.png", output.getvalue(), content_type="image/png"),
    }, format="multipart")


def test_upload_latest_clear_and_shared_catalog_are_tenant_private(real_rows, stored):
    set_role(real_rows, "WORKSHOP_MANAGER")
    set_role(real_rows, "ESTIMATOR", user="B", org="B")
    system = real_rows.demo_system
    article, sku = article_for(system)
    first = upload(real_rows, system, article)
    assert first.status_code == 201, first.content
    value = first.json()
    assert value["target_code"] == sku
    assert (value["width_px"], value["height_px"]) == (32, 16)
    assert "storage_path" not in value and "org_id" not in value and "actor_id" not in value
    assert len(stored) == 1
    path, content = next(iter(stored.items()))
    assert str(real_rows.organizations["A"]) in path
    assert value["content_sha256"] == sha256(content).hexdigest()
    assert client_for(real_rows).get("/api/v1/catalogs/visuals/", {"system_id": system}).json()[0]["id"] == value["id"]
    foreign = client_for(real_rows, user="B", org="B").get("/api/v1/catalogs/visuals/", {"system_id": system})
    assert foreign.status_code == 200 and foreign.json() == []
    cleared = client_for(real_rows).post("/api/v1/catalogs/visuals/", {
        "system_id": str(system), "kind": "PROFILE", "target_key": str(article), "cleared": "true",
    }, format="multipart")
    assert cleared.status_code == 201, cleared.content
    assert cleared.json()["image_url"] is None
    latest = client_for(real_rows).get("/api/v1/catalogs/visuals/", {"system_id": system}).json()
    assert len(latest) == 1 and latest[0]["cleared"] is True
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM public.catalog_visual_references WHERE org_id=%s", [real_rows.organizations["A"]])
        assert cursor.fetchone()[0] == 2
    assert len(stored) == 1  # Restoring the illustration retains the private audit.


@pytest.mark.parametrize("role", ["ESTIMATOR", "INSTALLER", "OWNER"])
def test_only_catalog_managers_can_change_appearance(real_rows, stored, role):
    set_role(real_rows, role)
    article, _ = article_for(real_rows.systems["A"])
    response = upload(real_rows, real_rows.systems["A"], article)
    assert response.status_code == 403
    assert not stored


def test_profile_must_belong_to_the_visible_system(real_rows, stored):
    set_role(real_rows, "WORKSHOP_MANAGER")
    article, _ = article_for(real_rows.systems["A"])
    response = upload(real_rows, real_rows.demo_system, article)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "visual_target_invalid"
    foreign_article, _ = article_for(real_rows.systems["B"])
    assert upload(real_rows, real_rows.systems["A"], foreign_article).status_code == 404
    assert not stored


def test_sql_blocks_foreign_actor_targets_and_mutation_even_if_backend_is_bypassed(real_rows, stored):
    set_role(real_rows, "WORKSHOP_MANAGER")
    system = real_rows.systems["A"]
    article, _ = article_for(system)
    result = upload(real_rows, system, article)
    assert result.status_code == 201, result.content
    row_id = result.json()["id"]
    claims = {"sub": str(real_rows.tokens["A"].user_id), "role": "authenticated", "aal": "aal1"}
    with authenticated_rls_context(claims):
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM public.catalog_visual_references")
            assert cursor.fetchone()[0] == 1
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute("INSERT INTO public.catalog_visual_references(id) VALUES(%s)", [uuid4()])
        for target, actor in [(article, real_rows.tokens["B"].user_id), (uuid4(), real_rows.tokens["A"].user_id)]:
            with pytest.raises(DatabaseError), transaction.atomic(), catalog_backend(), connection.cursor() as cursor:
                cursor.execute("INSERT INTO public.catalog_visual_references(org_id,system_id,kind,target_key,actor_id,file_name,cleared) VALUES(%s,%s,'PROFILE',%s,%s,'',true)", [real_rows.organizations["A"], system, str(target), actor])
    for statement in ["UPDATE public.catalog_visual_references SET file_name='changed' WHERE id=%s", "DELETE FROM public.catalog_visual_references WHERE id=%s"]:
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(statement, [row_id])
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("TRUNCATE public.catalog_visual_references")


def test_texture_requires_a_declared_finish_code(real_rows, stored):
    set_role(real_rows, "WORKSHOP_MANAGER")
    response = client_for(real_rows).post("/api/v1/catalogs/visuals/", {
        "system_id": str(real_rows.systems["A"]), "kind": "TEXTURE", "target_key": "invented", "cleared": "true",
    }, format="multipart")
    assert response.status_code == 400 and not stored

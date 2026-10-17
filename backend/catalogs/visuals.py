"""Private visual samples, separate from catalog engineering and issued output."""

from hashlib import sha256
from io import BytesIO
from uuid import UUID, uuid4
import warnings

from django.db import connection
from PIL import Image, ImageOps, UnidentifiedImageError

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs import service
from documents.repository import DocumentaryError
from documents.storage import SupabaseDocumentStorage
from ingest.extract import safe_file_name

MAX_BYTES = 8_000_000
MAX_PIXELS = 24_000_000


def normalized_sample(content: bytes) -> tuple[bytes, int, int]:
    if not content or len(content) > MAX_BYTES:
        raise contract_error(400, "visual_file_size", "Usa una imagen de hasta 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"} or source.width * source.height > MAX_PIXELS:
                    raise ValueError("unsupported_sample")
                oriented = ImageOps.exif_transpose(source).convert("RGBA")
                image = Image.new("RGBA", oriented.size, "white")
                image.alpha_composite(oriented)
                image = image.convert("RGB")
                image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                output = BytesIO()
                # Re-encoding removes EXIF, location, scripts and embedded payloads.
                image.save(output, format="WEBP", quality=90, method=4)
                return output.getvalue(), image.width, image.height
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise contract_error(400, "visual_file_invalid", "Usa una foto PNG, JPG o WebP de hasta 24 megapíxeles.") from error


def validate_target(org_id, system_id, kind, target_key):
    system = service.retrieve(service.SYSTEMS, org_id, system_id)
    if kind == "PROFILE":
        try:
            article_id = UUID(target_key)
        except ValueError as error:
            raise contract_error(400, "visual_target_invalid", "Elige un perfil de esta serie.") from error
        article = service.retrieve(service.ARTICLES, org_id, article_id)
        if str(article["system_id"]) != str(system_id):
            raise contract_error(400, "visual_target_invalid", "El perfil pertenece a otra serie.")
        return article["sku"]
    elif target_key not in {color["code"] for color in (system.get("finish_authority") or {}).get("colors", [])}:
        raise contract_error(400, "visual_target_invalid", "Elige un acabado de la carta de esta serie.")
    return target_key


def _response(row, storage=None):
    row = dict(row)
    path = row.pop("storage_path", None)
    row.pop("org_id", None)
    row.pop("actor_id", None)
    try:
        row["image_url"] = (storage or SupabaseDocumentStorage()).signed_url(path, 900) if path else None
    except DocumentaryError as error:
        raise contract_error(503, "visual_storage_unavailable", "No se pudo abrir la muestra. Reintenta.") from error
    return row


def latest(org_id, system_id):
    service.retrieve(service.SYSTEMS, org_id, system_id)
    with connection.cursor() as cursor:
        cursor.execute("""SELECT DISTINCT ON(v.kind,v.target_key) v.*,
            CASE WHEN v.kind='PROFILE' THEN a.sku ELSE v.target_key END AS target_code
            FROM public.catalog_visual_references v
            LEFT JOIN public.profile_articles a ON v.kind='PROFILE' AND a.id::text=v.target_key AND a.system_id=v.system_id
            WHERE v.org_id=%s AND v.system_id=%s ORDER BY v.kind,v.target_key,v.created_at DESC,v.id DESC""", [org_id, system_id])
        names = [column[0] for column in cursor.description]
        entries = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    return [_response(row) for row in entries]


def save(*, org_id, actor_id, system_id, kind, target_key, upload=None, cleared=False):
    target_code = validate_target(org_id, system_id, kind, target_key)
    file_name = ""
    content_hash = None
    path = None
    width = height = None
    storage = None
    identity = uuid4()
    if not cleared:
        if upload is None or not safe_file_name(upload.name) or len(upload.name) > 200:
            raise contract_error(400, "visual_file_missing", "Elige una foto PNG, JPG o WebP.")
        file_name = upload.name
        content, width, height = normalized_sample(upload.read(MAX_BYTES + 1))
        content_hash = sha256(content).hexdigest()
        path = f"catalog-visuals/{org_id}/{identity}/sample.webp"
        storage = SupabaseDocumentStorage()
        try:
            storage.upload_immutable(path, content, "image/webp")
        except DocumentaryError as error:
            raise contract_error(503, "visual_storage_unavailable", "No se pudo guardar la muestra. Reintenta.") from error
    try:
        with connection.cursor() as cursor, catalog_backend():
            cursor.execute("""INSERT INTO public.catalog_visual_references
              (id,org_id,system_id,kind,target_key,actor_id,file_name,storage_path,content_sha256,width_px,height_px,cleared)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
              [identity, org_id, system_id, kind, target_key, actor_id, file_name, path, content_hash, width, height, cleared])
            names = [column[0] for column in cursor.description]
            row = dict(zip(names, cursor.fetchone(), strict=True))
    except Exception:
        if path and storage:
            try:
                storage.delete_object(path)
            except DocumentaryError:
                pass
        raise
    row["target_code"] = target_code
    return _response(row, storage)

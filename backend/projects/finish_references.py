"""Business finish references: the company's own photo of a material, kept as
original plus a prepared repeatable sample, linked to the catalog finish it
represents visually. Presentation only — finish authority, price and every
fabrication value stay with the catalog. A photo never certifies a colour.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import io
from uuid import UUID

from django.db import transaction
from PIL import Image, ImageOps, UnidentifiedImageError

from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from pricing.repository import rows

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
PREPARED_PX = 1024
_TYPES = {"PNG": ("png", "image/png"), "JPEG": ("jpg", "image/jpeg"), "WEBP": ("webp", "image/webp")}
_COLUMNS = (
    "id, name, finish_code, original_type, tile_mm, grain, version, created_at, updated_at"
)


def _public(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "finish_code": row["finish_code"],
        "original_type": row["original_type"],
        "tile_mm": str(row["tile_mm"]),
        "grain": row["grain"],
        "version": row["version"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _fraction(value, default: Decimal) -> Decimal:
    if value in (None, ""):
        return default
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise contract_error(400, "finish_reference_crop_invalid", "El recorte no es válido.") from error
    if number < 0 or number > 1:
        raise contract_error(400, "finish_reference_crop_invalid", "El recorte no es válido.")
    return number


def _tile(value) -> Decimal:
    try:
        number = Decimal(str(value if value not in (None, "") else "300"))
    except InvalidOperation as error:
        raise contract_error(400, "finish_reference_tile_invalid", "Indica el tamaño de la muestra en mm.") from error
    if number < 20 or number > 3000:
        raise contract_error(400, "finish_reference_tile_invalid", "La muestra debe medir entre 20 y 3000 mm.")
    return number.quantize(Decimal("0.01"))


def _grain(value) -> str:
    grain = str(value or "ALONG").upper()
    if grain not in ("ALONG", "ACROSS", "NONE"):
        raise contract_error(400, "finish_reference_grain_invalid", "Elige la dirección de la veta.")
    return grain


def _encode(image: Image.Image, fmt: str, **options) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **options)
    return buffer.getvalue()


def prepare(content: bytes, crop: dict) -> tuple[bytes, str, bytes]:
    """Return (clean original, its content type, prepared square JPEG).

    The original is re-encoded without metadata (location, camera); the
    prepared sample is the chosen square, resized for repetition."""
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise contract_error(400, "finish_reference_size_invalid", "La imagen debe pesar hasta 8 MB.")
    try:
        with Image.open(io.BytesIO(content)) as probe:
            probe.verify()
        image = Image.open(io.BytesIO(content))
        fmt = image.format or ""
        image = ImageOps.exif_transpose(image)
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise contract_error(400, "finish_reference_type_invalid", "Sube una imagen PNG, JPEG o WebP.") from error
    if fmt not in _TYPES:
        raise contract_error(400, "finish_reference_type_invalid", "Sube una imagen PNG, JPEG o WebP.")
    if image.width < 64 or image.height < 64:
        raise contract_error(400, "finish_reference_too_small", "La imagen es demasiado pequeña para una muestra.")
    rgb = image.convert("RGB")
    _, content_type = _TYPES[fmt]
    original = _encode(rgb if fmt == "JPEG" else image.convert("RGBA" if fmt == "PNG" else "RGB"), fmt, **({"quality": 92} if fmt == "JPEG" else {}))
    side = min(rgb.width, rgb.height)
    size = _fraction(crop.get("size"), Decimal(1))
    box_side = max(int(Decimal(side) * size), 32)
    left = int(_fraction(crop.get("x"), Decimal("0.5")) * (rgb.width - box_side)) if rgb.width > box_side else 0
    top = int(_fraction(crop.get("y"), Decimal("0.5")) * (rgb.height - box_side)) if rgb.height > box_side else 0
    square = rgb.crop((left, top, left + box_side, top + box_side))
    prepared = _encode(square.resize((PREPARED_PX, PREPARED_PX), Image.Resampling.LANCZOS), "JPEG", quality=88)
    return original, content_type, prepared


def _finish_exists(org_id, finish_code: str) -> bool:
    """The code must be a finish the organization can read in some catalog."""
    found = rows(
        "SELECT 1 FROM public.profile_systems s "
        "WHERE s.is_active AND (s.is_global OR s.org_id=%s) AND s.finish_authority IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM jsonb_array_elements(s.finish_authority->'combinations') c "
        "WHERE c->>'code'=%s OR c->>'interior'=%s OR c->>'exterior'=%s) LIMIT 1",
        [org_id, finish_code, finish_code, finish_code],
    )
    return bool(found)


def list_references(org_id) -> dict:
    found = rows(
        f"SELECT {_COLUMNS} FROM public.finish_references WHERE org_id=%s AND archived_at IS NULL "
        "ORDER BY name, created_at",
        [org_id],
    )
    return {"items": [_public(row) for row in found]}


def create_reference(org_id, actor_id, data: dict, content: bytes) -> dict:
    name = str(data.get("name") or "").strip()[:120]
    code = str(data.get("finish_code") or "").strip().upper()
    if not name:
        raise contract_error(400, "finish_reference_name_missing", "Ponle un nombre a la muestra.")
    if not code or not _finish_exists(org_id, code):
        raise contract_error(
            400, "finish_reference_finish_unknown", "Elige un acabado que exista en tus catálogos."
        )
    original, content_type, prepared = prepare(content, data)
    original_sha = hashlib.sha256(original).hexdigest()
    prepared_sha = hashlib.sha256(prepared).hexdigest()
    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[content_type]
    base = f"org_{org_id}/finish-references"
    original_key = f"{base}/{original_sha[:20]}-original.{extension}"
    prepared_key = f"{base}/{prepared_sha[:20]}-prepared.jpg"
    storage = SupabaseDocumentStorage()
    storage.upload_immutable(original_key, original, content_type)
    storage.upload_immutable(prepared_key, prepared, "image/jpeg")
    with transaction.atomic(), documentary_backend():
        # One active reference per finish: a new photo replaces the previous
        # one in the library while its stored objects remain.
        current = rows(
            "SELECT version FROM public.finish_references WHERE org_id=%s AND finish_code=%s "
            "AND archived_at IS NULL FOR UPDATE",
            [org_id, code],
        )
        if current:
            rows(
                "UPDATE public.finish_references SET archived_at=now(), updated_at=now() "
                "WHERE org_id=%s AND finish_code=%s AND archived_at IS NULL RETURNING id",
                [org_id, code],
            )
        created = rows(
            "INSERT INTO public.finish_references(org_id,name,finish_code,original_key,original_sha256,"
            "original_type,prepared_key,prepared_sha256,tile_mm,grain,version,created_by) "
            f"VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_COLUMNS}",
            [
                org_id, name, code, original_key, original_sha, content_type, prepared_key,
                prepared_sha, _tile(data.get("tile_mm")), _grain(data.get("grain")),
                (current[0]["version"] + 1) if current else 1, actor_id,
            ],
        )
    return _public(created[0])


def update_reference(org_id, reference_id: UUID, data: dict) -> dict:
    with transaction.atomic(), documentary_backend():
        current = rows(
            f"SELECT {_COLUMNS} FROM public.finish_references WHERE org_id=%s AND id=%s "
            "AND archived_at IS NULL FOR UPDATE",
            [org_id, reference_id],
        )
        if not current:
            raise contract_error(404, "finish_reference_not_found", "La muestra ya no existe.")
        row = current[0]
        name = str(data.get("name", row["name"]) or "").strip()[:120]
        if not name:
            raise contract_error(400, "finish_reference_name_missing", "Ponle un nombre a la muestra.")
        updated = rows(
            "UPDATE public.finish_references SET name=%s, tile_mm=%s, grain=%s, version=version+1, "
            f"updated_at=now() WHERE org_id=%s AND id=%s RETURNING {_COLUMNS}",
            [
                name,
                _tile(data.get("tile_mm", row["tile_mm"])),
                _grain(data.get("grain", row["grain"])),
                org_id,
                reference_id,
            ],
        )
    return _public(updated[0])


def archive_reference(org_id, reference_id: UUID) -> dict:
    with transaction.atomic(), documentary_backend():
        found = rows(
            "UPDATE public.finish_references SET archived_at=now(), updated_at=now() "
            "WHERE org_id=%s AND id=%s AND archived_at IS NULL RETURNING id",
            [org_id, reference_id],
        )
    if not found:
        raise contract_error(404, "finish_reference_not_found", "La muestra ya no existe.")
    return list_references(org_id)


def reference_image(org_id, reference_id: UUID, variant: str) -> tuple[bytes, str]:
    found = rows(
        "SELECT original_key, original_sha256, original_type, prepared_key, prepared_sha256 "
        "FROM public.finish_references WHERE org_id=%s AND id=%s",
        [org_id, reference_id],
    )
    if not found:
        raise contract_error(404, "finish_reference_not_found", "La muestra ya no existe.")
    row = found[0]
    original = variant == "original"
    key = row["original_key"] if original else row["prepared_key"]
    digest = row["original_sha256"] if original else row["prepared_sha256"]
    content = SupabaseDocumentStorage().download_bounded(key, MAX_UPLOAD_BYTES * 2)
    if not content or hashlib.sha256(content).hexdigest() != digest:
        raise contract_error(409, "finish_reference_integrity_failed", "No se pudo verificar la imagen guardada.")
    return content, row["original_type"] if original else "image/jpeg"

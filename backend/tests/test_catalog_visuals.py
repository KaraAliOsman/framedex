"""Uploaded appearance is a sanitized private image, never engineering input."""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import pytest

from authentication.errors import ContractAPIException
from catalogs import visuals
from catalogs.visual_views import VisualUploadSerializer


def image_bytes(mode="RGB", size=(16, 8), color="red", format="PNG", **kwargs):
    output = BytesIO()
    Image.new(mode, size, color).save(output, format=format, **kwargs)
    return output.getvalue()


def test_orientation_metadata_and_size_are_normalized():
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "Private metadata"
    data = image_bytes(size=(4096, 1024), format="JPEG", exif=exif)
    content, width, height = visuals.normalized_sample(data)
    assert (width, height) == (512, 2048)
    with Image.open(BytesIO(content)) as result:
        assert result.format == "WEBP"
        assert result.size == (512, 2048)
        assert not result.getexif()
    assert b"Private metadata" not in content


def test_transparent_profile_samples_use_a_white_matte():
    content, _, _ = visuals.normalized_sample(image_bytes("RGBA", color=(0, 0, 0, 0)))
    with Image.open(BytesIO(content)) as result:
        assert all(channel > 245 for channel in result.convert("RGB").getpixel((4, 4)))


@pytest.mark.parametrize("content", [b"", b"<svg onload='alert(1)'/>", b"not a photo", image_bytes(format="GIF")])
def test_non_raster_or_unsupported_inputs_are_rejected(content):
    with pytest.raises(ContractAPIException) as error:
        visuals.normalized_sample(content)
    assert error.value.status_code == 400


def test_byte_and_pixel_limits_are_checked_before_decoding(monkeypatch):
    monkeypatch.setattr(visuals, "MAX_BYTES", 20)
    with pytest.raises(ContractAPIException):
        visuals.normalized_sample(b"x" * 21)
    monkeypatch.setattr(visuals, "MAX_BYTES", 8_000_000)
    monkeypatch.setattr(visuals, "MAX_PIXELS", 64)
    with pytest.raises(ContractAPIException):
        visuals.normalized_sample(image_bytes(size=(9, 8)))


def test_upload_and_clear_cannot_be_accidentally_combined():
    value = VisualUploadSerializer(data={
        "system_id": "00000000-0000-4000-8000-000000000001", "kind": "TEXTURE",
        "target_key": "WHITE", "cleared": True,
        "file": SimpleUploadedFile("sample.png", image_bytes(), content_type="image/png"),
    })
    assert not value.is_valid()
    assert "file" in value.errors

"""Issuer ink on paper. Color contrast is presentation, never engine authority."""

import re

TEAL = "#075F5A"
PAPER = "#FFFFFF"


def contrast(color: str, background: str = PAPER) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    first, second = sorted((luminance(color), luminance(background)))
    return (second + 0.05) / (first + 0.05)


def effective_color(requested: object) -> tuple[str, bool]:
    color = str(requested or TEAL).upper()
    valid = bool(re.fullmatch(r"#[0-9A-F]{6}", color)) and contrast(color) >= 4.5
    return (color if valid else TEAL, not valid)


def snapshot_preferences(row: dict) -> dict:
    color, fallback = effective_color(row.get("brand_primary_color"))
    return {
        "brand_schema": 1,
        "brand_primary_color": color,
        "brand_color_fallback": fallback,
        "document_attribution": bool(row.get("document_attribution", False)),
        "portal_attribution": bool(row.get("portal_attribution", True)),
    }

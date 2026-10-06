"""Supplier instructions from frozen engine pieces, with no re-entered sizes."""

from decimal import Decimal

from pydantic import Field

from dekopen_engine.glass_composition import GlassModel, GlassProcessing, format_glass_notation
from dekopen_engine.models import GlassPiece


class GlassSupplierRow(GlassModel):
    order_code: str
    position_index: int = Field(ge=1)
    location: str
    piece_index: int = Field(ge=1)
    width_mm: Decimal
    height_mm: Decimal
    integer_dimensions: bool
    quantity: int = Field(ge=1)
    composition: str
    article_sku: str | None
    processing: GlassProcessing | None
    instructions: tuple[str, ...]
    label_codes: tuple[str, ...]


def supplier_glass_rows(*, order_code: str, position_index: int, location: str, quantity: int,
                        pieces: list[GlassPiece], labels: dict[tuple[str, str | None], tuple[str, ...]] | None = None,
                        synthetic: bool = False
                        ) -> tuple[GlassSupplierRow, ...]:
    if quantity < 1:
        raise ValueError("La cantidad de vidrio debe ser positiva.")
    output = []
    for index, piece in enumerate(pieces, 1):
        instructions = []
        if synthetic:
            instructions.append("DEMO · catálogo sintético; no certifica seguridad ni rendimiento térmico.")
        notation = format_glass_notation(piece.composition) if piece.composition else piece.glass_spec
        if not notation:
            raise ValueError("Sin dato · falta la composición sellada del vidrio.")
        if piece.shape:
            instructions.append("Pieza con contorno: adjuntar el plano sellado; la caja envolvente no es su forma de corte.")
        integer = piece.width_mm == piece.width_mm.to_integral_value() and piece.height_mm == piece.height_mm.to_integral_value()
        if not integer:
            instructions.append("Medida con decimales: solicitar aceptación de la precisión exacta; no redondear.")
        if "templado" in notation.lower():
            instructions.append("Templado a medida exacta; no se recorta en taller.")
        codes = (labels or {}).get((piece.bay_id, piece.leaf_id)) or tuple(
            f"{order_code}-G{index:02d}-U{unit:02d}" for unit in range(1, quantity + 1))
        if len(codes) != quantity:
            raise ValueError("Las etiquetas no coinciden con la cantidad sellada.")
        output.append(GlassSupplierRow(order_code=order_code, position_index=position_index,
            location=location, piece_index=index, width_mm=piece.width_mm, height_mm=piece.height_mm,
            integer_dimensions=integer, quantity=quantity, composition=notation,
            article_sku=piece.article_sku, processing=piece.processing,
            instructions=tuple(instructions), label_codes=codes))
    return tuple(output)

"""Synthetic prices for the guided-series browser acceptance; no manufacturer authority."""

from pathlib import Path

from openpyxl import Workbook


def write_fixture(filename, rows):
    target = Path(__file__).resolve().parents[1] / "frontend/tests/e2e/fixtures" / filename
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Precios de prueba"
    sheet.append(["Código", "Descripción", "Unidad", "Precio neto"])
    for row in rows:
        sheet.append(row)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(target)
    workbook.close()


def main():
    write_fixture("p03-precios-sinteticos.xlsx", [
        ("PRO-F", "Marco sintético", "BARRA", "45000,1234"),
        ("PRO-S", "Hoja sintética", "BARRA", "46000,5678"),
        ("PRO-B", "Junquillo sintético", "METRO", "9000,0001"),
        ("001", "Código con ceros iniciales", "UNIDAD", "0,2500"),
        ("002", "Vidrio de prueba", "M²", "42000,9999"),
        *[(f"EXTRA-{index}", f"Insumo sintético {index}", "KIT", "1234,5678") for index in range(7)],
    ])
    write_fixture("p03-alta-precios-sinteticos.xlsx", [
        ("PRO-F", "Marco sintético", "BARRA", "45000,1234"),
        ("PRO-S", "Hoja sintética", "BARRA", "46000,5678"),
        ("PRO-B", "Junquillo sintético", "BARRA", "9000,0001"),
        ("STEEL-F", "Refuerzo de marco sintético", "BARRA", "8000,0000"),
        ("STEEL-S", "Refuerzo de hoja sintético", "BARRA", "8000,0000"),
        ("GLASS-24", "Vidrio sintético", "M²", "20000,0000"),
        ("PRO-TURN", "Herraje sintético", "KIT", "12000,0000"),
        ("SCREW-F", "Tornillo de marco sintético", "EA", "20,0000"),
        ("SCREW-S", "Tornillo de hoja sintético", "EA", "20,0000"),
        ("001", "Código con ceros iniciales", "UNIDAD", "0,2500"),
        ("002", "Insumo adicional sintético", "UNIDAD", "0,5000"),
        ("003", "Insumo adicional sintético", "UNIDAD", "0,7500"),
    ])


if __name__ == "__main__":
    main()

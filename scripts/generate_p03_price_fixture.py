"""Synthetic prices for the guided-series browser acceptance; no manufacturer authority."""

from pathlib import Path

from openpyxl import Workbook


def main():
    target = Path(__file__).resolve().parents[1] / "frontend/tests/e2e/fixtures/p03-precios-sinteticos.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Precios de prueba"
    sheet.append(["Código", "Descripción", "Unidad", "Precio neto"])
    rows = [
        ("PRO-F", "Marco sintético", "BARRA", "45000,1234"),
        ("PRO-S", "Hoja sintética", "BARRA", "46000,5678"),
        ("PRO-B", "Junquillo sintético", "METRO", "9000,0001"),
        ("001", "Código con ceros iniciales", "UNIDAD", "0,2500"),
        ("002", "Vidrio de prueba", "M²", "42000,9999"),
        *[(f"EXTRA-{index}", f"Insumo sintético {index}", "KIT", "1234,5678") for index in range(7)],
    ]
    for row in rows:
        sheet.append(row)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(target)
    workbook.close()


if __name__ == "__main__":
    main()

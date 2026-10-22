"""An arbitrary supplier table stays exact and bounded before human review."""

from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import pytest
from openpyxl import Workbook

from authentication.errors import ContractAPIException
from pricing import supplier_prices as prices

MAPPING = {"sku": "Código", "description": "Descripción", "unit": "Unidad", "unit_cost": "Precio"}
HEADER = "Código;Descripción;Unidad;Precio\n"


def csv_file(count=12, price="1234,5678"):
    return (HEADER + "".join(f"{index:03};Perfil {index};Barra;{price}\n" for index in range(count))).encode("utf-8-sig")


def workbook(rows):
    book, buffer = Workbook(), BytesIO()
    book.active.append(list(MAPPING.values()))
    for row in rows:
        book.active.append(row)
    book.save(buffer)
    book.close()
    return buffer.getvalue()


def test_inspection_suggests_unique_columns_and_shows_only_ten_original_rows():
    result = prices.inspect(csv_file(), "proveedor.csv")
    assert result["suggested_mapping"] == MAPPING
    assert result["total"] == 12 and len(result["preview"]) == 10
    assert result["preview"][0] == ["000", "Perfil 0", "Barra", "1234,5678"]


def test_csv_preserves_codes_exact_prices_and_does_not_convert_units():
    result = prices.parse(csv_file(), "proveedor.csv", MAPPING, ",")
    assert len(result) == 12
    assert result[0] == {"sku": "000", "description": "Perfil 0", "unit": "BAR", "unit_cost": Decimal("1234.5678")}
    bad = csv_file().replace(b"Barra", b"KG")
    with pytest.raises(ContractAPIException, match="kilos"):
        prices.parse(bad, "proveedor.csv", MAPPING, ",")


def test_xlsx_numeric_lexemes_are_exact_independent_of_text_locale():
    content = workbook([["001", "Texto", "M", 1]])
    buffer = BytesIO()
    with ZipFile(BytesIO(content)) as original, ZipFile(buffer, "w") as changed:
        for item in original.infolist():
            value = original.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                value = value.replace(b"<v>1</v>", b"<v>1.2345</v>")
            changed.writestr(item, value)
    result = prices.parse(buffer.getvalue(), "tarifa.xlsx", MAPPING, ",")
    assert result[0]["unit_cost"] == Decimal("1.2345") and result[0]["sku"] == "001"
    buffer2 = BytesIO()
    with ZipFile(BytesIO(buffer.getvalue())) as original, ZipFile(buffer2, "w") as changed:
        for item in original.infolist():
            changed.writestr(item, original.read(item.filename).replace(b"<v>1.2345</v>", b"<v>1.234500000000000001</v>"))
    with pytest.raises(ContractAPIException, match="cuatro decimales"):
        prices.parse(buffer2.getvalue(), "tarifa.xlsx", MAPPING, ",")


@pytest.mark.parametrize("value", ["1.234,50", "1 234,50", "NaN", "Infinity", "-1", "0,00001", "=1+1", ""])
def test_invalid_prices_reject_the_entire_csv(value):
    with pytest.raises(ContractAPIException):
        prices.parse(csv_file(price=value), "lista.csv", MAPPING, ",")


@pytest.mark.parametrize("mapping", [{}, {**MAPPING, "sku": []}, {**MAPPING, "sku": "Precio"}, {**MAPPING, "sku": "Ausente"}])
def test_mapping_never_accepts_missing_repeated_or_malformed_columns(mapping):
    with pytest.raises(ContractAPIException):
        prices.parse(csv_file(), "lista.csv", mapping, ",")


def test_duplicate_codes_and_formulas_cannot_be_imported():
    with pytest.raises(ContractAPIException, match="repetido"):
        prices.parse((HEADER + "A;Perfil;M;1\nA;Otro;M;2\n").encode(), "lista.csv", MAPPING, ".")
    with pytest.raises(ContractAPIException, match="fórmulas"):
        prices.inspect(workbook([["A", "Perfil", "M", "=1+1"]]), "lista.xlsx")


def test_limits_and_empty_files_fail_without_partial_rows():
    for content, name in ((b"", "lista.csv"), (b"x" * (prices.MAX_BYTES + 1), "lista.csv"),
            (csv_file(5001), "lista.csv"), (b"bad zip", "lista.xlsx"), (csv_file(), "lista.pdf")):
        with pytest.raises(ContractAPIException):
            prices.inspect(content, name)


def test_ambiguous_headers_are_not_auto_selected():
    data = b"SKU;Codigo;Descripcion;Unidad;Precio\nA;B;Perfil;M;1\n"
    assert prices.inspect(data, "lista.csv")["suggested_mapping"]["sku"] == ""

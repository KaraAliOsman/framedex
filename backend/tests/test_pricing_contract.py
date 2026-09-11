"""SHOT-08 import precision and transport boundaries, without production stubs."""

from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from openpyxl import Workbook
import pytest

from dekopen_engine.commercial import PricingError
from pricing.serializers import CostItemSerializer, FxSerializer, PriceRequestSerializer
from pricing.views import DecimalJSONParser, price_response
from pricing.xlsx_import import parse_xlsx

MAPPING = {'sku':'SKU','description':'Description','unit':'Unit','unit_cost':'Cost'}


def workbook_bytes(rows):
    book = Workbook()
    sheet = book.active
    sheet.append(['SKU','Description','Unit','Cost'])
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    book.save(buffer)
    book.close()
    return buffer.getvalue()


def test_xlsx_mapping_preserves_four_decimals_description_and_locale():
    output = parse_xlsx(workbook_bytes([['A','Profile','BAR','1,2345']]),MAPPING,',')
    assert output == [{'sku':'A','description':'Profile','unit':'BAR','unit_cost':Decimal('1.2345')}]


@pytest.mark.parametrize('price', ['1,234.50','1 234,50','NaN','Infinity','-1','0,00001'])
def test_xlsx_rejects_ambiguous_or_invalid_prices(price):
    with pytest.raises(PricingError):
        parse_xlsx(workbook_bytes([['A','Profile','BAR',price]]),MAPPING,',')


@pytest.mark.parametrize('rows', [
    [['A','Profile','BAR','=1+1']], [['A','Profile','BAR','1'],['A','Other','BAR','2']],
    [['A','Profile','UNKNOWN','1']], [['','Profile','M','1']],
])
def test_xlsx_rejects_formulas_duplicates_and_invalid_units(rows):
    with pytest.raises(PricingError):
        parse_xlsx(workbook_bytes(rows),MAPPING,'.')


def test_numeric_xml_lexeme_is_not_rounded_through_binary_number():
    content = workbook_bytes([['A','Numeric authority','M',1]])
    target = BytesIO()
    with ZipFile(BytesIO(content)) as original, ZipFile(target,'w') as changed:
        for item in original.infolist():
            data = original.read(item.filename)
            if item.filename == 'xl/worksheets/sheet1.xml':
                data = data.replace(b'<v>1</v>',b'<v>1.000000000000000001</v>')
            changed.writestr(item,data)
    with pytest.raises(PricingError,match='xlsx_invalid_price_row_2'):
        parse_xlsx(target.getvalue(),MAPPING,'.')


def test_decimal_json_parser_preserves_lexeme_and_rejects_nonfinite():
    assert DecimalJSONParser().parse(BytesIO(b'{"value":1.2345}'))['value'] == Decimal('1.2345')
    with pytest.raises(Exception,match='Revisa'):
        DecimalJSONParser().parse(BytesIO(b'{"value":NaN}'))


def test_admin_cost_precision_and_unknown_fields_are_rejected():
    data = {'cost_list_id':'11111111-1111-4111-8111-111111111111','sku':'A',
            'unit':'M','item_type':'PROFILE','unit_cost':'1.00001'}
    assert not CostItemSerializer(data=data).is_valid()
    data['unit_cost']='1.2345'
    assert CostItemSerializer(data=data).is_valid()
    data['org_id']='22222222-2222-4222-8222-222222222222'
    assert not CostItemSerializer(data=data).is_valid()


def test_fx_requires_positive_rate_and_explicit_source():
    data = {'base_currency':'USD','quote_currency':'CLP','observed_rate':'0',
            'observed_date':'2026-09-10','effective_date':'2026-09-10','source':'Owner observation'}
    assert not FxSerializer(data=data).is_valid()
    data['observed_rate']='900.12345678'
    assert FxSerializer(data=data).is_valid()


def test_pricing_request_cannot_supply_cost_or_actor():
    data = {'project_id':'11111111-1111-4111-8111-111111111111','pricing_mode':'COST_PLUS_MARGIN',
            'currency':'CLP','effective_date':'2026-09-10','reason':'Review','cost':'0'}
    assert not PriceRequestSerializer(data=data).is_valid()


def test_public_response_uses_line_total_strings():
    result = price_response({'lines':((1,Decimal('2')),),'project_net':Decimal('2'),
                             'project_tax':Decimal('0'),'project_gross':Decimal('2')})
    assert result['lines']==[{'position_index':1,'line_net':'2'}]
    assert result['project_net']=='2'

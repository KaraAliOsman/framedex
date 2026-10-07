from decimal import Decimal, localcontext
import json
from pathlib import Path
from typing import cast

import pytest

from dekopen_engine.billing import ai_usage_cost_usd
from engine.tests.ai_cost_cases import ai_cost_cases


def test_provider_usage_frozen_tariffs_and_unknown_cost() -> None:
    assert ai_cost_cases() == json.loads(Path(__file__).with_name("golden_ai_cost.json").read_text())
    with localcontext() as context:
        context.prec = 2
        assert ai_usage_cost_usd(91, 132, Decimal("1.25"), Decimal("3.50")) == Decimal("0.00057575")
        assert ai_usage_cost_usd(1, 0, Decimal("0.00000001"), Decimal(0)) == Decimal("0.00000000000001")


@pytest.mark.parametrize("tokens", [-1, True, Decimal(1)])
def test_invalid_usage_cannot_become_money(tokens: int | Decimal) -> None:
    with pytest.raises(ValueError):
        ai_usage_cost_usd(cast(int, tokens), 1, Decimal(1), Decimal(1))

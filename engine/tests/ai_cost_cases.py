from decimal import Decimal
from dekopen_engine.billing import ai_usage_cost_usd


def ai_cost_cases() -> list[dict[str, int | str | None]]:
    cases = [(91, 132, "1.25", "3.50"), (1, 0, "0.00000001", "0"),
             (2147483647, 2147483647, "1000000", "1000000"), (0, 0, "0", "0"),
             (91, 132, None, None)]
    result: list[dict[str, int | str | None]] = []
    for prompt, completion, input_rate, output_rate in cases:
        cost = ai_usage_cost_usd(prompt, completion, Decimal(input_rate) if input_rate is not None else None,
                                 Decimal(output_rate) if output_rate is not None else None)
        result.append({"tokens_prompt": prompt, "tokens_completion": completion,
                       "input_usd_per_million": input_rate, "output_usd_per_million": output_rate,
                       "estimated_cost_usd": format(cost, "f") if cost is not None else None})
    return result

"""Rational generating functions for whole-tune complexity counts."""

from functools import lru_cache


def polynomial_sum(*terms: list[int]) -> list[int]:
    result = [0] * max(map(len, terms))
    for term in terms:
        for i, value in enumerate(term):
            result[i] += value
    return result


def polynomial_product(*factors: list[int]) -> list[int]:
    result = [1]
    for factor in factors:
        product = [0] * (len(result) + len(factor) - 1)
        for i, left in enumerate(result):
            for j, right in enumerate(factor):
                product[i + j] += left * right
        result = product
    return result


def power(exponent: int, coefficient: int = 1) -> list[int]:
    return [0] * exponent + [coefficient]


def coefficients(numerator: list[int], denominator: list[int], limit: int) -> list[int]:
    """Expand N/Q using Q[0] = 1, with fixed work per coefficient."""
    if denominator[0] != 1:
        raise ValueError("The rational denominator must have constant term one")
    result: list[int] = []
    for cost in range(limit + 1):
        value = numerator[cost] if cost < len(numerator) else 0
        value -= sum(
            denominator[i] * result[cost - i]
            for i in range(1, min(cost + 1, len(denominator)))
        )
        result.append(value)
    return result


def duration_function() -> tuple[list[int], list[int]]:
    """D = (1-xt)(1+t+s) / ((1-x)(1-2t)(1+t)).

    Here x=z**BINARY_COST, t=z**NUMERATOR_COST, s=z**THIRD_COST.
    Counts reduced numerators only, including the exceptional numerator one.
    """
    numerator = polynomial_product(
        polynomial_sum([1], power(BINARY_COST + NUMERATOR_COST, -1)),
        polynomial_sum([1], power(NUMERATOR_COST), power(THIRD_COST)),
    )
    denominator = polynomial_product(
        polynomial_sum([1], power(BINARY_COST, -1)),
        polynomial_sum([1], power(NUMERATOR_COST, -2)),
        polynomial_sum([1], power(NUMERATOR_COST)),
    )
    return numerator, denominator


@lru_cache(maxsize=1)
def tune_counts(limit: int) -> dict[str, list[int]]:
    """Count completions at each stage, all by rational series recurrences.

    D=N/Q, P=(1+z**STEP_COST)/(1-z**STEP_COST), G=1+z**REST_COST*D.
    H=1/(1-z**ATTACK_COST*D*P*G) counts possibly empty note suffixes.
    The three completion series are H, D*H and G*D*H.
    """
    n, q = duration_function()
    pitch_n = polynomial_sum([1], power(STEP_COST))
    pitch_q = polynomial_sum([1], power(STEP_COST, -1))
    gap_n = polynomial_sum(q, polynomial_product(power(REST_COST), n))
    suffix_n = polynomial_product(q, q, pitch_q)
    denominator = polynomial_sum(
        suffix_n,
        polynomial_product(power(ATTACK_COST, -1), n, pitch_n, gap_n),
    )
    tables = {
        "duration": coefficients(n, q, limit),
        "suffix": coefficients(suffix_n, denominator, limit),
        "after_gap": coefficients(
            polynomial_product(n, q, pitch_q), denominator, limit
        ),
        "after_step": coefficients(
            polynomial_product(n, pitch_q, gap_n), denominator, limit
        ),
    }
    # Strictly preceding layers: z*T/(1-z) and z*D/(1-z).
    cumulative_q = [1, -1]
    tables["starts"] = coefficients(
        polynomial_product(power(ATTACK_COST + 1), n, q, pitch_q),
        polynomial_product(denominator, cumulative_q),
        limit + 1,
    )
    tables["duration_starts"] = coefficients(
        polynomial_product(power(1), n),
        polynomial_product(q, cumulative_q),
        limit + 1,
    )
    return tables


# Enumeration constants, editable together before release, never runtime settings.
ATTACK_COST = 1
STEP_COST = 1
REST_COST = 1
NUMERATOR_COST = 4
BINARY_COST = 1
THIRD_COST = 3

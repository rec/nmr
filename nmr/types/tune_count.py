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


def pitch_cost(step: int) -> int:
    return max(0, abs(step) - FREE_STEPS) * STEP_COST


def note_duration_function() -> tuple[list[int], list[int]]:
    """Remove durations below 1/24 beat from the unrestricted duration series.

    For numerator bit length h+1, binary durations below the cutoff have
    denominator exponent h+5 (partially) or >=h+6 (entirely). Durations with
    a factor of three are excluded at exponents >=h+4.
    With t=z**(NUMERATOR_COST+BINARY_COST), the respective numerator counts
    have series C=(1-t-t²)/((1-2t)(1+t)), A=(1-t)/(1-2t),
    and B=(1-t)/((1-2t)(1+t)).
    """
    n, q = duration_function()
    diagonal = NUMERATOR_COST + BINARY_COST
    binary_q = polynomial_sum([1], power(BINARY_COST, -1))
    removed_q = polynomial_product(
        binary_q,
        polynomial_sum([1], power(diagonal, -2)),
        polynomial_sum([1], power(diagonal)),
    )
    removed_n = polynomial_sum(
        polynomial_product(
            power(5 * BINARY_COST),
            binary_q,
            polynomial_sum([1], power(diagonal, -1), power(2 * diagonal, -1)),
        ),
        polynomial_product(
            power(6 * BINARY_COST),
            polynomial_sum([1], power(2 * diagonal, -1)),
        ),
        polynomial_product(
            power(4 * BINARY_COST + THIRD_COST),
            polynomial_sum([1], power(diagonal, -1)),
        ),
    )
    numerator = polynomial_sum(
        polynomial_product(n, removed_q),
        [-i for i in polynomial_product(removed_n, q)],
    )
    return numerator, polynomial_product(q, removed_q)


@lru_cache(maxsize=1)
def tune_counts(limit: int) -> dict[str, list[int]]:
    """Count completions at each stage, all by rational series recurrences.

    D=N/Q counts gaps, M/R counts sounding durations >=1/24 beat.
    P=(2*FREE_STEPS+1)+2*z**STEP_COST/(1-z**STEP_COST).
    G=1+z**REST_COST*D.
    H=1/(1-z**ATTACK_COST*M/R*P*G) counts possibly empty note suffixes.
    The three completion series are H, M/R*H and G*M/R*H.
    """
    n, q = duration_function()
    m, r = note_duration_function()
    pitch_n = polynomial_sum([2 * FREE_STEPS + 1], power(STEP_COST, 1 - 2 * FREE_STEPS))
    pitch_q = polynomial_sum([1], power(STEP_COST, -1))
    gap_n = polynomial_sum(q, polynomial_product(power(REST_COST), n))
    suffix_n = polynomial_product(r, q, pitch_q)
    denominator = polynomial_sum(
        suffix_n,
        polynomial_product(power(ATTACK_COST, -1), m, pitch_n, gap_n),
    )
    tables = {
        "duration": coefficients(n, q, limit),
        "note_duration": coefficients(m, r, limit),
        "suffix": coefficients(suffix_n, denominator, limit),
        "after_gap": coefficients(
            polynomial_product(m, q, pitch_q), denominator, limit
        ),
        "after_step": coefficients(
            polynomial_product(m, pitch_q, gap_n), denominator, limit
        ),
    }
    # Strictly preceding layers: z*T/(1-z) and z*D/(1-z).
    cumulative_q = [1, -1]
    tables["starts"] = coefficients(
        polynomial_product(power(ATTACK_COST + 1), m, q, pitch_q),
        polynomial_product(denominator, cumulative_q),
        limit + 1,
    )
    tables["duration_starts"] = coefficients(
        polynomial_product(power(1), n),
        polynomial_product(q, cumulative_q),
        limit + 1,
    )
    tables["note_duration_starts"] = coefficients(
        polynomial_product(power(1), m),
        polynomial_product(r, cumulative_q),
        limit + 1,
    )
    return tables


# Enumeration constants, editable together before release, never runtime settings.
ATTACK_COST = 1
STEP_COST = 1
FREE_STEPS = 2
REST_COST = 1
NUMERATOR_COST = 4
BINARY_COST = 1
THIRD_COST = 3

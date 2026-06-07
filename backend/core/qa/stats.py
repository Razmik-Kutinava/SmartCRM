"""Dr. QA — статистические хелперы."""
import math


def norm_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def z_test_proportions(p1: float, p2: float, n1: int, n2: int) -> dict:
    """Two-proportion z-test for accuracy metrics (as proportions 0-1)."""
    if n1 < 2 or n2 < 2:
        return {"error": "insufficient_data", "min_n": 30}
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return {"error": "zero_variance"}
    z = (p2 - p1) / se
    p_value = 2 * (1 - norm_cdf(abs(z)))
    lift_pct = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
    ci_half = 1.96 * se
    return {
        "z": round(z, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "lift_pct": round(lift_pct, 2),
        "ci_95": [round(p2 - p1 - ci_half, 4), round(p2 - p1 + ci_half, 4)],
    }


def min_sample_size(baseline: float, mde: float = 0.05, alpha: float = 0.05, power: float = 0.8) -> int:
    z_alpha = 1.96
    z_beta = 0.842
    p2 = baseline * (1 + mde)
    p_pool = (baseline + p2) / 2
    n = ((z_alpha + z_beta) ** 2 * 2 * p_pool * (1 - p_pool)) / ((p2 - baseline) ** 2)
    return math.ceil(n)

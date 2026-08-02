"""Probabilities — calibration, odds conversion, implied probability, expected value."""

import math
import numpy as np


def calibrate_probabilities(
    raw_probs: np.ndarray,
    actual_outcomes: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """Calibrate raw predictions against actual outcomes.

    Uses Platt scaling / isotonic-like binning.
    Returns: calibrated probabilities, calibration curve data.
    """
    bins = np.linspace(0, 1, n_bins + 1)
    calibrated = np.zeros_like(raw_probs)
    bin_centers = []
    bin_actuals = []

    for i in range(n_bins):
        mask = (raw_probs >= bins[i]) & (raw_probs < bins[i + 1])
        if mask.sum() > 0:
            actual_rate = actual_outcomes[mask].mean()
            calibrated[mask] = actual_rate
            bin_centers.append((bins[i] + bins[i + 1]) / 2)
            bin_actuals.append(actual_rate)
        else:
            calibrated[mask] = (bins[i] + bins[i + 1]) / 2

    # Brier score
    brier = float(np.mean((raw_probs - actual_outcomes) ** 2))

    # Log loss
    eps = 1e-10
    log_loss = float(-np.mean(
        actual_outcomes * np.log(raw_probs + eps) +
        (1 - actual_outcomes) * np.log(1 - raw_probs + eps)
    ))

    return {
        "brier_score": round(brier, 4),
        "log_loss": round(log_loss, 4),
        "calibration_curve": {
            "bin_centers": [round(c, 3) for c in bin_centers],
            "actual_rates": [round(a, 3) for a in bin_actuals],
        },
        "calibration_quality": _calibration_label(brier),
    }


def _calibration_label(brier: float) -> str:
    if brier < 0.15: return "Excellent"
    if brier < 0.20: return "Good"
    if brier < 0.25: return "Fair"
    return "Poor"


def probability_to_odds(prob: float, bookmaker_margin: float = 0.05) -> dict:
    """Convert win probability to betting odds (American, Decimal, Fractional)."""
    fair_prob = prob
    implied = fair_prob - bookmaker_margin / 2

    # American odds
    if implied >= 0.5:
        american = round(-100 * implied / (1 - implied))
    else:
        american = round(100 * (1 - implied) / implied)

    # Decimal odds
    decimal = round(1 / implied, 2) if implied > 0 else float("inf")

    # Fractional approximation
    if implied > 0:
        raw = 1 / implied - 1
        frac = _to_fraction(raw)

    return {
        "probability": round(prob, 3),
        "fair_probability": round(fair_prob - bookmaker_margin / 2, 3),
        "american": f"{'+' if american > 0 else ''}{american}",
        "decimal": decimal,
        "fractional": frac,
    }


def _to_fraction(x: float, max_denom: int = 20) -> str:
    """Convert decimal to nearest simple fraction."""
    best_num, best_den = 1, 1
    best_err = float("inf")
    for d in range(1, max_denom + 1):
        n = round(x * d)
        err = abs(x - n / d)
        if err < best_err:
            best_err, best_num, best_den = err, n, d
    return f"{best_num}/{best_den}"


def implied_probability(odds_american: int) -> float:
    """Convert bookmaker American odds to implied probability."""
    if odds_american > 0:
        return 100 / (odds_american + 100)
    return abs(odds_american) / (abs(odds_american) + 100)


def expected_value(model_prob: float, bookmaker_odds: int) -> dict:
    """Calculate expected value vs bookmaker odds.

    Positive EV = value bet.
    """
    imp_prob = implied_probability(bookmaker_odds)
    ev = model_prob - imp_prob

    if odds_american(bookmaker_odds, 0) != probability_to_odds(imp_prob, 0):
        pass

    return {
        "model_probability": round(model_prob, 3),
        "implied_probability": round(imp_prob, 3),
        "expected_value": round(ev, 4),
        "is_value_bet": ev > 0.03,
        "value_percentage": round(ev * 100, 1),
    }


def odds_american(american: int, margin: float = 0.0) -> str:
    return f"{'+' if american > 0 else ''}{american}"

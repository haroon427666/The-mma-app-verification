"""Model Serving — predict single fights or entire cards."""

import numpy as np
from typing import Any, Optional

from prediction.models.fight_predictor import FightPredictor
from prediction.models.finish_predictor import FinishPredictor
from prediction.models.round_predictor import RoundPredictor
from prediction.models.method_predictor import MethodPredictor
from prediction.models.confidence import ConfidenceScorer
from prediction.simulations.monte_carlo import MonteCarloSimulator
from prediction.explainability.prediction_report import generate_report


def predict_fight(
    fighter_a: dict,
    fighter_b: dict,
    predictor: Optional[FightPredictor] = None,
    run_monte_carlo: bool = True,
) -> dict:
    """Full fight prediction: winner, finish, round, method, confidence, Monte Carlo."""
    if predictor is None:
        predictor = FightPredictor()

    # Winner
    winner = predictor.predict_from_fighters(fighter_a, fighter_b)

    # Finish
    fp = FinishPredictor()
    finish = fp.predict_from_fighters(fighter_a, fighter_b)

    # Round
    is_title = fighter_a.get("is_title_fight", False) or fighter_b.get("is_title_fight", False)
    rp = RoundPredictor(is_title_fight=is_title)
    rounds = rp.predict_from_fighters(fighter_a, fighter_b)

    # Method
    mp = MethodPredictor()
    methods = mp.predict(fighter_a if winner["prob_a"] > 0.5 else fighter_b)

    # Monte Carlo
    mc = None
    if run_monte_carlo:
        sim = MonteCarloSimulator(n_simulations=10_000)
        mc = sim.simulate(
            prob_a=winner["prob_a"],
            elo_a=fighter_a.get("elo_rating", 1500),
            elo_b=fighter_b.get("elo_rating", 1500),
            finish_rate_a=fighter_a.get("finish_rate", 0.5),
            finish_rate_b=fighter_b.get("finish_rate", 0.5),
        )

    prediction = {
        **winner,
        "finish": finish,
        "rounds": rounds,
        "methods": methods,
        "monte_carlo": mc,
    }

    return generate_report(prediction)


def predict_card(
    fights: list[dict],
    fighter_lookup: dict[str, dict],
    predictor: Optional[FightPredictor] = None,
) -> list[dict]:
    """Predict every fight on a card. Returns ordered predictions."""
    predictions = []
    for fight in fights:
        a = fighter_lookup.get(fight.get("fighter_a_id", ""), {})
        b = fighter_lookup.get(fight.get("fighter_b_id", ""), {})
        if a and b:
            pred = predict_fight(a, b, predictor, run_monte_carlo=False)
            pred["fight_order"] = fight.get("order", 0)
            pred["card_segment"] = fight.get("card_segment", "")
            pred["is_main_event"] = fight.get("is_main_event", False)
            predictions.append(pred)

    predictions.sort(key=lambda p: p.get("fight_order", 0))
    return predictions

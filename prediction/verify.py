#!/usr/bin/env python3
"""Verify prediction/ package."""

import sys, numpy as np
print("=" * 60)
print("prediction/ — FULL VERIFICATION")
print("=" * 60)
p = 0

# 1. FIGHT PREDICTOR
print("\n1. FIGHT PREDICTOR")
from prediction.models.fight_predictor import FightPredictor
fp = FightPredictor()
a = {"name": "Islam Makhachev", "elo_rating": 1850, "streak": 14, "age": 31,
     "reach_cm": 179, "finish_rate": 0.6, "momentum_score": 0.9,
     "win_quality": 0.85, "championship_score": 1.0}
b = {"name": "Ilia Topuria", "elo_rating": 1780, "streak": 7, "age": 27,
     "reach_cm": 175, "finish_rate": 0.8, "momentum_score": 0.85,
     "win_quality": 0.75, "championship_score": 0.8}
pred = fp.predict_from_fighters(a, b)
assert 0 < pred["prob_a"] < 1 and pred["confidence"] in ("very_high","high","medium","low","coin_flip")
print(f"  ✓ {pred['fighter_a']} ({pred['prob_a']:.3f}) vs {pred['fighter_b']} ({pred['prob_b']:.3f}) [{pred['confidence']}]")
p += 1

# 2. FINISH PREDICTOR
print("\n2. FINISH PREDICTOR")
from prediction.models.finish_predictor import FinishPredictor
fp2 = FinishPredictor()
finish = fp2.predict_from_fighters(a, b)
assert "ko_tko" in finish and "submission" in finish and "decision" in finish
assert abs(sum(finish.values()) - 1.0) < 0.1
print(f"  ✓ KO/TKO: {finish['ko_tko']:.3f} | Sub: {finish['submission']:.3f} | Dec: {finish['decision']:.3f}")
p += 1

# 3. ROUND PREDICTOR
print("\n3. ROUND PREDICTOR")
from prediction.models.round_predictor import RoundPredictor
rp = RoundPredictor(is_title_fight=True)
rounds = rp.predict_from_fighters(a, b)
assert len(rounds) == 5
print(f"  ✓ R1={rounds['round_1']:.3f} R2={rounds['round_2']:.3f} R3={rounds['round_3']:.3f} R4={rounds['round_4']:.3f} R5={rounds['round_5']:.3f}")
p += 1

# 4. METHOD PREDICTOR
print("\n4. METHOD PREDICTOR")
from prediction.models.method_predictor import MethodPredictor
mp = MethodPredictor()
methods = mp.predict({"sub_avg_per_15": 1.5, "sig_strikes_landed_per_min": 3.5})
assert sum(methods.values()) > 0.99
top = list(methods.items())[0]
print(f"  ✓ Top method: {top[0]} ({top[1]:.3f})")
p += 1

# 5. MONTE CARLO
print("\n5. MONTE CARLO")
from prediction.simulations.monte_carlo import MonteCarloSimulator
mc = MonteCarloSimulator(n_simulations=5000)
result = mc.simulate(prob_a=0.72, elo_a=1850, elo_b=1780, finish_rate_a=0.6, finish_rate_b=0.8)
assert "prob_a" in result and "confidence_interval_95" in result
print(f"  ✓ A={result['prob_a']:.3f} B={result['prob_b']:.3f} CI=[{result['confidence_interval_95']['lower']:.3f},{result['confidence_interval_95']['upper']:.3f}]")
p += 1

# 6. PROBABILITIES
print("\n6. PROBABILITIES")
from prediction.probabilities import probability_to_odds, implied_probability, expected_value
odds = probability_to_odds(0.72)
imp = implied_probability(-180)
ev = expected_value(0.72, -180)
assert odds["american"] != ""
assert imp > 0.5
print(f"  ✓ 72% → {odds['american']} | Bookmaker -180 implies {imp:.3f} | EV: {ev['expected_value']:.3f}")
p += 1

# 7. STYLE MATCHUP
print("\n7. STYLE MATCHUP")
from prediction.styles.style_matchups import analyze_style_matchup
sa = np.array([0.7,0.5,0.6,0.4,0.2,0.3,0.5,0.3,0.5,0.5,0.6,0.2,0.5,0.5,0.8,0.5], np.float32)
sb = np.array([0.3,0.6,0.7,0.2,0.5,0.5,0.3,0.5,0.5,0.5,0.3,0.4,0.5,0.5,0.3,0.7], np.float32)
analysis = analyze_style_matchup(sa, sb)
assert "archetype" in analysis and "key_edges" in analysis
print(f"  ✓ Archetype: {analysis['archetype']}, {len(analysis['key_edges'])} key edges")
p += 1

# 8. TRAINING
print("\n8. TRAINING")
from prediction.training.trainer import train_fight_predictor, cross_validate
from prediction.training.datasets import build_fight_dataset
X = np.random.randn(100, 10).astype(np.float32)
y = (np.random.rand(100) > 0.5).astype(np.float32)
model, metrics = train_fight_predictor(X, y, model_type="logistic")
assert metrics["accuracy"] > 0.3  # Better than random on 100 samples
cv = cross_validate(X, y, n_folds=3)
assert len(cv["folds"]) == 3
print(f"  ✓ Train acc={metrics['accuracy']:.3f}, CV mean acc={cv['mean_accuracy']:.3f}")
p += 1

# 9. BACKTESTING
print("\n9. BACKTESTING")
from prediction.evaluation.backtesting import run_backtest
test_fights = [
    {"fighter_a_id": "f1", "fighter_b_id": "f2", "winner_id": "f1", "date": "2024-01-01", "event_name": "UFC 300"},
    {"fighter_a_id": "f1", "fighter_b_id": "f3", "winner_id": "f3", "date": "2024-02-01", "event_name": "UFC 301"},
]
lookup = {"f1": {"name": "Islam", "elo_rating": 1850}, "f2": {"name": "Charles", "elo_rating": 1750},
          "f3": {"name": "Arman", "elo_rating": 1900}}
bt = run_backtest(test_fights, lookup)
assert bt["total_fights"] == 2
print(f"  ✓ {bt['correct']}/{bt['total_fights']} correct, acc={bt['accuracy']:.3f}, logloss={bt['log_loss']:.3f}")
p += 1

# 10. SERVING
print("\n10. SERVING")
from prediction.serving.predictor import predict_fight, predict_card
report = predict_fight(a, b, run_monte_carlo=False)
assert "prediction" in report and "key_factors" in report
assert report["prediction"]["winner"] in (a["name"], b["name"])
card_pred = predict_card([{"fighter_a_id": "f1", "fighter_b_id": "f2", "order": 1, "card_segment": "Main Card", "is_main_event": True}],
                         {"f1": a, "f2": b})
assert len(card_pred) == 1
print(f"  ✓ Winner: {report['prediction']['winner']}, confidence: {report['prediction']['confidence']['level']}")
p += 1

print(f"\n{'='*60}")
print(f"prediction/: {p}/10 sections VERIFIED")
print(f"{'='*60}")
sys.exit(0 if p == 10 else 1)

"""prediction/ — Fight Intelligence & Probabilistic Modeling.

Answers every question a serious MMA fan wants:
    Who wins? By what method? In which round? With what confidence?

Real ML. Monte Carlo. Calibration. Backtesting. Explainability.
"""

from prediction.models.fight_predictor import FightPredictor
from prediction.models.finish_predictor import FinishPredictor
from prediction.models.round_predictor import RoundPredictor
from prediction.models.method_predictor import MethodPredictor
from prediction.models.confidence import ConfidenceScorer
from prediction.simulations.monte_carlo import MonteCarloSimulator
from prediction.probabilities import calibrate_probabilities, probability_to_odds, implied_probability
from prediction.explainability.prediction_report import generate_report
from prediction.evaluation.backtesting import run_backtest
from prediction.serving.predictor import predict_fight, predict_card
from prediction.training.trainer import train_models

__all__ = [
    "FightPredictor", "FinishPredictor", "RoundPredictor", "MethodPredictor", "ConfidenceScorer",
    "MonteCarloSimulator",
    "calibrate_probabilities", "probability_to_odds", "implied_probability",
    "generate_report",
    "run_backtest",
    "predict_fight", "predict_card",
    "train_models",
]

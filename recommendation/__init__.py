"""recommendation/ — Personalization & Recommendation Platform.

Depends on: backend (data) + intelligence (features/embeddings).
Never calls ESPN or providers directly.
"""

from recommendation.engine.recommendation_engine import RecommendationEngine, RecommendationResult
from recommendation.user_profile.builder import UserProfileBuilder, UserProfile
from recommendation.user_profile.embeddings import embed_profile, find_similar_users
from recommendation.scoring.final_score import compute_final_score
from recommendation.retrieval.candidates import FighterRetrieval, EventRetrieval, FightRetrieval
from recommendation.explainability.reasons import explain_recommendation
from recommendation.trending.fighters import TrendingEngine, FighterTrending
from recommendation.search.hybrid import HybridSearch, SemanticSearch, AutocompleteEngine
from recommendation.experiments.ab_testing import Experiment, ExperimentTracker
from recommendation.evaluation.metrics import precision_at_k, recall_at_k, ndcg_at_k, diversity_score
from recommendation.notifications import WatchlistChecker, DigestBuilder, NotificationTrigger
from recommendation.benchmarks.speed import bench_profiling

__all__ = [
    "RecommendationEngine", "RecommendationResult",
    "UserProfileBuilder", "UserProfile", "embed_profile", "find_similar_users",
    "compute_final_score",
    "FighterRetrieval", "EventRetrieval", "FightRetrieval",
    "explain_recommendation",
    "TrendingEngine", "FighterTrending",
    "HybridSearch", "SemanticSearch", "AutocompleteEngine",
    "Experiment", "ExperimentTracker",
    "precision_at_k", "recall_at_k", "ndcg_at_k", "diversity_score",
    "WatchlistChecker", "DigestBuilder", "NotificationTrigger",
    "bench_profiling",
]

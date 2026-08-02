"""Recommendation config — scoring weights, pipeline parameters."""

# ── Pipeline ──────────────────────────────────────────────────────────
DEFAULT_RECOMMENDATIONS = 20
CANDIDATE_POOL_SIZE = 500
MIN_CONFIDENCE = 0.1

# ── Scoring Weights (sum = 1.0) ───────────────────────────────────────
PERSONALIZATION_WEIGHT = 0.30
SIMILARITY_WEIGHT = 0.15
TRENDING_WEIGHT = 0.10
POPULARITY_WEIGHT = 0.08
FRESHNESS_WEIGHT = 0.12
QUALITY_WEIGHT = 0.10
DIVERSITY_PENALTY = 0.05
NOVELTY_BONUS = 0.05
WATCHLIST_BOOST = 0.05

# ── Diversity ─────────────────────────────────────────────────────────
DIVERSITY_WINDOW = 3
DIVERSITY_SIMILARITY_THRESHOLD = 0.85

# ── Trending ──────────────────────────────────────────────────────────
TRENDING_WINDOW_DAYS = 7
TRENDING_MIN_VIEWS = 10

# ── Freshness ─────────────────────────────────────────────────────────
FRESHNESS_HALF_LIFE_DAYS = 30
MAX_AGE_DAYS = 365

# ── User Profile ──────────────────────────────────────────────────────
PROFILE_DECAY_RATE = 0.01
INTEREST_WEIGHT_THRESHOLD = 0.05
MAX_PROFILE_WEIGHT_CLASSES = 5

# ── Cache ─────────────────────────────────────────────────────────────
RECOMMENDATION_CACHE_TTL = 300
TRENDING_CACHE_TTL = 600

# ── Search ────────────────────────────────────────────────────────────
SEARCH_TOP_K = 20
AUTOCOMPLETE_LIMIT = 8
SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.4

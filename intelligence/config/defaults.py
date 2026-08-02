"""Configuration — no more magic numbers.

Every weight, threshold, and constant lives here.
Change one file to retune the entire intelligence pipeline.
"""

# ── Embedding Dimensions ──────────────────────────────────────────────────
FIGHTER_DIM = 64
MATCHUP_DIM = 32
STYLE_DIM = 16
EVENT_DIM = 48
PROMOTION_DIM = 24
WEIGHT_CLASS_DIM = 8

# ── Elo / Glicko ──────────────────────────────────────────────────────────
INITIAL_ELO = 1500.0
INITIAL_GLICKO_RATING = 1500.0
INITIAL_GLICKO_RD = 350.0
MIN_GLICKO_RD = 60.0
BASE_K_FACTOR = 32
TITLE_K_FACTOR = 48
PROSPECT_K_FACTOR = 64
FINISH_BONUS_MULTIPLIER = 1.25
PROSPECT_THRESHOLD_FIGHTS = 5
ELO_SCALE = 400.0
ELO_MIN = 1200.0
ELO_MAX = 2000.0

# ── Age Curve ─────────────────────────────────────────────────────────────
PEAK_AGE_MIN = 29
PEAK_AGE_MAX = 32
DECLINE_START_AGE = 34
SHARP_DECLINE_AGE = 37
ROOKIE_AGE = 18
MAX_AGE = 45

# ── Composite Ranking Weights ─────────────────────────────────────────────
COMPOSITE_ELO_WEIGHT = 0.30
COMPOSITE_WIN_QUALITY_WEIGHT = 0.20
COMPOSITE_OPP_QUALITY_WEIGHT = 0.15
COMPOSITE_MOMENTUM_WEIGHT = 0.15
COMPOSITE_CHAMPIONSHIP_WEIGHT = 0.10
COMPOSITE_FINISH_RATE_WEIGHT = 0.10

# ── Momentum ──────────────────────────────────────────────────────────────
MOMENTUM_WR_WEIGHT = 0.40
MOMENTUM_STREAK_WEIGHT = 0.40
MOMENTUM_OPP_QUALITY_WEIGHT = 0.20
MOMENTUM_RECENT_WINDOW = 5

# ── Normalization ─────────────────────────────────────────────────────────
STRIKES_PER_MIN_MAX = 8.0
TAKEDOWNS_PER_15_MAX = 6.0
SUBMISSIONS_PER_15_MAX = 3.0
KNOCKDOWNS_PER_FIGHT_MAX = 2.0
HEIGHT_MIN = 155.0
HEIGHT_RANGE = 50.0
REACH_RANGE = 50.0
WEIGHT_MAX = 120.0
EXPERIENCE_MAX_FIGHTS = 50.0
TITLE_WINS_MAX = 10.0
RANKING_TOTAL = 15

# ── Cache ─────────────────────────────────────────────────────────────────
EMBEDDING_CACHE_TTL = 3600
FEATURE_CACHE_TTL = 1800
RANKING_CACHE_TTL = 600

# ── Similarity ────────────────────────────────────────────────────────────
SIMILARITY_TOP_K = 10
STYLE_CLUSTER_COUNT = 8

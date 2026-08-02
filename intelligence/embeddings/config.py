"""Embedding dimensions and normalization config.

All vectors in the intelligence package use these dimensions.
Consistent dimensionality enables cross-module similarity search.
"""

from dataclasses import dataclass

FIGHTER_EMBEDDING_DIM = 64
MATCHUP_EMBEDDING_DIM = 32
STYLE_VECTOR_DIM = 16
EVENT_EMBEDDING_DIM = 48
PROMOTION_EMBEDDING_DIM = 24
WEIGHT_CLASS_EMBEDDING_DIM = 8


@dataclass(frozen=True)
class EmbeddingConfig:
    fighter_dim: int = FIGHTER_EMBEDDING_DIM
    matchup_dim: int = MATCHUP_EMBEDDING_DIM
    style_dim: int = STYLE_VECTOR_DIM
    event_dim: int = EVENT_EMBEDDING_DIM
    promotion_dim: int = PROMOTION_EMBEDDING_DIM
    weight_class_dim: int = WEIGHT_CLASS_EMBEDDING_DIM

    normalize: bool = True


DEFAULT_CONFIG = EmbeddingConfig()

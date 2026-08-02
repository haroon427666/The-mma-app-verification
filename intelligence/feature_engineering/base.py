"""Feature Engineering — extract numeric features from raw fighter data.

Each module produces a numpy array. Pipelines are composable.
No external AI — pure math and statistics.
"""

import numpy as np


class FeaturePipeline:
    """Base class for composable feature extraction pipelines."""

    @property
    def dim(self) -> int:
        raise NotImplementedError

    def extract(self, fighter: dict) -> np.ndarray:
        raise NotImplementedError

    def extract_batch(self, fighters: list[dict]) -> np.ndarray:
        return np.array([self.extract(f) for f in fighters], dtype=np.float32)

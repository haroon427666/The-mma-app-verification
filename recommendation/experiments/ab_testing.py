"""A/B Testing & Experiments — variant assignment, metric tracking."""

import hashlib
import random
from typing import Any


class Experiment:
    def __init__(self, name: str, variants: list[str], weights: list[float] | None = None):
        self.name = name
        self.variants = variants
        self.weights = weights or [1.0 / len(variants)] * len(variants)
        assert len(self.variants) == len(self.weights)
        assert abs(sum(self.weights) - 1.0) < 0.01

    def assign(self, user_id: str) -> str:
        h = hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest()
        bucket = int(h[:8], 16) / 0xFFFFFFFF
        cumulative = 0.0
        for variant, weight in zip(self.variants, self.weights):
            cumulative += weight
            if bucket <= cumulative:
                return variant
        return self.variants[-1]


class ExperimentTracker:
    def __init__(self):
        self._experiments: dict[str, Experiment] = {}
        self._metrics: dict[str, dict[str, list[float]]] = {}

    def register(self, exp: Experiment) -> None:
        self._experiments[exp.name] = exp
        self._metrics[exp.name] = {v: [] for v in exp.variants}

    def get_variant(self, exp_name: str, user_id: str) -> str:
        exp = self._experiments.get(exp_name)
        if exp is None:
            return "control"
        return exp.assign(user_id)

    def record_metric(self, exp_name: str, variant: str, value: float) -> None:
        if exp_name in self._metrics:
            self._metrics[exp_name].setdefault(variant, []).append(value)

    def results(self, exp_name: str) -> dict:
        import statistics
        variants = self._metrics.get(exp_name, {})
        return {
            variant: {
                "count": len(values),
                "mean": statistics.mean(values) if values else 0,
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            }
            for variant, values in variants.items()
        }

"""Monte Carlo Simulator — runs N simulations of a fight.

Each simulation: sample from probability distributions for each factor.
Aggregate results to produce robust win/loss estimates.
"""

import numpy as np
from typing import Optional


class MonteCarloSimulator:
    """Run N fight simulations with variance around point estimates."""

    def __init__(self, n_simulations: int = 100_000):
        self.n = n_simulations
        self.rng = np.random.default_rng()

    def simulate(
        self,
        prob_a: float,
        elo_a: float = 1500,
        elo_b: float = 1500,
        elo_std: float = 150,
        finish_rate_a: float = 0.5,
        finish_rate_b: float = 0.5,
        momentum_a: float = 0.5,
        momentum_b: float = 0.5,
    ) -> dict:
        """Run Monte Carlo simulation.

        Models uncertainty around: Elo ratings, finish rates, momentum.
        Each simulation samples slightly different values.
        """
        # Sample Elo ratings around point estimates
        elos_a = self.rng.normal(elo_a, elo_std, self.n)
        elos_b = self.rng.normal(elo_b, elo_std, self.n)

        # Sample finish rates (beta distribution for [0,1])
        fr_a = self.rng.beta(
            max(finish_rate_a * 20, 1), max((1 - finish_rate_a) * 20, 1), self.n,
        )
        fr_b = self.rng.beta(
            max(finish_rate_b * 20, 1), max((1 - finish_rate_b) * 20, 1), self.n,
        )

        # Sample momentum
        mom_a = self.rng.normal(momentum_a, 0.15, self.n)
        mom_b = self.rng.normal(momentum_b, 0.15, self.n)

        # Compute win probability per simulation
        elo_diff = elos_a - elos_b
        streak_factor = 0.2 * (mom_a - mom_b)
        raw = elo_diff / 400.0 + streak_factor
        sim_probs = 1.0 / (1.0 + np.exp(-raw * 2.5))

        wins_a = int(np.sum(sim_probs > 0.5))

        # Round prediction sampling
        comb_fr = 0.6 * np.maximum(fr_a, fr_b) + 0.4 * np.minimum(fr_a, fr_b)
        rounds = self.rng.choice([1, 2, 3, 4, 5], size=self.n, p=[0.12, 0.22, 0.29, 0.20, 0.17])

        return {
            "simulations": self.n,
            "fighter_a_wins": wins_a,
            "fighter_b_wins": self.n - wins_a,
            "prob_a": round(wins_a / self.n, 4),
            "prob_b": round((self.n - wins_a) / self.n, 4),
            "std_dev": round(float(np.std(sim_probs)), 4),
            "confidence_interval_95": {
                "lower": round(float(np.percentile(sim_probs, 2.5)), 4),
                "upper": round(float(np.percentile(sim_probs, 97.5)), 4),
            },
            "most_likely_round": int(np.bincount(rounds).argmax()),
            "round_distribution": {
                f"round_{i+1}": round(float(np.sum(rounds == i+1) / self.n * 100), 1)
                for i in range(5)
            },
        }

    def simulate_tournament(self, fighters: list[dict], bracket: list[list[int]]) -> dict:
        """Run a tournament simulation. Returns winner probabilities per fighter."""
        n_fighters = len(fighters)
        win_counts = np.zeros(n_fighters, dtype=int)

        for _ in range(min(self.n // 10, 5000)):
            # Simple bracket simulation
            remaining = list(range(n_fighters))
            round_num = 0
            while len(remaining) > 1 and round_num < len(bracket):
                next_round = []
                for i in range(0, len(remaining), 2):
                    if i + 1 >= len(remaining):
                        next_round.append(remaining[i])
                        continue
                    a, b = remaining[i], remaining[i + 1]
                    p_a = self._quick_prob(fighters[a], fighters[b])
                    winner = a if self.rng.random() < p_a else b
                    next_round.append(winner)
                remaining = next_round
                round_num += 1
            if remaining:
                win_counts[remaining[0]] += 1

        return {
            fighter.get("name", f"fighter_{i}"): round(win_counts[i] / max(win_counts.sum(), 1), 4)
            for i, fighter in enumerate(fighters)
        }

    def _quick_prob(self, a: dict, b: dict) -> float:
        ed = a.get("elo_rating", 1500) - b.get("elo_rating", 1500)
        return 1.0 / (1.0 + np.exp(-ed / 250.0))

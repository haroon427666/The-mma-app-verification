# Mathematical Reference

## Elo Rating

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
R_A' = R_A + K × (S_A - E_A) × finish_multiplier
```

Where:
- K = 32 (base), 48 (title fight), 64 (prospect, <5 fights)
- finish_multiplier = 1.25 for KO/sub wins, 1.0 for decisions
- R_A = rating before fight, R_A' = rating after

## Glicko Rating

```
g(RD) = 1 / sqrt(1 + 3q²RD²/π²)    where q = ln(10)/400
E = 1 / (1 + 10^(-g(RD_opp)×(R - R_opp)/400))
d² = 1 / (q² × g(RD_opp)² × E × (1-E))
R' = R + (q / (1/RD² + 1/d²)) × g(RD_opp) × (S - E)
RD' = max(60, sqrt(1 / (1/RD² + 1/d²)))
```

RD increases with inactivity: `RD_new = sqrt(RD² + 0.005 × days_inactive)`

## Composite Ranking Score (0-1000)

```
score = 0.30 × elo_norm    + 0.20 × win_quality
      + 0.15 × opp_quality + 0.15 × momentum
      + 0.10 × championship + 0.10 × finish_rate

elo_norm = (elo - 1200) / 800    # Maps [1200, 2000] → [0, 1]
```

## Momentum Score

```
momentum = 0.40 × weighted_win_rate + 0.40 × streak_score + 0.20 × opp_quality
streak_score = clamp((streak + 5) / 10, 0, 1)
weighted_win_rate = Σ(recent_results[i] × exp(i/len), i=0..n-1) / Σ(exp(i/len))
```

## Age Performance Curve

```
Peak:      age 29-32 → 1.00
Rising:    age 18-28 → linear 0.00 → 1.00
Early decline: age 33-34 → 1.00 → 0.90
Moderate decline: age 35-37 → 0.90 → 0.45
Sharp decline: age 38+ → 0.45 → 0.10
```

## Win Probability (Heuristic)

```
raw_score = Σ(matchup_vector[i] × weight[i]), i=0..31
probability = 1 / (1 + e^(-raw_score × 3))     # Scaled sigmoid
```

## Cosine Similarity

```
sim(A, B) = (A · B) / (|A| × |B|)
```

All embeddings are pre-normalized to unit length, so `sim = A · B`.

# Intelligence Platform — Algorithms Overview

## Rating Systems

### Elo
- Standard Elo with MMA-specific K-factors
- Prospect K=64 (fewer than 5 fights)
- Title fight K=48
- Finish bonus: 1.25× rating transfer
- Initial rating: 1500

### Glicko
- Elo + rating deviation (uncertainty)
- High RD for new/inactive fighters → faster rating moves
- Minimum RD: 60
- Inactivity decay: 0.005/day

### Composite
- Weighted combination of Elo, win quality, momentum, championship
- Used for ranking display in the frontend

## Similarity

### Cosine Similarity
- All embeddings are unit-normalized
- Similarity = dot product of normalized vectors
- Search: O(N) brute force, O(N log K) with heap

### K-Means Clustering
- On 16-dim style vectors
- Default: 8 clusters
- Labels: Striker, Grappler, Knockout Artist, etc.

## Predictions

### Win Probability
- Linear combination of 32-dim matchup embedding
- Scaled sigmoid output
- Weights tuned for MMA (champion status, momentum, ranking weighted heavily)

### Finish Probability
- Bayesian combination of each fighter's finish rate
- Adjusted by opponent's durability

### Style Analysis
- Classifies matchup archetype
- striker_vs_grappler, grappler_vs_striker, striker_vs_striker, grappler_vs_grappler, mixed

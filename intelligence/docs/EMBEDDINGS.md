# Embeddings Architecture

## Dimensions

| Embedding | Dim | Purpose |
|---|---|---|
| Fighter | 64 | Complete fighter representation |
| Matchup | 32 | Fighter A vs Fighter B pair |
| Style | 16 | Fighting style categorization |
| Event | 48 | Event card strength/quality |
| Promotion | 24 | Promotion prestige |
| Weight Class | 8 | Division strength |

## Fighter Embedding (64-dim)

```
[0:16]   Style vector (from style_vector.py)
[16:24]  Physical attributes (age, height, reach, ape index, weight, experience, age score)
[24:32]  Record stats (win%, loss%, finish rate, streak, title exp, activity, champion)
[32:40]  Ranking & Division (rank percentile, momentum, division strength)
[40:48]  Momentum (momentum score, activity rate, streak normalized)
[48:56]  Career trajectory (age score, experience, trajectory slope)
[56:64]  Quality scores (win quality, opponent quality, composite)
```

All normalized to unit length for cosine similarity.

## Versioning

Embedding version is implicit in the dimension and layout.
When dimensions change, bump the embedding version and rebuild all vectors.
Old vectors stored in artifacts/vectors/v{N}/.

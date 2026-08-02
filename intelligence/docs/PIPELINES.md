# Pipeline Architecture

## Offline Jobs

```
build_features.py     → Feature Store
build_embeddings.py   → Vector Store + artifacts/vectors/
rebuild_rankings.py   → Elo/Glicko recalculated from all fights
```

## Pipeline Flow

```
Raw Fighter Data
       ↓
build_features.py
       ↓
Feature Store (repository)
       ↓
build_embeddings.py
       ↓
Vector Store (embeddings)
       ↓
rebuild_rankings.py
       ↓
Rankings (Elo + Glicko + Composite)
       ↓
Export (artifacts/)
```

## Running Manually

```bash
# From intelligence/ directory
python -m pipeline.build_features
python -m pipeline.build_embeddings
python -m pipeline.rebuild_rankings
```

## Scheduling

These scripts are called by the backend scheduler (Phase 7).
Frequency: features/embeddings/rankings rebuilt daily after ESPN sync.

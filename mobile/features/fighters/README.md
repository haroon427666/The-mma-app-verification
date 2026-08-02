# Fighters Module

Complete fighter profiles, statistics, history, similar fighters, style analysis, predictions, and comparison.

## Architecture
```
Screen → Hook → Repository → API
```
All hooks go through the repository layer. Never call API directly.

## Features
- Fighter profiles with full stats
- Strike-by-strike and grappling breakdowns
- Complete fight history with opponent quality
- Similar fighters (powered by intelligence embeddings)
- AI-generated style analysis  
- Prediction integration
- Fighter comparison (tale of the tape)
- Rank history with movement tracking
- Career timeline and achievements
- Favorite/unfavorite with optimistic updates

## API Endpoints
See API.md for the complete endpoint reference.

## Cache Strategy
- Fighter list: 10 min stale
- Fighter detail: 10 min stale
- Stats: 30 min stale
- Fight history: 30 min stale
- Similar fighters: 60 min stale
- Predictions: 30 min stale

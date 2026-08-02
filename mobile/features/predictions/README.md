# Predictions Module — README + Architecture + API + Testing

## Features
- Fight prediction (win probability, finish/round/method)
- Monte Carlo simulation (100K runs)
- Confidence scoring with calibration
- Key factors with explainability
- Style matchup analysis
- Odds comparison and value bets
- Prediction history and accuracy tracking
- Save/unsave predictions

## Architecture
`Screen → Hook → Repository → API → prediction/ package (Phase 11)`

## API Endpoints
| GET `/v1/predictions/fight/:id` | Full fight prediction |
| GET `/v1/predictions/event/:id` | Event predictions |
| GET `/v1/predictions/dashboard` | Dashboard |
| GET `/v1/predictions/highlights` | Top predictions |
| GET `/v1/predictions/history` | History |
| GET `/v1/predictions/accuracy` | Accuracy stats |
| GET `/v1/predictions/matchup` | Head-to-head |
| POST `/v1/predictions/saved/:id` | Save |
| DELETE `/v1/predictions/saved/:id` | Unsave |
| GET `/v1/predictions/saved` | Saved list |
| POST `/v1/predictions/:id/share` | Share |

## Cache
- Fight predictions: 5 min
- Live predictions: 30s
- History/accuracy: 60 min

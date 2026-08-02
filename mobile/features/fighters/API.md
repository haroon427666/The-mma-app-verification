# Fighters Module — API Reference

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/v1/fighters` | List with filters |
| GET | `/v1/fighters/:id` | Fighter profile |
| GET | `/v1/fighters/search` | Search |
| GET | `/v1/fighters/trending` | Trending |
| GET | `/v1/fighters/champions` | Champions |
| GET | `/v1/fighters/:id/stats` | Full stats |
| GET | `/v1/fighters/:id/fights` | Fight history |
| GET | `/v1/fighters/:id/similar` | Similar fighters |
| GET | `/v1/fighters/:id/style-analysis` | AI style analysis |
| GET | `/v1/fighters/:id/rankings/history` | Rank history |
| GET | `/v1/fighters/:id/timeline` | Career timeline |
| GET | `/v1/fighters/:id/achievements` | Achievements |
| POST | `/v1/favorites/fighters/:id` | Favorite |
| DELETE | `/v1/favorites/fighters/:id` | Unfavorite |
| POST | `/v1/follows/fighters/:id` | Follow |
| DELETE | `/v1/follows/fighters/:id` | Unfollow |
| GET | `/v1/predictions/fighter/:id` | Fighter predictions |
| GET | `/v1/predictions/matchup` | Head-to-head prediction |

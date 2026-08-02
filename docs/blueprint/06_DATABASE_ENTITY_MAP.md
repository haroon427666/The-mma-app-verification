# Part 6 — Database Entity Map

## Entity relationship overview

```
Promotion (organization)
  │
  ├── 1:N ── Event
  │            │
  │            ├── N:1 ── Venue
  │            ├── 1:N ── Broadcast          (deduplicated at event level, not per-bout)
  │            └── 1:N ── Competition (a "Fight")
  │                         │
  │                         ├── N:1 ── WeightClass
  │                         └── 1:N ── Competitor ── N:1 ── Fighter
  │
  └── 1:N ── Ranking ── N:1 ── Fighter
                       └── N:1 ── WeightClass (nullable — pound-for-pound has none)

Fighter
  ├── N:1 ── WeightClass (fighter's own current weight class)
  ├── 1:N ── Competitor (every appearance across every Competition)
  └── 1:N ── Statistic (via Competitor — stats are tied to one appearance)

User (model exists, unpopulated — awaiting auth)
  ├── 1:N ── FighterFollow ── N:1 ── Fighter
  ├── 1:N ── PromotionFollow ── N:1 ── Promotion
  ├── 1:N ── Reminder ── N:1 ── Event
  └── 1:N ── Notification

ExternalId (generic, not yet populated)
  — (entity_type, entity_id) <-> (provider, external_id), any of Fighter/Promotion/Event/Venue

EntityImage (generic, not yet populated)
  — (entity_type, entity_id, image_type) -> ranked list of provider image URLs

SyncRun (operational, not user-facing)
  — one row per background sync job execution; powers Admin's ADMIN-01 only
```

## Entity notes relevant to product decisions

- **A "Fight" in product language is a `Competition` in the schema.**
- **`Competitor` is not a pure join table** — it's where corner (red/blue) and outcome (win/loss/draw/no-contest) live.
- **`Broadcast` belongs to `Event`, not `Competition`.**
- **`Ranking.weight_class_id` is nullable.** Any Rankings/Champions screen must handle a ranking row with no weight class (pound-for-pound categories) as a normal case, not an error.
- **`FighterFollow`/`PromotionFollow` models already exist in the schema** but have zero rows and no API surface yet.
- **`Notification` (the DB row) is not the same thing as a push notification.** It's a durable record of one sent notification.
- **`ExternalId` and `EntityImage` exist specifically so future data-source expansion doesn't require a schema migration for every existing entity.**
- **There is no `SearchIndex` entity as a separate table.** Full-text search is implemented as a generated `search_vector` column directly on `Fighter`, `Promotion`, `Event`, and `Venue`.
- **There is no separate "Champion" table.** Champions (CHAMP-01) is a derived view over `Ranking` rows where `is_champion = true`.

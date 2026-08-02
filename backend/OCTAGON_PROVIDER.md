# Octagon API Provider Profile

**Provider:** Octagon API | **URL:** `https://api.octagon-api.com` | **Auth:** None (open)
**Source:** Open-source (GitHub: victor-lillo/octagon-api, 30 stars, 2 forks, 859 commits)
**Method:** Web scraper — extracts data from ufc.com athlete profiles and rankings pages
**Last verified:** 2026-08-01 (live API calls)

---

## Endpoints

| Method | Endpoint | Returns | Verified |
|---|---|---|---|
| GET | `/fighters` | All fighters (200+), keyed by slug ID | ✅ |
| GET | `/fighter/:id` | Single fighter detail | ✅ |
| GET | `/rankings` | 13 ranking categories (champion + ordered fighters) | ✅ |
| GET | `/division/:id` | Single division detail | Available |

---

## Fighter Schema (confirmed from 100+ real records)

| Field | Type | Example | Coverage | Notes |
|---|---|---|---|---|
| `name` | string | "Islam Makhachev" | 100% | Full name |
| `nickname` | string | "El Matador" | 95% | Sometimes empty string |
| `category` | string | "Lightweight Division" | 100% | Division assignment |
| `wins` | string | "27" | 100% | Need to parse as int |
| `losses` | string | "1" | 100% | Need to parse as int |
| `draws` | string | "0" | 100% | Need to parse as int |
| `status` | string | "Active" | 100% | "Active" or "Retired" |
| `placeOfBirth` | string | "Dagestan Republic, Russia" | 95% | Richer than TSDB |
| `trainsAt` | string | "AKA (American Kickboxing Academy)" | 85% | **UNIQUE** — not in ESPN or TSDB |
| `fightingStyle` | string | "Sambo", "Muay Thai", "Jiu-Jitsu" | 95% | **UNIQUE** — not in ESPN or TSDB |
| `age` | string | "33" | 100% | Need to parse as int |
| `height` | string | "70.00" | 100% | Inches, parse as float |
| `weight` | string | "154.50" | 100% | Pounds, parse as float |
| `reach` | string | "70.50" | 98% | Inches, parse as float |
| `legReach` | string | "40.50" | 98% | **UNIQUE** — inches, parse as float |
| `octagonDebut` | string | "May. 23, 2015" | 100% | **UNIQUE** — debut date |
| `imgUrl` | string | `https://ufc.com/images/.../MAKHACHEV_ISLAM_L_07-17.png` | 100% | **Official UFC full-body render** |

---

## Rankings Schema (13 categories)

```json
{
  "id": "mens-pound-for-pound-top-rank",
  "categoryName": "Men's Pound-for-Pound Top Rank",
  "champion": { "id": "ilia-topuria", "championName": "Ilia Topuria" },
  "fighters": [
    { "id": "ilia-topuria", "name": "Ilia Topuria" },
    { "id": "islam-makhachev", "name": "Islam Makhachev" }
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | Slug-based category ID |
| `categoryName` | string | Human-readable name |
| `champion.id` | string | Fighter slug ID |
| `champion.championName` | string | Fighter name |
| `fighters[].id` | string | Fighter slug ID (ordered by rank) |
| `fighters[].name` | string | Fighter name |

Rankings are ordered — index 0 = #1 contender, index 1 = #2, etc.
Fighter slugs use format: `firstname-lastname` (e.g., "islam-makhachev", "alex-pereira").

---

## Fighter ID Mapping

Octagon uses **slug-based IDs** (e.g., "islam-makhachev"). These map to ESPN numeric IDs via:
1. Slug → name (e.g., "islam-makhachev" → "Islam Makhachev")
2. Name + division → ESPN fighter (match on fullName + weight class)
3. Store mapping in `external_ids` table

This is the cleanest cross-reference because Octagon IDs are human-readable (derived from fighter names).

---

## What Octagon provides that others don't

| Field | ESPN | TSDB | Octagon | Winner |
|---|---|---|---|---|
| **legReach** | ❌ | ❌ | ✅ 98% | **Octagon** |
| **trainsAt (gym)** | ❌ | ❌ (0% for MMA) | ✅ 85% | **Octagon** |
| **fightingStyle** | ❌ | ❌ | ✅ 95% | **Octagon** |
| **octagonDebut** | ❌ (must derive from eventLog) | ❌ | ✅ 100% | **Octagon** |
| **placeOfBirth** | ❌ | ✅ 90% | ✅ 95% | **Octagon** (higher coverage) |
| **imgUrl (fighter image)** | ✅ 30% CDN | ✅ 30% JPEG | ✅ 100% UFC CDN | **Octagon** (official renders) |
| **nickname** | ❌ | ✅ 50% | ✅ 95% | **Octagon** (higher coverage) |

---

## Reliability Assessment

| Factor | Rating | Notes |
|---|---|---|
| **Data accuracy** | ⭐⭐⭐⭐ | Scraped from ufc.com — same source as ESPN internally |
| **Data freshness** | ⭐⭐⭐⭐ | Rankings up-to-date (reflects recent title changes) |
| **API stability** | ⭐⭐⭐ | Open-source, no SLA, depends on UFC website structure |
| **Rate limits** | ⭐⭐⭐⭐⭐ | None observed — 200+ fighters in single response |
| **Uptime** | ⭐⭐⭐⭐ | Cloudflare Workers — fast response, CDN-backed |
| **Maintenance** | ⭐⭐⭐ | Small community project (30 stars) — could be abandoned |
| **Versioning** | ⭐⭐ | No API versioning — breaking changes possible |

**Risk mitigation:** Octagon should be a **best-effort enrichment provider**. If it fails, skip and use ESPN/TSDB fallback. Never block the sync pipeline on Octagon availability.

---

## Recommended Integration

```
Source authority for enriched fighter fields:

  nickname      → Octagon (95% coverage) > TSDB (50%) > ESPN (none)
  placeOfBirth  → Octagon (95%) > TSDB (90%)
  trainsAt      → Octagon (85%) ONLY
  fightingStyle → Octagon (95%) ONLY
  legReach      → Octagon (98%) ONLY
  octagonDebut  → Octagon (100%) ONLY
  imgUrl        → Octagon (100%, UFC renders) > TSDB (30%, JPEG cutouts)
  
  Rankings:     → ESPN (primary) + Octagon (verification)
                 Alert if rankings differ between sources

  All other fields → ESPN (primary, unchanged)
```

**Rankings verification workflow:**
```
ESPN Rankings → sync → Database
                          ↓
Octagon Rankings → fetch → Compare
                          ↓
                    Match? ── Yes → Log confidence
                          ── No  → Alert + flag for review
```

**Sync schedule:** Weekly (fighter enrichments don't change frequently).
**Cron:** `0 5 * * 0` (Sunday 5 AM, after ESPN weekly sync).

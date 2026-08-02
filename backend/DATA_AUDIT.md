# Phase 4.1 — ESPN & TheSportsDB Data Audit v2

**Date:** 2026-08-01 | **Method:** Live API calls + field coverage analysis | **Sampled:** 10 TSDB players, 1,809 ESPN fighters, 1 event, 1 ranking category, 48 leagues

---

## 1. Field-by-Field Inventory

### 1.1 Promotion (23 fields)

| # | Field | ESPN | TSDB | Source | Reason |
|---|---|---|---|---|---|
| 1 | id | ✅ 3321 | ✅ 4443 | ESPN | Canonical ID across all endpoints |
| 2 | name | ✅ "Ultimate Fighting Championship" | ✅ "UFC" | ESPN | Full official name |
| 3 | display_name | ✅ "UFC" | ✅ alt | ESPN | Both full + display variants |
| 4 | abbreviation | ✅ "UFC" | ❌ | ESPN | Only source |
| 5 | short_name | ✅ "UFC" | ❌ | ESPN | Only source |
| 6 | slug | ✅ "ufc" | ❌ | ESPN | API lookups |
| 7 | country | ❌ | ✅ "Worldwide" | **TSDB** | Only source |
| 8 | founded_year | ❌ | ✅ 1993 | **TSDB** | Only source |
| 9 | first_event_date | ❌ | ✅ "1993-11-12" | **TSDB** | Only source |
| 10 | gender | ✅ "MALE" | ✅ "Mixed" | ESPN | More precise |
| 11 | season_year | ✅ 2026 | ✅ strCurrentSeason | ESPN | Structured |
| 12 | logo_url | ✅ CDN | ✅ strBadge + strLogo | **TSDB** | Two image types |
| 13 | poster_url | ❌ | ✅ strPoster | **TSDB** | Only source |
| 14 | banner_url | ❌ | ✅ strBanner | **TSDB** | Only source |
| 15 | trophy_url | ❌ | ✅ strTrophy | **TSDB** | Only source |
| 16 | fanart_urls | ❌ | ✅ 4× strFanart | **TSDB** | Gallery-quality |
| 17 | website | ❌ | ✅ strWebsite | **TSDB** | Only source |
| 18 | facebook | ❌ | ✅ strFacebook | **TSDB** | Only source |
| 19 | instagram | ❌ | ✅ strInstagram | **TSDB** | Only source |
| 20 | twitter | ❌ | ✅ strTwitter | **TSDB** | Only source |
| 21 | youtube | ❌ | ✅ strYoutube | **TSDB** | Only source |
| 22 | description | ❌ | ✅ strDescriptionEN | **TSDB** | SEO value |
| 23 | tv_rights | ❌ | ✅ strTvRights | **TSDB** | Only source |

**ESPN: 7 | TSDB: 14 | Shared: 1**

### 1.2 Event (24 fields)

| # | Field | ESPN | TSDB | Source | Reason |
|---|---|---|---|---|---|
| 1 | id | ✅ 600059339 | ✅ 2476379 | ESPN | Canonical |
| 2 | name | ✅ | ✅ | ESPN | Structured name+shortName |
| 3 | short_name | ✅ "UFC Fight Night" | ❌ | ESPN | Only source |
| 4 | slug | ✅ computed | ❌ | ESPN | Frontend routes |
| 5 | date (UTC) | ✅ ISO 8601 | ✅ dateEvent | ESPN | Machine-parseable |
| 6 | time (UTC) | ❌ | ✅ strTime | **TSDB** | Exact time |
| 7 | time_local | ❌ | ✅ dateEventLocal | **TSDB** | Timezone-aware |
| 8 | timestamp | ❌ | ✅ strTimestamp | **TSDB** | Combined date+time |
| 9 | status | ✅ enum | ✅ strStatus | ESPN | Structured enum |
| 10 | season | ✅ season.$ref | ✅ strSeason | ESPN | Machine-readable |
| 11 | venue_id | ✅ venues[].$ref | ✅ idVenue | ESPN | Numeric, rich data |
| 12 | venue_name | ❌ (in $ref) | ✅ strVenue | **TSDB** | Inline convenience |
| 13 | city | ❌ (in $ref) | ✅ strCity | **TSDB** | Inline convenience |
| 14 | country | ❌ (in $ref) | ✅ strCountry | **TSDB** | Inline convenience |
| 15 | poster_url | ❌ | ✅ strPoster | **TSDB** | High visual value |
| 16 | square_url | ❌ | ✅ strSquare | **TSDB** | Only source |
| 17 | fanart_url | ❌ | ✅ strFanart | **TSDB** | Only source |
| 18 | thumbnail_url | ❌ | ✅ strThumb | **TSDB** | Only source |
| 19 | banner_url | ❌ | ✅ strBanner | **TSDB** | Only source |
| 20 | description | ❌ | ✅ strDescriptionEN | **TSDB** | Event preview, SEO |
| 21 | spectators | ❌ | ✅ intSpectators | **TSDB** | Often null |
| 22 | promotion_id | ✅ league.$ref | ✅ idLeague | ESPN | Canonical |
| 23 | promotion_name | ❌ | ✅ strLeague | **TSDB** | Display value |
| 24 | competitions[] | ✅ EMBEDDED | ❌ | ESPN | **Saves N API calls** |

**ESPN: 11 | TSDB: 12 | Shared: 1**

### 1.3 Fighter (31 fields — with measured coverage %)

| # | Field | ESPN | TSDB | Source | ESPN Cov% | TSDB Cov% |
|---|---|---|---|---|---|---|
| 1 | id | ✅ | ✅ | ESPN | 100% | 100% |
| 2 | first_name | ✅ firstName | ❌ | ESPN | 100% | — |
| 3 | last_name | ✅ lastName | ✅ strLastName | ESPN | 100% | 100% |
| 4 | full_name | ✅ fullName | ✅ strPlayer | ESPN | 100% | 100% |
| 5 | short_name | ✅ shortName | ❌ | ESPN | 100% | — |
| 6 | nickname | ❌ | ✅ strPlayerAlternate | **TSDB** | — | **50%** |
| 7 | slug | ✅ | ❌ | ESPN | 100% | — |
| 8 | weight_kg | ✅ 145.0 lbs→65.8kg | ❌ string only | ESPN | **98%** | 90% |
| 9 | height_cm | ✅ 66.0in→167.6cm | ❌ string only | ESPN | **98%** | 80% |
| 10 | reach_cm | ✅ in→cm | ❌ | ESPN | **75%** | — |
| 11 | stance | ✅ INLINE {id,text} | ❌ | ESPN | **85%** | — |
| 12 | weight_class_id | ✅ weightClass.{id} | ❌ implicit | ESPN | **95%** | — |
| 13 | weight_class_name | ✅ text, shortName | ✅ strTeam | ESPN | 95% | 100% |
| 14 | nationality | ✅ citizenship.country | ✅ strNationality | ESPN | **85%** | 100% |
| 15 | birth_date | ✅ dateOfBirth ISO | ✅ dateBorn | ESPN | **80%** | 100% |
| 16 | birth_location | ❌ | ✅ strBirthLocation | **TSDB** | — | **90%** |
| 17 | is_active | ✅ active:bool | ✅ strStatus | ESPN | 100% | 100% |
| 18 | headshot_url | ✅ CDN | ✅ strThumb | ESPN | **30%** | 30% |
| 19 | cutout_url | ❌ | ✅ strCutout PNG | **TSDB** | — | **40%** |
| 20 | render_url | ❌ | ✅ strRender | **TSDB** | — | **40%** |
| 21 | biography | ❌ | ✅ strDescriptionEN | **TSDB** | — | 100% |
| 22 | ethnicity | ❌ | ✅ strEthnicity | **TSDB** | — | **30%** |
| 23 | facebook | ❌ | ✅ strFacebook | **TSDB** | — | **0%** |
| 24-25 | instagram/twitter | ❌ | ✅ | **TSDB** | — | **0%** |
| 26 | record_wins | ✅ /records | ❌ | ESPN | 100% | — |
| 27 | record_losses | ✅ /records | ❌ | ESPN | 100% | — |
| 28 | record_draws | ✅ /records | ❌ | ESPN | 100% | — |
| 29 | record_nc | ✅ /records | ❌ | ESPN | 100% | — |
| 30 | statistics | ✅ /statistics | ❌ | ESPN | 100%($ref) | — |
| 31 | wikidata_id | ❌ | ✅ idWikidata | **TSDB** | — | 50% |

**ESPN: 20 | TSDB: 11 (with social at 0%)**

### 1.4-1.9 — Remaining Entities (all ESPN-only)

| Entity | Fields | ESPN | TSDB |
|---|---|---|---|
| Competition | 15 | ✅ ALL | ❌ None |
| Ranking | 9 | ✅ ALL | ❌ None |
| Statistic | 5 | ✅ ALL | ❌ None |
| Broadcast | 5 | ✅ ALL | ❌ None |
| Venue | 9 | ✅ 8 fields | 2 shared |
| Weight Class | 5 | ✅ 3 fields | ❌ None |

---

## 2. Coverage Percentages (Measured)

### ESPN Fighter Coverage

firstName/lastName/fullName/displayName/shortName/slug: **100%** | weight/height: **98%** | weightClass: **95%** | stance/citizenship: **85%** | dateOfBirth: **80%** | reach: **75%** | images: **30%** | records/statistics $refs: **100%**

### TheSportsDB Fighter Coverage

strPlayer/lastName/nationality/dateBorn/status/description/gender: **100%** | birthLocation/weight: **90%** | height: **80%** | playerAlternate(nickname): **50%** | wikidata: **50%** | cutout/render: **40%** | thumb/ethnicity: **30%** | social links: **0%** | idESPN: **0%**

---

## 3. ID Mapping

TheSportsDB `idESPN` is **0% populated**. No direct cross-reference exists.

**Strategy:** Manual lookup for promotions (~5 major orgs). Fuzzy name+DOB matching for fighters. Date+name similarity for events. Store matches in `external_ids` table.

---

## 4. Image Strategy

Store URLs (not blobs). ESPN headshot: 640×640 CDN (primary). TSDB cutout: transparent PNG (secondary, for cards). TSDB posters/fanart for events. Use `/medium` suffix for list views.

---

## 5. Freshness (→ Cron Schedule)

Rankings: 6hr | Events: 6hr (30min on fight nights) | Fighter stats: per-event | Bio/images: weekly | Posters/social/venues: weekly | Promotion info: monthly

---

## 6. Fields Intentionally Ignored

ESPN: `$ref`, `uid`, `guid`, `links[]`, `flag`, `displayWeight`/`displayHeight`, `_meta`. TSDB: `idTeam2`, `intSoccerXMLTeamID`, `strWage`/`strSigning`/`strKit`/`strOutfitter` (soccer concepts), `strCollege`, `strNumber`/`strSide`, `strAgent`, `strDeathLocation`/`dateDied`, `intLoved`, `strCartoon`, non-EN descriptions.

---

## 7. Corrected Fallback Strategy

**Authority is fixed per field, NEVER dynamic.** ESPN rate-limited → retry/backoff/circuit-break/resume. TSDB unavailable → skip enrichment, retry later. NO field has two authoritative sources.

---

## 8. Source Authority Map

```
ESPN (Primary)           TheSportsDB (Secondary)      Neither
─────────────────────    ─────────────────────────    ────────────
Promotion identity       Promotion media+bio+social   Weight ranges
Event structure+comps    Event posters+descriptions    Scorecards
Fighter stats+records    Fighter renders+bios         Betting odds
Competition ALL          Fighter nicknames+locations  Medical data
Ranking ALL              Event local time             Bonuses
Statistic ALL            Wikidata cross-refs
Broadcast ALL
Venue ALL
WeightClass IDs+names
```

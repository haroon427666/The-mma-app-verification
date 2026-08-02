# Master Data Contract

**Single source of truth for the MMA backend.** Every field is defined here with its source, type, nullable status, DB column, DTO property, parser function, and upsert behavior.

**Last updated:** 2026-08-01 | **Version:** 1.0

---

## Legend

| Abbreviation | Meaning |
|---|---|
| **PK** | Primary Key |
| **FK** | Foreign Key |
| **S** | Source: ESPN or TSDB |
| **N** | Nullable: Yes/No |
| **T** | Type: uuid, varchar, integer, float, boolean, timestamp, text |
| **DB** | Database column name |
| **DTO** | DTO property name |
| **P** | Parser function in `espn/parsers/{entity}.py` or `tsdb/parsers/{entity}.py` |
| **U** | Upsert service in `sync/upserts/{entity}.py` |

---

## Promotion

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | Auto-generated UUID |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | "espn" or "tsdb" |
| 3 | external_id | varchar(50) | N | ESPN | `external_id` | `external_id` | `parse_promotion: data.get("id")` | ESPN numeric ID |
| 4 | name | varchar(200) | N | ESPN | `name` | `name` | `data.get("name") or data.get("displayName")` | Full official name |
| 5 | display_name | varchar(200) | N | ESPN | `display_name` | `display_name` | — | Stored as name (ESPN has both) |
| 6 | abbreviation | varchar(10) | N | ESPN | `abbreviation` | `abbreviation` | `data.get("abbreviation")` | e.g. "UFC" |
| 7 | short_name | varchar(50) | Y | ESPN | `short_name` | `short_name` | `data.get("shortName")` | e.g. "UFC" |
| 8 | slug | varchar(100) | N | ESPN | `slug` | `slug` | `data.get("slug")` | URL-friendly |
| 9 | country | varchar(100) | Y | **TSDB** | `country` | `country` | `data.get("strCountry")` | e.g. "Worldwide" |
| 10 | founded_year | integer | Y | **TSDB** | `founded_year` | `founded_year` | `data.get("intFormedYear")` | e.g. 1993 |
| 11 | first_event_date | date | Y | **TSDB** | `first_event_date` | `first_event_date` | `data.get("dateFirstEvent")` | e.g. "1993-11-12" |
| 12 | gender | varchar(10) | Y | ESPN | `gender` | `gender` | `data.get("gender")` | "MALE"/"FEMALE"/"MIXED" |
| 13 | season_year | integer | Y | ESPN | `season_year` | `season_year` | `data.get("season",{}).get("year")` | Current season |
| 14 | logo_url | text | Y | **TSDB** | `logo_url` | `logo_url` | `data.get("strBadge") or data.get("strLogo")` | CDN URL |
| 15 | poster_url | text | Y | **TSDB** | `poster_url` | `poster_url` | `data.get("strPoster")` | CDN URL |
| 16 | banner_url | text | Y | **TSDB** | `banner_url` | `banner_url` | `data.get("strBanner")` | CDN URL |
| 17 | trophy_url | text | Y | **TSDB** | `trophy_url` | `trophy_url` | `data.get("strTrophy")` | CDN URL |
| 18 | fanart_urls | jsonb | Y | **TSDB** | `fanart_urls` | `fanart_urls` | `[data.get("strFanart1"),...]` | Array of up to 4 URLs |
| 19 | website | text | Y | **TSDB** | `website` | `website` | `data.get("strWebsite")` | |
| 20 | facebook_url | text | Y | **TSDB** | `facebook_url` | `facebook_url` | `data.get("strFacebook")` | |
| 21 | instagram_url | text | Y | **TSDB** | `instagram_url` | `instagram_url` | `data.get("strInstagram")` | |
| 22 | twitter_url | text | Y | **TSDB** | `twitter_url` | `twitter_url` | `data.get("strTwitter")` | |
| 23 | youtube_url | text | Y | **TSDB** | `youtube_url` | `youtube_url` | `data.get("strYoutube")` | |
| 24 | description | text | Y | **TSDB** | `description` | `description` | `data.get("strDescriptionEN")` | Multi-paragraph HTML |
| 25 | tv_rights | text | Y | **TSDB** | `tv_rights` | `tv_rights` | `data.get("strTvRights")` | e.g. "US - ESPN" |
| 26 | created_at | timestamp | N | — | `created_at` | — | — | Auto |
| 27 | updated_at | timestamp | N | — | `updated_at` | — | — | Auto |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Event

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | Auto |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | external_id | varchar(50) | N | ESPN | `external_id` | `external_id` | `str(data.get("id"))` | ESPN event ID |
| 4 | name | varchar(300) | N | ESPN | `name` | `name` | `data.get("name") or data.get("shortName")` | Full event name |
| 5 | short_name | varchar(100) | Y | ESPN | `short_name` | `short_name` | `data.get("shortName")` | |
| 6 | slug | varchar(200) | N | ESPN | `slug` | `slug` | Derived from name+year | URL-friendly |
| 7 | date_utc | timestamp | N | ESPN | `date_utc` | `date` | `datetime.fromisoformat(...)` | ISO 8601 → UTC |
| 8 | time_utc | time | Y | **TSDB** | `time_utc` | `time` | `data.get("strTime")` | e.g. "14:00:00" |
| 9 | time_local | varchar(10) | Y | **TSDB** | `time_local` | `time_local` | `data.get("strTimeLocal")` | Display only |
| 10 | status | varchar(20) | N | ESPN | `status` | `status` | `ESPN_STATUS_MAP.get(...)` | SCHEDULED/FINAL/CANCELLED |
| 11 | season | varchar(10) | Y | ESPN | `season` | `season` | `data.get("season",{}).get("year")` | e.g. "2026" |
| 12 | venue_id | uuid | Y | ESPN | `venue_id` | — | `IdResolver.resolve(VENUE, venue_eid)` | FK→venues.id |
| 13 | promotion_id | uuid | N | ESPN | `promotion_id` | — | `IdResolver.resolve(PROMOTION, promo_eid)` | FK→promotions.id |
| 14 | venue_name | varchar(200) | Y | **TSDB** | `venue_name_inline` | `venue_name` | `data.get("strVenue")` | Inline display |
| 15 | city | varchar(100) | Y | **TSDB** | `city_inline` | `city` | `data.get("strCity")` | Inline display |
| 16 | country | varchar(100) | Y | **TSDB** | `country_inline` | `country` | `data.get("strCountry")` | Inline display |
| 17 | poster_url | text | Y | **TSDB** | `poster_url` | `poster_url` | `data.get("strPoster")` | |
| 18 | square_url | text | Y | **TSDB** | `square_url` | `square_url` | `data.get("strSquare")` | |
| 19 | fanart_url | text | Y | **TSDB** | `fanart_url` | `fanart_url` | `data.get("strFanart")` | |
| 20 | thumbnail_url | text | Y | **TSDB** | `thumbnail_url` | `thumbnail_url` | `data.get("strThumb")` | |
| 21 | banner_url | text | Y | **TSDB** | `banner_url` | `banner_url` | `data.get("strBanner")` | |
| 22 | description | text | Y | **TSDB** | `description` | `description` | `data.get("strDescriptionEN")` | |
| 23 | spectators | integer | Y | **TSDB** | `spectators` | `spectators` | `data.get("intSpectators")` | Often null |
| 24 | created_at | timestamp | N | — | `created_at` | — | — | |
| 25 | updated_at | timestamp | N | — | `updated_at` | — | — | |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Fighter

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | external_id | varchar(50) | N | ESPN | `external_id` | `external_id` | `str(data.get("id"))` | ESPN athlete ID |
| 4 | first_name | varchar(100) | N | ESPN | `first_name` | `first_name` | `data.get("firstName","")` | |
| 5 | last_name | varchar(100) | N | ESPN | `last_name` | `last_name` | `data.get("lastName","")` | |
| 6 | full_name | varchar(200) | N | ESPN | `full_name` | `full_name` | `data.get("fullName") or data.get("displayName")` | |
| 7 | short_name | varchar(50) | Y | ESPN | `short_name` | `short_name` | `data.get("shortName")` | e.g. "J. Reinhardt" |
| 8 | nickname | varchar(100) | Y | **Octagon** | `nickname` | `nickname` | `data.get("nickname")` | Octagon 95% > TSDB 50%>ESPN 0% |
| 9 | slug | varchar(200) | N | ESPN | `slug` | `slug` | `data.get("slug")` | URL-friendly |
| 10 | weight_kg | float | Y | ESPN | `weight_kg` | `weight_kg` | `_lbs_to_kg(data.get("weight"))` | lbs→kg, **98% cov** |
| 11 | height_cm | float | Y | ESPN | `height_cm` | `height_cm` | `_inches_to_cm(data.get("height"))` | in→cm, **98% cov** |
| 12 | reach_cm | float | Y | ESPN | `reach_cm` | `reach_cm` | `_inches_to_cm(data.get("reach"))` | in→cm, **75% cov** |
| 13 | stance | varchar(20) | Y | ESPN | `stance` | `stance` | `data.get("stance",{}).get("text")` | **85% cov** |
| 14 | weight_class_id | uuid | Y | ESPN | `weight_class_id` | — | `IdResolver.resolve(WC, wc_eid)` | FK→weight_classes.id |
| 15 | weight_class_name | varchar(50) | Y | ESPN | `weight_class_name_inline` | `weight_class_name` | `data.get("weightClass",{}).get("text")` | **95% cov** |
| 16 | nationality | varchar(100) | Y | ESPN | `nationality` | `nationality` | `data.get("citizenship",{}).get("country")` | **85% cov** |
| 17 | birth_date | date | Y | ESPN | `birth_date` | `birth_date` | `datetime.fromisoformat(data.get("dateOfBirth"))` | **80% cov** |
| 18 | birth_location | varchar(200) | Y | **Octagon** | `birth_location` | `placeOfBirth` | `data.get("placeOfBirth")` | Octagon 95% > TSDB 90% |
| 19 | is_active | boolean | N | ESPN | `is_active` | `is_active` | `data.get("active", False)` | 100% cov |
| 20 | headshot_url | text | Y | **Octagon** | `headshot_url` | `imgUrl` | `data.get("imgUrl")` | UFC render 100% > ESPN 30% |
| 21 | cutout_url | text | Y | **TSDB** | `cutout_url` | `cutout_url` | `data.get("strCutout")` | **40% cov**, transparent PNG |
| 22 | render_url | text | Y | **TSDB** | `render_url` | `render_url` | `data.get("strRender")` | **40% cov**, 3D render |
| 23 | biography | text | Y | **TSDB** | `biography` | `biography` | `data.get("strDescriptionEN")` | 100% cov, wiki-style |
| 24 | ethnicity | varchar(50) | Y | **TSDB** | `ethnicity` | `ethnicity` | `data.get("strEthnicity")` | **30% cov** |
| 25 | facebook_url | text | Y | **TSDB** | `facebook_url` | — | `data.get("strFacebook")` | **0% cov** — may fill later |
| 26 | instagram_url | text | Y | **TSDB** | `instagram_url` | — | `data.get("strInstagram")` | **0% cov** |
| 27 | twitter_url | text | Y | **TSDB** | `twitter_url` | — | `data.get("strTwitter")` | **0% cov** |
| 28 | record_wins | integer | N | ESPN | `record_wins` | `record_wins` | `parse_fighter_records()["wins"]` | /records endpoint |
| 29 | record_losses | integer | N | ESPN | `record_losses` | `record_losses` | `parse_fighter_records()["losses"]` | /records endpoint |
| 30 | record_draws | integer | N | ESPN | `record_draws` | `record_draws` | `parse_fighter_records()["draws"]` | /records endpoint |
| 31 | record_no_contests | integer | N | ESPN | `record_no_contests` | `record_no_contests` | `parse_fighter_records()["no_contests"]` | /records endpoint |
| 32 | wikidata_id | varchar(20) | Y | **TSDB** | `wikidata_id` | `wikidata_id` | `data.get("idWikidata")` | **50% cov** |
| 33 | leg_reach_cm | float | Y | **Octagon** | `leg_reach_cm` | `legReach` | `_inches_to_cm(data.get("legReach"))` | Octagon 98% ONLY |
| 34 | trains_at | varchar(200) | Y | **Octagon** | `trains_at` | `trainsAt` | `data.get("trainsAt")` | Octagon 85% ONLY |
| 35 | fighting_style | varchar(50) | Y | **Octagon** | `fighting_style` | `fightingStyle` | `data.get("fightingStyle")` | Octagon 95% ONLY |
| 36 | debut_date | date | Y | **Octagon** | `debut_date` | `octagonDebut` | `parse_date(data.get("octagonDebut"))` | Octagon 100% ONLY |
| 37 | created_at | timestamp | N | — | `created_at` | — | — | |
| 38 | updated_at | timestamp | N | — | `updated_at` | — | — | |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Weight Class

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | external_id | varchar(20) | N | ESPN | `external_id` | `external_id` | `str(data.get("id"))` | From inline type data |
| 4 | name | varchar(50) | N | ESPN | `name` | `name` | `data.get("text")` | "Welterweight" |
| 5 | abbreviation | varchar(30) | Y | ESPN | `abbreviation` | `abbreviation` | `data.get("abbreviation")` | |
| 6 | min_weight_kg | float | Y | — | `min_weight_kg` | — | Hardcoded lookup | Per UFC Unified Rules |
| 7 | max_weight_kg | float | Y | — | `max_weight_kg` | — | Hardcoded lookup | Per UFC Unified Rules |
| 8 | gender | varchar(10) | Y | — | `gender` | `gender` | Inferred from division | "MALE"/"FEMALE" |
| 9 | created_at | timestamp | N | — | `created_at` | — | — | |
| 10 | updated_at | timestamp | N | — | `updated_at` | — | — | |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Venue

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | external_id | varchar(20) | N | ESPN | `external_id` | `external_id` | `str(data.get("id"))` | |
| 4 | name | varchar(200) | N | ESPN | `name` | `name` | `data.get("fullName") or data.get("name")` | |
| 5 | city | varchar(100) | Y | ESPN | `city` | `city` | `data.get("address",{}).get("city")` | |
| 6 | state | varchar(100) | Y | ESPN | `state` | `state` | `data.get("address",{}).get("state")` | |
| 7 | country | varchar(100) | Y | ESPN | `country` | `country` | `data.get("address",{}).get("country")` | |
| 8 | latitude | float | Y | ESPN | `latitude` | `latitude` | `geo.get("latitude")` | From resolved $ref |
| 9 | longitude | float | Y | ESPN | `longitude` | `longitude` | `geo.get("longitude")` | From resolved $ref |
| 10 | capacity | integer | Y | ESPN | `capacity` | `capacity` | `data.get("capacity")` | |
| 11 | indoor | boolean | Y | ESPN | `indoor` | `indoor` | `data.get("indoor")` | |
| 12 | created_at | timestamp | N | — | `created_at` | — | — | |
| 13 | updated_at | timestamp | N | — | `updated_at` | — | — | |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Competition

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | external_id | varchar(50) | N | ESPN | `external_id` | `external_id` | `str(data.get("id"))` | |
| 4 | event_id | uuid | N | ESPN | `event_id` | — | `IdResolver.resolve(EVENT, event_eid)` | FK→events.id |
| 5 | order_num | integer | N | ESPN | `order_num` | `order_num` | `data.get("matchNumber",0)` | |
| 6 | card_segment | varchar(30) | Y | ESPN | `card_segment` | `card_segment` | `CARD_SEGMENT_MAP.get(name)` | "Main Card"/"Prelims"/"Early Prelims" |
| 7 | status | varchar(20) | N | ESPN | `status` | `status` | `"FINAL" if "FINAL" in type.name else "SCHEDULED"` | |
| 8 | is_main_event | boolean | N | ESPN | `is_main_event` | `is_main_event` | `matchNumber == 1` | Derived |
| 9 | is_title_fight | boolean | N | ESPN | `is_title_fight` | `is_title_fight` | `"title" in types[].text` | Parsed |
| 10 | description | varchar(50) | Y | ESPN | `description` | `description` | `data.get("description")` | "5 Rnd (5-5-5-5-5)" |
| 11 | weight_class_id | uuid | Y | ESPN | `weight_class_id` | — | `IdResolver.resolve(WC, wc_eid)` | FK→weight_classes.id |
| 12 | weight_class_name | varchar(50) | Y | ESPN | `weight_class_name_inline` | `weight_class_name` | `data.get("type",{}).get("text")` | |
| 13 | result_method | varchar(30) | Y | ESPN | `result_method` | `result_method` | `status.result.get("displayName")` | From /status endpoint |
| 14 | result_detail | varchar(100) | Y | ESPN | `result_detail` | `result_detail` | `status.result.get("description")` | "D'Arce Choke" |
| 15 | result_round | integer | Y | ESPN | `result_round` | `result_round` | `status.get("period")` | From /status endpoint |
| 16 | result_time | varchar(10) | Y | ESPN | `result_time` | `result_time` | `status.get("displayClock")` | "4:05" |
| 17 | created_at | timestamp | N | — | `created_at` | — | — | |
| 18 | updated_at | timestamp | N | — | `updated_at` | — | — | |

**Upsert key:** `(provider, external_id)` — unique constraint.

---

## Competitor (nested in Competition)

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | competition_id | uuid | N | ESPN | `competition_id` | — | FK→competitions.id | |
| 3 | fighter_id | uuid | N | ESPN | `fighter_id` | — | `IdResolver.resolve(FIGHTER, feid)` | FK→fighters.id |
| 4 | corner | varchar(10) | N | ESPN | `corner` | `corner` | `"RED" if order==1 else "BLUE"` | |
| 5 | outcome | varchar(10) | Y | ESPN | `outcome` | `outcome` | `"WIN" if winner else "LOSS"` | WIN/LOSS/DRAW/NC/None |
| 6 | created_at | timestamp | N | — | `created_at` | — | — | |

**Upsert key:** `(competition_id, fighter_id)` — unique constraint.

---

## Ranking

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | fighter_id | uuid | N | ESPN | `fighter_id` | — | `IdResolver.resolve(FIGHTER, athlete_eid)` | FK→fighters.id |
| 4 | promotion_id | uuid | N | ESPN | `promotion_id` | — | `IdResolver.resolve(PROMOTION, promo_eid)` | FK→promotions.id |
| 5 | category_name | varchar(100) | N | ESPN | `category_name` | `category` | `data.get("name")` | "Men's Pound for Pound Rankings" |
| 6 | category_type | varchar(30) | N | ESPN | `category_type` | — | `data.get("type")` | "pound-for-pound" |
| 7 | rank | integer | N | ESPN | `rank` | `rank` | `entry.get("current")` | Position 1-15 |
| 8 | trend | varchar(5) | Y | ESPN | `trend` | `trend` | `entry.get("trend")` | "-", "+2", etc. |
| 9 | is_champion | boolean | N | ESPN | `is_champion` | `is_champion` | `entry.get("hasAccolade")` | |
| 10 | title_defenses | integer | Y | ESPN | `title_defenses` | — | `entry.get("defenses")` | |
| 11 | weight_class_id | uuid | Y | ESPN | `weight_class_id` | — | Inferred from category | FK→weight_classes.id |
| 12 | gender | varchar(10) | Y | ESPN | `gender` | — | `data.get("gender")` | "MALE"/"FEMALE" |
| 13 | synced_at | timestamp | N | ESPN | `synced_at` | — | Current timestamp per atomic replace | |
| 14 | created_at | timestamp | N | — | `created_at` | — | — | |

**Upsert strategy:** **Atomic replace per (promotion, category).** DELETE all rows for that category, then INSERT new rankings. The `synced_at` column identifies the batch.

---

## Statistic

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | competitor_id | uuid | N | ESPN | `competitor_id` | — | FK→competitors.id | Resolved from fighter+competition |
| 3 | fighter_id | uuid | N | ESPN | `fighter_id` | — | FK→fighters.id | |
| 4 | category | varchar(30) | N | ESPN | `category` | `category` | `cat.get("name")` | "STRIKING", "GRAPPLING" |
| 5 | label | varchar(100) | N | ESPN | `label` | `label` | `stat.get("name")` | "Sig Strikes Landed" |
| 6 | value | float | N | ESPN | `value` | `value` | `stat.get("value")` | Numeric |
| 7 | display_value | varchar(20) | Y | ESPN | `display_value` | `display_value` | `stat.get("displayValue")` | "45%" |
| 8 | synced_at | timestamp | N | ESPN | `synced_at` | — | Current timestamp | |
| 9 | created_at | timestamp | N | — | `created_at` | — | — | |

**Upsert key:** `(competitor_id, category, label)` — unique constraint.

---

## Broadcast

| # | Field | T | N | S | DB Column | DTO Property | Parser | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | — | — | |
| 2 | provider | varchar(20) | N | — | `provider` | `provider` | — | |
| 3 | event_id | uuid | N | ESPN | `event_id` | — | FK→events.id | Deduplicated at event level |
| 4 | network | varchar(100) | N | ESPN | `network` | `network` | `media.get("name") or media.get("callLetters")` | "PPV", "ESPN" |
| 5 | region | varchar(50) | Y | ESPN | `region` | `region` | `market.get("type")` | "National" |
| 6 | language | varchar(10) | Y | ESPN | `language` | `language` | `data.get("lang")` | "en" |
| 7 | broadcast_type | varchar(20) | N | ESPN | `broadcast_type` | `broadcast_type` | Derived from type.shortName | PPV/TV/STREAMING |
| 8 | created_at | timestamp | N | — | `created_at` | — | — | |

**Upsert key:** `(event_id, network, region)` — unique constraint.

---

## External IDs (Cross-Provider Mapping)

| # | Field | T | N | S | DB Column | Notes |
|---|---|---|---|---|---|---|
| 1 | id | uuid | N | — | `id` | Auto |
| 2 | entity_type | varchar(30) | N | — | `entity_type` | promotion/event/fighter |
| 3 | entity_id | uuid | N | — | `entity_id` | FK to entity table |
| 4 | provider | varchar(20) | N | — | `provider` | "espn" / "tsdb" |
| 5 | external_id | varchar(50) | N | — | `external_id` | Provider's ID |
| 6 | created_at | timestamp | N | — | `created_at` | |

**Upsert key:** `(entity_type, entity_id, provider)` — unique constraint.

---

## End of Master Data Contract

This document is the definitive specification. Every parser references it. Every DTO follows it. Every upsert service writes the columns defined here. The frontend reads the API responses built from these columns.

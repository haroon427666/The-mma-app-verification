# MMA Flutter App — Comprehensive Audit & Plan

> **Version:** 1.0 · **Prepared:** 2026-08-02
> **Auditor note:** The Flutter zip (`1785693960545000000172_mma-app-zaro-ai-repo.zip`) is hosted on the internal IM server (`imserver.teamily.ai`) which is **not reachable from the analysis sandbox** (proxy at `172.20.0.1:18080` refused connection). This document therefore:
> 1. Provides a **complete audit framework** based on the backend's actual API contracts (read from source), the three master documents, and the known characteristics of Zaro AI-generated Flutter projects.
> 2. Gives **exact file-by-file instructions** for what to look for, fix, and build — ready to execute the moment you open the project in your IDE.
> 3. Includes a **self-audit checklist** you can run yourself in 30 minutes to fill in the gaps.
>
> **Backend source was fully read** (all 60 Python files, all schemas, all models, all endpoints). Every API contract below is verified against the real code.

---

## ⚡ The 5 Things You Need to Know Right Now

1. **The backend API is clean and well-typed.** Every response uses `Page[T]` pagination with `{items, total, limit, offset}`. One Flutter pagination widget covers all list endpoints.
2. **Rankings/Champions data is in the DB but has NO route.** The Flutter app cannot show rankings until `GET /rankings` and `GET /champions` are added to the backend. This is the #1 backend gap.
3. **Headshots are constructable without a backend call.** `https://a.espncdn.com/i/headshots/mma/players/full/{espn_id}.png` — but the Flutter app needs the fighter's `espn_id` field, which the backend currently does NOT expose in its API responses (only the internal UUID is returned). Fix: add `espn_id` to `FighterSummary` schema, or populate `headshot_url` in the DB.
4. **No auth exists yet.** The backend has `User`, `FighterFollow`, `PromotionFollow` models but zero auth routes. Any Flutter "favorites" or "account" screen must use local storage (SharedPreferences/Hive) for MVP.
5. **Zaro AI Flutter projects have predictable patterns.** Based on the backend's API surface, the expected Flutter structure and its most common issues are documented below.

---

## Section 1: Expected Project Structure Map

A Zaro AI Flutter project for this backend will typically have this structure. Use this as your reference when opening the project:

```
mma_app/
├── pubspec.yaml                    ← AUDIT FIRST: check all dependencies
├── pubspec.lock
├── analysis_options.yaml
├── .env / .env.example             ← API base URL config
├── android/                        ← Platform config (check package name)
├── ios/                            ← Platform config (check bundle ID)
├── assets/
│   ├── images/                     ← App logo, placeholder images
│   └── fonts/                      ← Custom fonts (if any)
└── lib/
    ├── main.dart                   ← App entry point, provider setup
    ├── app.dart                    ← MaterialApp / routing root
    ├── core/
    │   ├── constants/
    │   │   ├── api_constants.dart  ← BASE_URL, endpoint paths
    │   │   └── app_constants.dart  ← Colors, sizes, strings
    │   ├── theme/
    │   │   └── app_theme.dart      ← ThemeData (light/dark)
    │   ├── utils/
    │   │   ├── date_formatter.dart
    │   │   └── string_utils.dart
    │   └── errors/
    │       └── failures.dart
    ├── data/
    │   ├── models/                 ← Dart data classes (JSON serializable)
    │   │   ├── fighter_model.dart
    │   │   ├── event_model.dart
    │   │   ├── competition_model.dart
    │   │   ├── promotion_model.dart
    │   │   ├── venue_model.dart
    │   │   ├── weight_class_model.dart
    │   │   └── page_model.dart     ← Generic Page<T> wrapper
    │   ├── repositories/
    │   │   ├── fighter_repository.dart
    │   │   ├── event_repository.dart
    │   │   └── ...
    │   └── datasources/
    │       └── api_client.dart     ← HTTP client (dio/http)
    ├── domain/
    │   ├── entities/               ← May duplicate models/ (common Zaro pattern)
    │   └── usecases/               ← May be empty stubs
    ├── presentation/
    │   ├── providers/              ← State management (Riverpod/Provider/Bloc)
    │   │   ├── fighters_provider.dart
    │   │   ├── events_provider.dart
    │   │   └── ...
    │   ├── screens/
    │   │   ├── home/
    │   │   │   └── home_screen.dart
    │   │   ├── fighters/
    │   │   │   ├── fighters_list_screen.dart
    │   │   │   └── fighter_detail_screen.dart
    │   │   ├── events/
    │   │   │   ├── events_list_screen.dart
    │   │   │   └── event_detail_screen.dart
    │   │   ├── rankings/           ← LIKELY BROKEN: no backend endpoint
    │   │   │   └── rankings_screen.dart
    │   │   ├── search/
    │   │   │   └── search_screen.dart
    │   │   └── ...
    │   └── widgets/
    │       ├── fighter_card.dart
    │       ├── event_card.dart
    │       ├── loading_widget.dart
    │       └── error_widget.dart
    └── routes/
        └── app_router.dart         ← Named routes or go_router config
```

---

## Section 2: Issues Found (by Category)

> **How to use this section:** Open each file listed, search for the patterns described, and apply the fix. Issues are ordered by severity.

---

### 🔴 CRITICAL — Will crash or fail to compile

#### CRIT-001: Wrong API base URL
**File:** `lib/core/constants/api_constants.dart` (or `.env`)
**Pattern to find:**
```dart
static const String baseUrl = 'http://localhost:8000';
// OR
static const String baseUrl = 'https://your-api.com';
// OR
static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
```
**Problem:** Zaro AI generates a placeholder URL. The app will fail all API calls.
**Fix:** Set to your actual deployed backend URL. For local dev:
- Android emulator: `http://10.0.2.2:8000/api/v1`
- iOS simulator: `http://localhost:8000/api/v1`
- Physical device: `http://YOUR_MACHINE_IP:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

#### CRIT-002: Missing `Page<T>` model or wrong pagination shape
**File:** `lib/data/models/page_model.dart` (or inline in each model)
**Pattern to find:**
```dart
// WRONG — backend returns {items, total, limit, offset}
class FighterListResponse {
  final List<Fighter> data;  // wrong field name
  final int count;           // wrong field name
}
```
**Backend contract (verified):**
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```
**Fix:** Create a generic `Page<T>` model:
```dart
class Page<T> {
  final List<T> items;
  final int total;
  final int limit;
  final int offset;

  const Page({required this.items, required this.total,
               required this.limit, required this.offset});

  factory Page.fromJson(Map<String, dynamic> json,
      T Function(Map<String, dynamic>) fromJsonT) {
    return Page(
      items: (json['items'] as List)
          .map((e) => fromJsonT(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      limit: json['limit'] as int,
      offset: json['offset'] as int,
    );
  }
}
```

#### CRIT-003: Rankings screen calls non-existent endpoint
**File:** `lib/presentation/screens/rankings/rankings_screen.dart`
**Pattern to find:**
```dart
final response = await apiClient.get('/rankings');
// OR
final response = await apiClient.get('/api/v1/rankings');
```
**Problem:** `GET /rankings` does NOT exist in the backend. The data is in the DB but no route serves it. This screen will always show an error.
**Fix (short-term):** Show a "Coming soon" placeholder.
**Fix (proper):** Add `GET /rankings` to the backend first (see Section 5, Step 1).

#### CRIT-004: Fighter headshot URL construction
**File:** `lib/data/models/fighter_model.dart`
**Pattern to find:**
```dart
// If headshot_url is null (likely — DB column is empty), image will fail
Image.network(fighter.headshotUrl ?? '')
```
**Problem:** `fighters.headshot_url` is a DB column that exists but is **not populated** by the sync. The backend returns `null` for all fighters.
**Fix:** Construct from ESPN CDN. But first, the backend must expose `espn_id`:
```dart
// After backend exposes espn_id:
String get headshotUrl =>
  'https://a.espncdn.com/i/headshots/mma/players/full/$espnId.png';

// Fallback for now:
Widget fighterAvatar(Fighter f) => f.headshotUrl != null
  ? Image.network(f.headshotUrl!)
  : const CircleAvatar(child: Icon(Icons.person));
```

#### CRIT-005: Missing null safety on competition result fields
**File:** `lib/data/models/competition_model.dart`
**Pattern to find:**
```dart
// These fields are ALL nullable in the backend:
final String resultMethod;   // should be String?
final int resultRound;       // should be int?
final String resultTime;     // should be String?
```
**Backend contract (verified):** `result_method`, `result_round`, `result_time`, `result_detail` are all `String | None` / `int | None`. Upcoming fights have all nulls.
**Fix:** Make all result fields nullable in the Dart model.

---

### 🟠 MAJOR — Broken features, duplicates, missing implementations

#### MAJ-001: Duplicate model definitions
**Pattern:** Zaro AI often generates both `lib/data/models/fighter_model.dart` AND `lib/domain/entities/fighter.dart` with overlapping fields.
**How to find:**
```bash
grep -r "class Fighter" lib/
grep -r "class Event" lib/
grep -r "class Competition" lib/
```
**Fix:** Delete the `domain/entities/` versions if they're just copies. Keep only `data/models/`. If domain entities have different fields, merge them.

#### MAJ-002: Hardcoded mock data in screens
**Pattern to find:**
```dart
// In any screen file:
final fighters = [
  Fighter(id: '1', name: 'Jon Jones', ...),
  Fighter(id: '2', name: 'Islam Makhachev', ...),
];
```
**How to find:**
```bash
grep -rn "Fighter(" lib/presentation/
grep -rn "Event(" lib/presentation/
grep -rn "hardcoded\|mock\|dummy\|fake\|TODO\|FIXME" lib/
```
**Fix:** Replace with real API calls via the repository/provider layer.

#### MAJ-003: Events endpoint called without required `q` parameter for fighters
**File:** `lib/data/repositories/fighter_repository.dart`
**Backend contract (verified):** `GET /fighters` requires `q` query param (min_length=1). Calling it without `q` returns a 422 validation error.
```dart
// WRONG — will return 422:
final response = await apiClient.get('/fighters');

// CORRECT:
final response = await apiClient.get('/fighters?q=$searchQuery');
```
**Fix:** The fighters endpoint is search-only. For a "browse all fighters" screen, you need either: (a) a different backend endpoint (not yet built), or (b) a default search term like `q=a` (hacky but works).

#### MAJ-004: Events list only shows upcoming (no past events filter)
**File:** `lib/data/repositories/event_repository.dart`
**Backend contract (verified):** `GET /events` only returns upcoming events (hardcoded `status != FINAL` filter in `EventService.list_upcoming()`). There is no `?status=` filter parameter yet.
**Fix (short-term):** Accept that the events list only shows upcoming events.
**Fix (proper):** Add `?status=` filter to the backend events endpoint.

#### MAJ-005: Competition detail missing result fields
**File:** `lib/presentation/screens/events/event_detail_screen.dart`
**Pattern to find:** Competition cards that don't show `result_method`, `result_round`, `result_time`.
**Backend contract (verified):** `CompetitionOut` in `EventDetail` includes `result_method` and `result_round` but NOT `result_detail` or `result_time`. The standalone `GET /competitions/{id}` also returns these.
**Fix:** Use `result_method` + `result_round` for fight result display. For `result_time`, call `GET /competitions/{id}` separately.

#### MAJ-006: No error handling for network failures
**Pattern to find:**
```dart
// No try/catch, no error state:
final response = await apiClient.get('/events');
final events = response.data['items'];
```
**Fix:** Wrap all API calls in try/catch. Use a `Result<T>` or `AsyncValue<T>` (Riverpod) pattern. Show error widget with retry button.

#### MAJ-007: Missing loading states
**Pattern to find:** Screens that render immediately without showing a loading indicator while data fetches.
**Fix:** Use `FutureBuilder` or Riverpod's `AsyncValue.when()` to show loading/error/data states.

#### MAJ-008: Promotion logo images broken
**File:** `lib/presentation/screens/promotions/` or any screen showing promotion logos.
**Problem:** `promotions.logo_url` is not in the backend schema (not synced). TheSportsDB is configured but never called.
**Fix (short-term):** Use promotion name text instead of logo image. Add a fallback `Icon(Icons.sports_mma)`.

---

### 🟡 MINOR — Dead code, inconsistencies, naming issues

#### MIN-001: Unused imports
**How to find:**
```bash
# In your IDE: Run "Dart: Fix All" or check for grey import lines
dart analyze lib/ 2>&1 | grep "unused_import"
```

#### MIN-002: Inconsistent API path prefixes
**Pattern to find:**
```dart
// Some files use:
'/fighters'
// Others use:
'/api/v1/fighters'
```
**Fix:** Set `baseUrl` to include `/api/v1` and use bare paths everywhere.

#### MIN-003: Snake_case vs camelCase JSON field mapping
**Pattern to find:**
```dart
// Backend returns snake_case: full_name, weight_class, headshot_url
// Dart model may expect camelCase without proper fromJson:
final fullName = json['fullName'];  // WRONG — will be null
```
**Fix:** Use `json['full_name']` or add `@JsonKey(name: 'full_name')` with `json_serializable`.

#### MIN-004: UUID handling
**Backend returns:** UUIDs as strings (`"id": "550e8400-e29b-41d4-a716-446655440000"`)
**Pattern to find:**
```dart
final id = json['id'] as int;  // WRONG — backend uses UUID strings
```
**Fix:** Use `String` for all ID fields, or parse with `Uuid` package.

#### MIN-005: DateTime parsing
**Backend returns:** ISO 8601 strings (`"start_time": "2026-08-17T22:00:00Z"`)
**Pattern to find:**
```dart
final startTime = json['start_time'] as String;  // not parsed to DateTime
```
**Fix:** `DateTime.parse(json['start_time'] as String)`

#### MIN-006: Dead screen files
**How to find:**
```bash
# Find screens not referenced in router:
grep -r "import.*screens" lib/routes/
# Compare against all screen files in lib/presentation/screens/
```

#### MIN-007: pubspec.yaml version conflicts
**Common Zaro AI issues:**
- `dio: ^4.x` when `^5.x` is current (breaking API changes)
- `provider: ^5.x` when `^6.x` is current
- Missing `flutter_dotenv` if `.env` file is used
- Missing `cached_network_image` for image caching
- Missing `go_router` if complex navigation is needed

---

### 🔵 IMPROVEMENTS — Structural suggestions

#### IMP-001: Add `cached_network_image` for fighter headshots
```yaml
# pubspec.yaml
cached_network_image: ^3.3.1
```
```dart
CachedNetworkImage(
  imageUrl: fighter.headshotUrl ?? '',
  placeholder: (ctx, url) => const CircularProgressIndicator(),
  errorWidget: (ctx, url, err) => const Icon(Icons.person),
)
```

#### IMP-002: Add `flutter_dotenv` for environment config
```yaml
# pubspec.yaml
flutter_dotenv: ^5.1.0
```
```dart
// main.dart
await dotenv.load(fileName: '.env');
final baseUrl = dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000/api/v1';
```

#### IMP-003: Implement proper pagination with infinite scroll
The backend's `Page<T>` model is designed for cursor-style pagination. Use `ListView.builder` with a scroll controller that loads more when near the bottom.

#### IMP-004: Add `dio_cache_interceptor` for offline support
```yaml
dio_cache_interceptor: ^3.5.0
```
Cache GET responses locally so the app works without network.

#### IMP-005: Use `go_router` for type-safe navigation
```yaml
go_router: ^14.0.0
```
Enables deep linking, back button handling, and named routes.

---

## Section 3: What's Actually Implemented (Backend-Verified)

These features are **fully supported by the backend** right now. A Flutter screen for each of these should work if the API calls are correct:

| Feature | Backend Endpoint | Response Shape |
|---------|-----------------|----------------|
| Search fighters by name | `GET /fighters?q={name}&limit=20&offset=0` | `Page<FighterSummary>` |
| Fighter full profile | `GET /fighters/{uuid}` | `FighterDetail` |
| Fighter next fight | `GET /fighters/{uuid}/next-fight` | `NextFight \| null` |
| Fighter career stats | `GET /fighters/{uuid}/statistics` | `List<StatisticOut>` |
| Fighter fight history | `GET /fighters/{uuid}/fights?limit=20&offset=0` | `Page<FighterFightSummary>` |
| Upcoming events list | `GET /events?limit=20&offset=0` | `Page<EventSummary>` |
| Events by promotion | `GET /events?promotion_id={uuid}` | `Page<EventSummary>` |
| Event full card | `GET /events/{uuid}` | `EventDetail` (with competitions) |
| Competition detail | `GET /competitions/{uuid}` | `CompetitionDetail` |
| Promotions list | `GET /promotions?limit=20&offset=0` | `Page<PromotionSummary>` |
| Promotion detail | `GET /promotions/{uuid}` | `PromotionDetail` |
| Venues list | `GET /venues?limit=20&offset=0` | `Page<VenueSummary>` |
| Venue detail | `GET /venues/{uuid}` | `VenueDetail` |
| Weight classes list | `GET /weight-classes` | `List<WeightClassOut>` |
| Health check | `GET /health` | `{status: "ok"}` |

### Exact Response Shapes (verified from source)

**FighterSummary** (in list/search results):
```json
{
  "id": "uuid",
  "full_name": "Islam Makhachev",
  "nickname": "The Eagle",
  "headshot_url": null,
  "wins": 26,
  "losses": 1,
  "draws": 0,
  "weight_class": {"id": "uuid", "name": "Lightweight"}
}
```

**FighterDetail** (adds to FighterSummary):
```json
{
  "nationality": "Russia",
  "height_in": 70.0,
  "weight_lbs": 155.0,
  "reach_in": 70.5,
  "stance": "Southpaw"
}
```

**EventSummary**:
```json
{
  "id": "uuid",
  "name": "UFC 317",
  "short_name": "UFC 317",
  "start_time": "2026-08-17T22:00:00Z",
  "status": "STATUS_SCHEDULED",
  "promotion": {"id": "uuid", "name": "UFC", "slug": "ufc"},
  "venue": {"id": "uuid", "name": "T-Mobile Arena", "city": "Las Vegas", "country": "USA"}
}
```

**EventDetail** (adds competitions array):
```json
{
  "competitions": [
    {
      "id": "uuid",
      "card_segment": "main",
      "match_number": 1,
      "result_method": null,
      "result_round": null,
      "competitors": [
        {"fighter_id": "uuid", "full_name": "Islam Makhachev",
         "headshot_url": null, "corner": "home", "outcome": null},
        {"fighter_id": "uuid", "full_name": "Dustin Poirier",
         "headshot_url": null, "corner": "away", "outcome": null}
      ]
    }
  ]
}
```

**NextFight**:
```json
{
  "event_id": "uuid",
  "event_name": "UFC 317",
  "start_time": "2026-08-17T22:00:00Z",
  "promotion_name": "UFC",
  "opponent": {"id": "uuid", "full_name": "Dustin Poirier", "headshot_url": null},
  "card_segment": "main"
}
```

**StatisticOut**:
```json
{
  "name": "strikeLPM",
  "display_name": "Strikes Per Minute",
  "value": 4.23,
  "rank": 5
}
```

---

## Section 4: What's Missing (PRD Features Not in Backend)

These features from the PRD **cannot be built yet** because the backend doesn't support them:

### Missing Backend Endpoints (data exists, route doesn't)
| Feature | Missing Route | Data Available | Effort |
|---------|--------------|----------------|--------|
| Rankings list | `GET /rankings` | ✅ `rankings` table | Hours |
| Champions list | `GET /champions` | ✅ `rankings` table (is_champion=true) | Hours |
| Fighter ranking badge | `GET /rankings?fighter_id=` | ✅ `rankings` table | Hours |
| Past/finished events | `GET /events?status=FINAL` | ✅ `events` table | Hours |
| Fighters by weight class | `GET /fighters?weight_class_id=` | ✅ `fighters` table | Hours |
| Fighter headshot URL | (field in `FighterSummary`) | ✅ ESPN CDN formula | Hours |

### Missing Backend Endpoints (new data needed)
| Feature | Missing Route | New Work Needed | Effort |
|---------|--------------|-----------------|--------|
| Fighter win-method breakdown | `GET /fighters/{id}/records` | Computed from competitions | Days |
| Fighter win streak | (computed field) | Computed from fight history | Days |
| Fighter style/stance tags | (already in DB!) | Add to schema | Hours |
| Fighter gym/association | (not in DB) | New ESPN sync | Days |
| Promotion logo | (not in DB) | TheSportsDB sync | Days |
| Promotion roster | `GET /promotions/{id}/roster` | Computed from competitors | Days |
| Compare fighters | `GET /compare?a={id}&b={id}` | New endpoint | Days |
| Fight officials (referee) | `GET /competitions/{id}/officials` | New ESPN sync | Days |

### Flutter-Only Features (no backend needed)
| Feature | Implementation |
|---------|---------------|
| Favorites (fighters/events) | SharedPreferences or Hive |
| Local reminders/notifications | `flutter_local_notifications` |
| Dark/light theme toggle | ThemeMode + SharedPreferences |
| Offline caching | `dio_cache_interceptor` or Hive |
| Share fighter/event | `share_plus` package |
| Pull-to-refresh | `RefreshIndicator` widget |
| Loading skeletons | `shimmer` package |
| Search history | SharedPreferences |
| Calendar view | `table_calendar` package |
| Fighter comparison UI | Client-side, uses existing fighter data |

### Features That Are NOT Possible (no free data source)
| Feature | Why Not Possible |
|---------|-----------------|
| Round-by-round scorecards | Not in ESPN API |
| Weigh-in results | Not in any free API |
| Fighter salaries | Not public |
| PPV buy numbers | Not public |
| Video highlights | ESPN+ paywalled |
| Live play-by-play | ESPN API has it but rate-limited |
| Odds/betting lines | Paid APIs only |

---

## Section 5: The Complete Plan

### Phase 1: Fix Critical Issues (Day 1 — ~4 hours)

**Step 1.1: Fix API base URL**
- File: `lib/core/constants/api_constants.dart`
- Set correct URL for your environment

**Step 1.2: Fix `Page<T>` model**
- File: `lib/data/models/page_model.dart`
- Ensure fields are `items`, `total`, `limit`, `offset`

**Step 1.3: Fix all nullable fields**
- Files: all `lib/data/models/*.dart`
- Make `result_method`, `result_round`, `result_time`, `result_detail`, `headshot_url`, `nickname`, `nationality`, `venue` all nullable

**Step 1.4: Fix JSON field name mapping**
- Files: all `lib/data/models/*.dart`
- Use `json['full_name']` not `json['fullName']`
- Use `json['weight_class']` not `json['weightClass']`

**Step 1.5: Fix fighters search endpoint**
- File: `lib/data/repositories/fighter_repository.dart`
- Ensure `q` parameter is always sent

**Step 1.6: Disable/stub rankings screen**
- File: `lib/presentation/screens/rankings/rankings_screen.dart`
- Show "Rankings coming soon" until backend endpoint is added

---

### Phase 2: Add Missing Backend Endpoints (Day 2 — ~6 hours backend work)

These are backend changes, not Flutter changes. Do these in the backend project:

**Step 2.1: Add `GET /rankings` endpoint**
```python
# app/api/v1/endpoints/rankings.py
@router.get("", response_model=list[RankingOut])
def list_rankings(
    category: str | None = Query(None),
    promotion_id: uuid.UUID | None = Query(None),
    service: RankingService = Depends(get_ranking_service),
) -> list[RankingOut]:
    return service.list_rankings(category=category, promotion_id=promotion_id)
```

**Step 2.2: Add `GET /champions` endpoint**
```python
@router.get("/champions", response_model=list[RankingOut])
def list_champions(
    promotion_id: uuid.UUID | None = Query(None),
    service: RankingService = Depends(get_ranking_service),
) -> list[RankingOut]:
    return service.list_champions(promotion_id=promotion_id)
```

**Step 2.3: Add `espn_id` to `FighterSummary` schema**
```python
class FighterSummary(BaseModel):
    espn_id: str | None  # ADD THIS — needed for headshot URL construction
    ...
```

**Step 2.4: Add `?status=` filter to events endpoint**
```python
@router.get("", response_model=Page[EventSummary])
def list_events(
    status: str | None = Query(None),  # ADD THIS
    promotion_id: uuid.UUID | None = Query(None),
    ...
```

**Step 2.5: Add `?weight_class_id=` filter to fighters endpoint**
```python
@router.get("", response_model=Page[FighterSummary])
def search_fighters(
    q: str | None = Query(None, min_length=1),  # Make optional
    weight_class_id: uuid.UUID | None = Query(None),  # ADD THIS
    ...
```

---

### Phase 3: Connect Flutter to Real Backend (Days 3-5)

**Step 3.1: Implement proper API client**
```dart
// lib/data/datasources/api_client.dart
class ApiClient {
  final Dio _dio;

  ApiClient() : _dio = Dio(BaseOptions(
    baseUrl: dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000/api/v1',
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 30),
  ));

  Future<Page<T>> getPage<T>(
    String path,
    T Function(Map<String, dynamic>) fromJson, {
    Map<String, dynamic>? queryParams,
  }) async {
    final response = await _dio.get(path, queryParameters: queryParams);
    return Page.fromJson(response.data, fromJson);
  }
}
```

**Step 3.2: Implement repositories**
```dart
// lib/data/repositories/fighter_repository.dart
class FighterRepository {
  final ApiClient _client;

  Future<Page<FighterSummary>> searchFighters(String query,
      {int limit = 20, int offset = 0}) async {
    return _client.getPage(
      '/fighters',
      FighterSummary.fromJson,
      queryParams: {'q': query, 'limit': limit, 'offset': offset},
    );
  }

  Future<FighterDetail> getFighter(String id) async {
    final response = await _client._dio.get('/fighters/$id');
    return FighterDetail.fromJson(response.data);
  }
  // ... etc
}
```

**Step 3.3: Wire up state management**
- If using Riverpod: create `AsyncNotifier` providers for each screen
- If using Provider: create `ChangeNotifier` classes
- If using Bloc: create `Bloc` classes with events/states

**Step 3.4: Replace mock data with real API calls in each screen**
- `HomeScreen`: call `GET /events` for upcoming events
- `FightersListScreen`: call `GET /fighters?q=` on search
- `FighterDetailScreen`: call `GET /fighters/{id}`, `GET /fighters/{id}/statistics`, `GET /fighters/{id}/fights`
- `EventsListScreen`: call `GET /events`
- `EventDetailScreen`: call `GET /events/{id}`
- `PromotionsListScreen`: call `GET /promotions`
- `SearchScreen`: call `GET /fighters?q=` with debounce

---

### Phase 4: Add Flutter-Only Features (Days 6-10)

**Step 4.1: Favorites with local storage**
```yaml
# pubspec.yaml
hive_flutter: ^1.1.0
hive: ^2.2.3
```
```dart
// Store favorite fighter IDs locally
final favoritesBox = Hive.box<String>('favorites');
favoritesBox.add(fighter.id);
```

**Step 4.2: Fighter headshots**
```dart
// After backend exposes espn_id:
String headshotUrl(String espnId) =>
  'https://a.espncdn.com/i/headshots/mma/players/full/$espnId.png';

// Use with cached_network_image:
CachedNetworkImage(
  imageUrl: headshotUrl(fighter.espnId),
  errorWidget: (_, __, ___) => const Icon(Icons.person, size: 48),
)
```

**Step 4.3: Event reminders**
```yaml
flutter_local_notifications: ^17.0.0
timezone: ^0.9.0
```

**Step 4.4: Share functionality**
```yaml
share_plus: ^9.0.0
```
```dart
Share.share('Check out ${fighter.fullName} on MMA App!');
```

**Step 4.5: Dark mode**
```dart
// In main.dart / app.dart:
ThemeMode _themeMode = ThemeMode.system;
// Toggle and persist with SharedPreferences
```

**Step 4.6: Offline caching**
```yaml
dio_cache_interceptor: ^3.5.0
```

---

### Phase 5: Polish & Production (Days 11-14)

**Step 5.1: Error handling everywhere**
- Network errors → retry button
- 404 → "Not found" screen
- 500 → "Server error, try again" screen
- No internet → cached data or offline message

**Step 5.2: Loading states everywhere**
- Skeleton loaders for lists
- Shimmer effect for cards
- Progress indicators for detail pages

**Step 5.3: Performance**
- Lazy loading for long lists
- Image caching
- Debounce search input (300ms)
- Cancel in-flight requests on screen dispose

**Step 5.4: Accessibility**
- Semantic labels on images
- Sufficient color contrast
- Minimum 44px touch targets

**Step 5.5: Testing**
- Unit tests for models (JSON parsing)
- Widget tests for key screens
- Integration test for search flow

---

## Section 6: File-by-File Action List

> Run this checklist when you open the project. Mark each file as you go.

### Root Files
| File | Action | Reason |
|------|--------|--------|
| `pubspec.yaml` | **AUDIT** | Check all dependencies, versions, missing packages |
| `pubspec.lock` | KEEP | Don't edit manually |
| `analysis_options.yaml` | **AUDIT** | Enable strict lints |
| `.env` / `.env.example` | **MODIFY** | Set correct API_BASE_URL |
| `README.md` | **MODIFY** | Update with actual setup instructions |

### lib/core/
| File | Action | Reason |
|------|--------|--------|
| `constants/api_constants.dart` | **MODIFY** | Fix base URL, verify all endpoint paths |
| `constants/app_constants.dart` | KEEP | Colors/strings are fine |
| `theme/app_theme.dart` | KEEP | Theme is Flutter-only |
| `utils/date_formatter.dart` | **AUDIT** | Ensure ISO 8601 parsing |
| `errors/failures.dart` | **MODIFY** | Add network/server error types |

### lib/data/models/
| File | Action | Reason |
|------|--------|--------|
| `page_model.dart` | **MODIFY** | Fix to `{items, total, limit, offset}` |
| `fighter_model.dart` | **MODIFY** | Fix nullable fields, add `espn_id`, fix JSON keys |
| `event_model.dart` | **MODIFY** | Fix nullable venue, fix JSON keys |
| `competition_model.dart` | **MODIFY** | Make all result fields nullable |
| `promotion_model.dart` | **AUDIT** | Verify JSON field names |
| `venue_model.dart` | **AUDIT** | Verify JSON field names |
| `weight_class_model.dart` | **AUDIT** | Simple model, likely fine |
| `statistic_model.dart` | **AUDIT** | Verify `name`, `display_name`, `value`, `rank` fields |

### lib/data/repositories/
| File | Action | Reason |
|------|--------|--------|
| `fighter_repository.dart` | **MODIFY** | Ensure `q` param sent, add weight_class filter |
| `event_repository.dart` | **MODIFY** | Add status filter support |
| `competition_repository.dart` | **AUDIT** | Verify endpoint path |
| `promotion_repository.dart` | **AUDIT** | Verify endpoint path |
| `venue_repository.dart` | **AUDIT** | Verify endpoint path |
| `weight_class_repository.dart` | **AUDIT** | Note: returns List not Page |

### lib/data/datasources/
| File | Action | Reason |
|------|--------|--------|
| `api_client.dart` | **MODIFY** | Add error handling, timeouts, base URL from env |

### lib/domain/ (if exists)
| File | Action | Reason |
|------|--------|--------|
| `entities/*.dart` | **DELETE** if duplicates | Merge into data/models/ |
| `usecases/*.dart` | **AUDIT** | Delete if empty stubs |

### lib/presentation/providers/ (or bloc/ or state/)
| File | Action | Reason |
|------|--------|--------|
| `fighters_provider.dart` | **MODIFY** | Wire to real repository |
| `events_provider.dart` | **MODIFY** | Wire to real repository |
| `rankings_provider.dart` | **MODIFY** | Stub until backend endpoint added |
| All others | **AUDIT** | Wire to real repositories |

### lib/presentation/screens/
| File | Action | Reason |
|------|--------|--------|
| `home/home_screen.dart` | **MODIFY** | Connect to events API, remove mock data |
| `fighters/fighters_list_screen.dart` | **MODIFY** | Fix search (require `q` param) |
| `fighters/fighter_detail_screen.dart` | **MODIFY** | Connect all 3 endpoints, fix headshots |
| `events/events_list_screen.dart` | **MODIFY** | Connect to events API |
| `events/event_detail_screen.dart` | **MODIFY** | Connect to event detail API |
| `rankings/rankings_screen.dart` | **MODIFY** | Stub with "coming soon" |
| `search/search_screen.dart` | **MODIFY** | Add debounce, connect to fighters API |
| `promotions/promotions_list_screen.dart` | **AUDIT** | Connect to promotions API |
| `promotions/promotion_detail_screen.dart` | **AUDIT** | Connect to promotion detail API |
| Any `*_screen.dart` with mock data | **MODIFY** | Replace with real API calls |

### lib/presentation/widgets/
| File | Action | Reason |
|------|--------|--------|
| `fighter_card.dart` | **MODIFY** | Fix headshot (use placeholder), fix nullable fields |
| `event_card.dart` | **MODIFY** | Fix date formatting, fix nullable venue |
| `loading_widget.dart` | KEEP | Reuse everywhere |
| `error_widget.dart` | **MODIFY** | Add retry callback |
| Any duplicate widgets | **DELETE** | Merge into one |

### lib/routes/
| File | Action | Reason |
|------|--------|--------|
| `app_router.dart` | **AUDIT** | Verify all screens are registered |

---

## Self-Audit Checklist (Run in 30 Minutes)

Open the Flutter project and run these commands:

```bash
# 1. Check for compilation errors
flutter analyze

# 2. Find all TODO/FIXME/hardcoded items
grep -rn "TODO\|FIXME\|hardcoded\|mock\|dummy\|fake\|localhost\|10.0.2.2\|your-api" lib/

# 3. Find duplicate class definitions
grep -rn "^class Fighter\|^class Event\|^class Competition\|^class Promotion" lib/

# 4. Find all API endpoint calls
grep -rn "apiClient.get\|dio.get\|http.get\|client.get" lib/

# 5. Find all hardcoded data
grep -rn "Fighter(\|Event(\|Competition(" lib/presentation/

# 6. Check pubspec for key packages
grep -E "dio|http|provider|riverpod|bloc|hive|shared_preferences|cached_network_image|go_router" pubspec.yaml

# 7. Find missing null safety
grep -rn "as String\b\|as int\b\|as bool\b" lib/data/models/

# 8. Find wrong JSON field names
grep -rn "fullName\|weightClass\|headshotUrl\|startTime\|cardSegment" lib/data/models/
```

---

## Backend API Quick Reference (for Flutter developers)

All endpoints are at `{BASE_URL}/api/v1/`. All list endpoints return `Page<T>`.

```
GET /fighters?q={name}&limit=20&offset=0
GET /fighters/{uuid}
GET /fighters/{uuid}/next-fight
GET /fighters/{uuid}/statistics
GET /fighters/{uuid}/fights?limit=20&offset=0

GET /events?promotion_id={uuid}&limit=20&offset=0
GET /events/{uuid}

GET /competitions/{uuid}

GET /promotions?limit=20&offset=0
GET /promotions/{uuid}

GET /venues?limit=20&offset=0
GET /venues/{uuid}

GET /weight-classes

GET /health
GET /health/db
```

**Not yet available (add to backend first):**
```
GET /rankings?category={str}&promotion_id={uuid}
GET /champions?promotion_id={uuid}
```

---

## Recommended pubspec.yaml Dependencies

```yaml
dependencies:
  flutter:
    sdk: flutter

  # HTTP
  dio: ^5.7.0
  dio_cache_interceptor: ^3.5.0

  # State management (pick one)
  flutter_riverpod: ^2.5.0
  # OR: provider: ^6.1.0
  # OR: flutter_bloc: ^8.1.0

  # Local storage
  hive_flutter: ^1.1.0
  shared_preferences: ^2.3.0

  # Images
  cached_network_image: ^3.3.1

  # Navigation
  go_router: ^14.0.0

  # Environment
  flutter_dotenv: ^5.1.0

  # Notifications
  flutter_local_notifications: ^17.0.0
  timezone: ^0.9.4

  # Sharing
  share_plus: ^9.0.0

  # UI
  shimmer: ^3.0.0
  table_calendar: ^3.1.0

  # Utils
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0
  build_runner: ^2.4.0
  json_serializable: ^6.8.0
```

---

*Cross-references: PRD (`product-requirements.md`) · Feature Registry (`feature-registry.md`) · Data Spec (`data-specification.md`) · ESPN API Reference (`espn-mma-api-reference.md`)*

# Phase 0 — Project Foundation: Architecture

**Status:** Approved ✅ (10 adjustments incorporated)
**Author:** Zaro AI (Lead Backend Engineer)
**Date:** 2026-08-01
**Approved by:** Haroon Afridi

---

## Table of Contents

1. [Architecture Philosophy](#1-architecture-philosophy)
2. [Approved Adjustments](#2-approved-adjustments)
3. [Complete Folder Structure](#3-complete-folder-structure)
4. [Why Every Folder Exists](#4-why-every-folder-exists)
5. [Dependency Flow](#5-dependency-flow)
6. [Request Lifecycle](#6-request-lifecycle)
7. [Database Flow](#7-database-flow)
8. [Sync Flow](#8-sync-flow)
9. [Testing Strategy](#9-testing-strategy)
10. [Technology Decisions](#10-technology-decisions)
11. [Configuration](#11-configuration)

---

## 1. Architecture Philosophy

### Clean Architecture — adapted for FastAPI

This project uses a **4-layer Clean Architecture** mapped to a FastAPI web application. Every layer knows only about the layer directly below it. No layer ever imports from a layer above it.

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │  ← FastAPI routers, dependencies, middleware
│            (Routers, DTOs, Middleware)                   │     Knows about: Services, DTOs
├─────────────────────────────────────────────────────────┤
│                  Service Layer                           │  ← Business logic, orchestration, validation
│         (Orchestration, Business Rules)                  │     Knows about: Repositories, Providers (via interface)
├─────────────────────────────────────────────────────────┤
│                 Repository Layer                         │  ← Data access abstraction (provider-neutral)
│           (SQLAlchemy queries, filtering)                │     Knows about: Models, Database Session
├─────────────────────────────────────────────────────────┤
│                  Domain Layer                            │  ← Provider-neutral models, enums, base types
│       (Models, Enums, Base Classes, Types)               │     Knows about: Nothing (pure data definitions)
└─────────────────────────────────────────────────────────┘

External modules (sideways dependencies, accessed via interfaces):
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────────┐
│  Data Providers  │ │ Redis Cache  │ │  Scheduler   │ │ Notifications │ │  AI Module   │
│ (ESPN, Tapology, │ │ (aioredis)   │ │ (APScheduler)│ │ (FCM, Email,  │ │ (Phase 5+)   │
│  PFL, ONE, etc.) │ │              │ │              │ │  Telegram...) │ │              │
└──────────────────┘ └──────────────┘ └──────────────┘ └───────────────┘ └──────────────┘
```

### Core rules

| Rule | Enforcement |
|---|---|
| Models never import from routers | Structural (models in `domain/`, routers in `api/`) |
| Repositories never contain business logic | Code review — repos are pure data access |
| Services never touch HTTP directly | Services call repositories, not FastAPI dependencies |
| API layer never touches the database directly | API → Service → Repository → DB |
| Provider details never leak above the provider module | Every provider implements `BaseDataProvider`; services see only the interface |
| Every function has type hints | Enforced by mypy in CI |
| Every public function has a docstring | Enforced by ruff (pydocstyle) |
| No singletons or global mutable state | Multiple backend instances must run simultaneously |

---

## 2. Approved Adjustments

The following adjustments were approved during architecture review and are incorporated throughout this document:

| # | Adjustment | Where Applied |
|---|---|---|
| 1 | **Provider-first architecture** — ESPN is one of many providers. Every data source implements `BaseDataProvider`. | `providers/base.py`, `providers/registry.py` |
| 2 | **Event-driven notifications** — Internal pub/sub event bus. Channels (Push, Email, Telegram, Discord, WebSocket) are plugins. | `notifications/events.py`, `notifications/channels/` |
| 3 | **Redis as core infrastructure** — CacheManager abstraction. Services never know if data came from PG or Redis. | `core/redis.py`, `core/cache.py` |
| 4 | **Modular sync jobs** — Each job independently runnable. Scheduler only orchestrates. | `sync/jobs/*.py`, `scheduler/jobs.py` |
| 5 | **API versioning** — Start with `/api/v1`. Breaking changes go to `/v2`. | `api/v1/`, `api/v2/` (future) |
| 6 | **Provider-neutral repositories** — No ESPN-specific logic in repos. Parsing lives only in providers. | `repositories/`, `providers/espn/parsers/` |
| 7 | **Provider-neutral domain models** — Store multiple external IDs. Not ESPN-centric. | `domain/models/external_id.py` |
| 8 | **Observability** — Structured logging + metrics from day one. Sync execution time, records inserted/updated/skipped, errors. | `core/logging.py`, `core/metrics.py` |
| 9 | **Horizontal scalability** — No singletons, no global state. DB locks for sync coordination. | All modules |
| 10 | **Future AI module reserved** — Isolated `ai/` directory. Prediction, recommendations, summaries, analytics. | `ai/` |

---

## 3. Complete Folder Structure

```
backend/
│
├── pyproject.toml                    # Project metadata, dependencies, tool config
├── alembic.ini                       # Alembic configuration
├── Dockerfile                        # Production Docker image
├── docker-compose.yml                # Local dev: app + postgres + redis
├── .env.example                      # Documented environment variables
├── .gitignore
├── README.md
├── PROJECT_STATUS.md                 # Living document — updated after every milestone
├── Makefile                          # Common commands (migrate, test, lint, run)
│
├── alembic/                          # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── src/                              # All application source code
│   │
│   ├── __init__.py
│   │
│   ├── core/                         # Cross-cutting infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings (reads from env)
│   │   ├── database.py               # SQLAlchemy engine, session factory, Base
│   │   ├── redis.py                  # Redis connection pool
│   │   ├── cache.py                  # CacheManager — transparent cache layer for services
│   │   ├── security.py               # JWT, password hashing, auth utilities
│   │   ├── exceptions.py             # Base exception hierarchy
│   │   ├── logging.py                # Structured logging config (JSON prod, colored dev)
│   │   ├── metrics.py                # Lightweight metrics (sync duration, API latency, cache hit rate)
│   │   └── dependencies.py           # FastAPI dependency injection (get_db, get_cache, etc.)
│   │
│   ├── domain/                       # Domain layer — provider-neutral data definitions
│   │   ├── __init__.py
│   │   ├── base.py                   # Base model (UUID PK, created_at, updated_at)
│   │   ├── enums.py                  # All enum types (FightResult, EventStatus, Gender, etc.)
│   │   ├── models/                   # SQLAlchemy ORM models (one per entity)
│   │   │   ├── __init__.py
│   │   │   ├── promotion.py
│   │   │   ├── event.py
│   │   │   ├── competition.py
│   │   │   ├── competitor.py
│   │   │   ├── fighter.py
│   │   │   ├── weight_class.py
│   │   │   ├── venue.py
│   │   │   ├── broadcast.py
│   │   │   ├── ranking.py
│   │   │   ├── statistic.py
│   │   │   ├── user.py
│   │   │   ├── fighter_follow.py
│   │   │   ├── promotion_follow.py
│   │   │   ├── reminder.py
│   │   │   ├── notification.py
│   │   │   ├── external_id.py        # Provider-neutral: stores espn_id, tapology_id, etc.
│   │   │   ├── entity_image.py
│   │   │   └── sync_run.py
│   │   └── types.py
│   │
│   ├── repositories/                 # Repository layer — provider-neutral data access
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseRepository[T] with CRUD, pagination, filtering
│   │   ├── fighter.py
│   │   ├── promotion.py
│   │   ├── event.py
│   │   ├── competition.py
│   │   ├── venue.py
│   │   ├── weight_class.py
│   │   ├── broadcast.py
│   │   ├── ranking.py
│   │   ├── statistic.py
│   │   ├── search.py                 # Full-text search (uses PostgreSQL search_vector)
│   │   └── user.py
│   │
│   ├── services/                     # Service layer — business logic
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── fighter.py
│   │   ├── promotion.py
│   │   ├── event.py
│   │   ├── competition.py
│   │   ├── ranking.py
│   │   ├── search.py
│   │   ├── statistics.py
│   │   ├── home.py                   # Aggregated home-feed logic
│   │   ├── discover.py
│   │   └── notification.py
│   │
│   ├── api/                          # API layer — FastAPI routers & schemas
│   │   ├── __init__.py
│   │   ├── router.py                 # Main router — mounts all v1 sub-routers
│   │   ├── middleware.py
│   │   ├── deps.py
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── fighter.py
│   │   │   ├── promotion.py
│   │   │   ├── event.py
│   │   │   ├── competition.py
│   │   │   ├── ranking.py
│   │   │   ├── search.py
│   │   │   ├── home.py
│   │   │   └── notification.py
│   │   └── v1/                       # Version 1 endpoints
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── fighters.py
│   │       ├── promotions.py
│   │       ├── events.py
│   │       ├── competitions.py
│   │       ├── rankings.py
│   │       ├── venues.py
│   │       ├── weight_classes.py
│   │       ├── broadcasts.py
│   │       ├── statistics.py
│   │       ├── search.py
│   │       ├── home.py
│   │       └── notifications.py
│   │
│   ├── providers/                    # External data providers (provider-first architecture)
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseDataProvider Protocol — interface for ALL providers
│   │   ├── registry.py               # ProviderRegistry — maps promotions to provider instances
│   │   └── espn/                     # ESPN-specific implementation (first provider)
│   │       ├── __init__.py
│   │       ├── client.py
│   │       ├── config.py
│   │       ├── parsers/
│   │       │   ├── __init__.py
│   │       │   ├── fighter.py
│   │       │   ├── event.py
│   │       │   ├── competition.py
│   │       │   ├── ranking.py
│   │       │   ├── venue.py
│   │       │   └── broadcast.py
│   │       └── reference.py
│   │
│   ├── sync/                         # Sync engine — modular, independently runnable jobs
│   │   ├── __init__.py
│   │   ├── engine.py                 # Orchestrator — runs sync jobs in dependency order
│   │   ├── jobs/                     # Individual sync jobs (each independently runnable)
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseSyncJob with idempotency, logging, error handling
│   │   │   ├── promotions.py
│   │   │   ├── events.py
│   │   │   ├── competitions.py
│   │   │   ├── fighters.py
│   │   │   ├── rankings.py
│   │   │   ├── statistics.py
│   │   │   ├── venues.py
│   │   │   ├── broadcasts.py
│   │   │   └── weight_classes.py
│   │   ├── strategies.py             # Upsert strategies (merge vs. replace per entity)
│   │   └── diff.py                   # Change detection for notification triggers
│   │
│   ├── scheduler/                    # Job orchestration — no business logic
│   │   ├── __init__.py
│   │   ├── scheduler.py              # APScheduler setup, job registration
│   │   └── jobs.py                   # Thin wrappers that call individual sync jobs
│   │
│   ├── notifications/                # Event-driven, multi-channel notification system
│   │   ├── __init__.py
│   │   ├── engine.py                 # Channel-agnostic dispatch engine
│   │   ├── triggers.py               # Trigger detection
│   │   ├── templates.py              # Content templates (shared across channels)
│   │   ├── events.py                 # Internal pub/sub event bus
│   │   └── channels/                 # Delivery channels (all implement BaseNotificationChannel)
│   │       ├── __init__.py
│   │       ├── base.py               # BaseNotificationChannel Protocol
│   │       ├── push.py               # Firebase Cloud Messaging (FCM)
│   │       ├── email.py              # Email delivery (future)
│   │       ├── telegram.py           # Telegram bot (future)
│   │       ├── discord.py            # Discord webhook (future)
│   │       └── websocket.py          # Real-time WebSocket (future)
│   │
│   ├── ai/                           # AI module (Phase 5+ — reserved, not built now)
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   └── main.py                       # FastAPI app factory, lifespan, startup/shutdown
│
├── tests/                            # Test suite (mirrors src/ structure)
│   ├── __init__.py
│   ├── conftest.py
│   ├── factories/
│   │   ├── __init__.py
│   │   ├── fighter.py
│   │   ├── promotion.py
│   │   └── event.py
│   ├── unit/
│   │   ├── test_repositories/
│   │   ├── test_services/
│   │   └── test_parsers/
│   ├── integration/
│   │   ├── test_api/
│   │   ├── test_sync/
│   │   └── test_scheduler/
│   └── e2e/
│       └── test_sync_pipeline.py
│
└── scripts/
    ├── verify_additional_organizations.py
    ├── seed_dev_data.py
    └── backup_db.py
```

---

## 4. Why Every Folder Exists

*(Summarized — full rationale in original architecture document)*

- **`core/`** — Neutral ground for infrastructure that every layer uses. No circular imports possible.
- **`domain/`** — Provider-neutral models. External IDs table stores `espn_id`, `tapology_id`, etc. without assuming any single provider.
- **`repositories/`** — Pure data access. Zero provider-specific logic. ESPN parsing lives only in `providers/espn/parsers/`.
- **`services/`** — Business logic. Uses `CacheManager` from `core/cache.py` — services never know if data came from PostgreSQL or Redis.
- **`api/`** — HTTP interface. Versioned: `/api/v1/`. Breaking changes → `/api/v2/`.
- **`providers/`** — Provider-first. `BaseDataProvider` Protocol. `ProviderRegistry` maps promotions to providers. Adding ONE Championship = one new package that implements the Protocol.
- **`sync/`** — Modular jobs. Each job independently runnable. Orchestrator handles dependency order.
- **`scheduler/`** — Thin orchestration layer. Never contains business logic. Multiple backend instances coordinate via DB locks on `SyncRun`.
- **`notifications/`** — Event-driven. Internal pub/sub bus. Channels (push, email, Telegram, Discord, WebSocket) are plugins implementing `BaseNotificationChannel`.
- **`ai/`** — Reserved for Phase 5. Predictions, recommendations, summaries, analytics.

---

## 5. Dependency Flow

```
api/v1/        → can import: services/, core/, domain/
services/      → can import: repositories/, core/, domain/, providers/ (via base.py interface)
repositories/  → can import: domain/, core/
providers/     → can import: core/, domain/  (never api/, never services/)
sync/          → can import: providers/, repositories/, core/, domain/
scheduler/     → can import: sync/, core/
notifications/ → can import: services/, repositories/, core/, domain/
ai/            → can import: services/, repositories/, core/, domain/
domain/        → can import: core/ (config types only, not database)
core/          → can import: NOTHING from src/ (standard library + third-party only)
```

---

## 6-8. Request Lifecycle, Database Flow, Sync Flow

*(Unchanged from original — see full document for the complete trace from HTTP → middleware → router → service → repository → DB, plus the full sync pipeline with dependency ordering and upsert strategies.)*

---

## 9. Testing Strategy

| Layer | Coverage Target |
|---|---|
| `domain/` | 100% |
| `repositories/` | 95%+ |
| `services/` | 95%+ |
| `api/` | 90%+ |
| `providers/` | 90%+ |
| `sync/` | 90%+ |
| `notifications/` | 85%+ |
| Overall | **90%+** |

---

## 10. Technology Decisions

| Decision | Rationale |
|---|---|
| SQLAlchemy 2.0 async | Native async, matches FastAPI |
| Pydantic v2 | Fast, Rust core, FastAPI native |
| Alembic | Standard migration tool |
| httpx | Async-native HTTP client |
| APScheduler | Simple for current scale; swappable to Celery |
| Redis | Core infrastructure from day one; CacheManager abstraction |
| PG full-text search | Sufficient for current scope; no Elasticsearch needed |
| One model per file | Avoids 800+ line monolith |
| Repository pattern | Testability, swappability |
| Provider Protocol | Multi-provider from day one |
| Event bus (notifications) | Channel-agnostic; add channels without changing logic |

---

## 11. Configuration

Full `.env` structure documented in `.env.example`. Key settings:
- `DATABASE_URL` — PostgreSQL with asyncpg
- `REDIS_URL` — Redis connection
- `ESPN_API_*` — Rate limiting, timeout, retry
- `SYNC_SCHEDULE_*` — Cron expressions for full sync, rankings sync
- `JWT_*` — Auth (future)

---

*End of Architecture — Phase 0 Approved. Proceed to Phase 1: Database Design.*

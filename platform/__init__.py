"""
MMA Data Platform — Enterprise connector framework, scheduler, data lake,
normalization, identity resolution, and validation engine.

This package sits BETWEEN the raw data providers and the application layer.
Sources: ESPN, UFCStats, TheSportsDB, Wikipedia, Sherdog, Tapology, Official UFC, etc.

Architecture:
    ┌──────────────────────────────────────────────────────────┐
    │                    Scheduler (19.2)                       │
    │   Worker pools · Priority queues · Dead letters           │
    └────────────────────────┬─────────────────────────────────┘
                             │
    ┌────────────────────────┴─────────────────────────────────┐
    │              Connector Framework (19.1)                    │
    │   BaseConnector · Registry · Manager · Health             │
    └────────────────────────┬─────────────────────────────────┘
                             │
    ┌────────────────────────┴─────────────────────────────────┐
    │                 Raw Data Lake (19.3)                       │
    │   Raw store · Compression · Versioning · Replay            │
    └────────────────────────┬─────────────────────────────────┘
                             │
    ┌────────────────────────┴─────────────────────────────────┐
    │              Normalization Engine (19.4)                   │
    │   Canonical models · Mappers · Transformers                │
    └────────────────────────┬─────────────────────────────────┘
                             │
    ┌────────────────────────┴─────────────────────────────────┐
    │           Identity Resolution (19.5)                       │
    │   Similarity · Merge · Confidence · Deduplication          │
    └────────────────────────┬─────────────────────────────────┘
                             │
    ┌────────────────────────┴─────────────────────────────────┐
    │              Validation Engine (19.6)                      │
    │   Rules · Severity · Auto-fix · Quality dashboard          │
    └────────────────────────┬─────────────────────────────────┘
                             │
                    Canonical MMA Database
"""

__version__ = "1.0.0"
__all__ = [
    "connectors", "scheduler", "scheduler_jobs", "datalake",
    "normalization", "identity", "resolution", "quality",
    "trust", "lineage", "validation", "hardening", "integration",
]

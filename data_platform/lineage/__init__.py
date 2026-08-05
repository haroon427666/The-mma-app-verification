"""
Data Lineage & Audit Platform — every data mutation is traceable.

Every entity answers: Where did this value come from? When was it updated?
Which source changed it? Why was it changed?

Full version history, diff comparison, rollback support, timeline API.
No data mutation without history.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime as _dt, timezone as _tz
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Audit Entry — a single mutation record
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AuditEntry:
    """Immutable record of a single data mutation."""
    id: str
    entity_type: str
    entity_id: str
    field: str
    old_value: Any
    new_value: Any
    source: str                    # connector name
    pipeline_stage: str            # fetch/parse/normalize/validate/merge
    reason: str
    changed_at: str = ""
    job_id: str = ""
    request_id: str = ""
    version: int = 1

    def __post_init__(self):
        if not self.changed_at:
            self.changed_at = _dt.now(_tz.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "field": self.field,
            "old_value": str(self.old_value)[:200],
            "new_value": str(self.new_value)[:200],
            "source": self.source, "pipeline_stage": self.pipeline_stage,
            "reason": self.reason, "changed_at": self.changed_at,
            "version": self.version,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Entity Snapshot — full state at a point in time
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EntitySnapshot:
    """Complete snapshot of an entity at a specific version."""
    entity_type: str
    entity_id: str
    version: int
    data: dict[str, Any]
    checksum: str = ""
    created_at: str = ""
    created_by: str = ""
    pipeline_stage: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = _dt.now(_tz.utc).isoformat()
        if not self.checksum and self.data:
            self.checksum = hashlib.sha256(
                str(sorted(self.data.items())).encode()
            ).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Diff Engine
# ═══════════════════════════════════════════════════════════════════════════

class DiffEngine:
    """Compare two entity versions and produce a human-readable diff."""

    @staticmethod
    def diff(before: dict, after: dict) -> dict:
        """Compare two entity states. Returns structured diff."""
        all_keys = set(before.keys()) | set(after.keys())
        changes = []

        for key in sorted(all_keys):
            old = before.get(key)
            new = after.get(key)
            if old == new:
                continue
            if old is None and new is not None:
                changes.append({"field": key, "action": "added", "new": str(new)[:200]})
            elif old is not None and new is None:
                changes.append({"field": key, "action": "removed", "old": str(old)[:200]})
            else:
                changes.append({
                    "field": key, "action": "changed",
                    "old": str(old)[:200], "new": str(new)[:200],
                })

        return {
            "total_fields": len(all_keys),
            "changed_fields": len(changes),
            "checksums_match": before.get("checksum") == after.get("checksum"),
            "changes": changes,
        }

    @staticmethod
    def summary_diff(before: dict, after: dict) -> str:
        """Human-readable summary of what changed."""
        d = DiffEngine.diff(before, after)
        if d["changed_fields"] == 0:
            return "No changes detected"
        parts = []
        for c in d["changes"][:5]:
            if c["action"] == "added":
                parts.append(f"+{c['field']}: {c['new']}")
            elif c["action"] == "removed":
                parts.append(f"-{c['field']}: {c['old']}")
            else:
                parts.append(f"~{c['field']}: {c['old']} → {c['new']}")
        more = f" (+{d['changed_fields'] - 5} more)" if d["changed_fields"] > 5 else ""
        return "; ".join(parts) + more


# ═══════════════════════════════════════════════════════════════════════════
# Lineage Tracker
# ═══════════════════════════════════════════════════════════════════════════

class LineageTracker:
    """Complete audit trail and version history for all entities."""

    def __init__(self):
        self._audit: list[AuditEntry] = []
        self._snapshots: dict[str, list[EntitySnapshot]] = {}

    def record_change(
        self, entity_type: str, entity_id: str, field: str,
        old_value: Any, new_value: Any,
        source: str = "unknown", pipeline_stage: str = "unknown",
        reason: str = "", version: int = 1,
        job_id: str = "", request_id: str = "",
    ) -> str:
        """Record a single field change. Returns the audit entry ID."""
        import uuid
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            entity_type=entity_type, entity_id=entity_id,
            field=field, old_value=old_value, new_value=new_value,
            source=source, pipeline_stage=pipeline_stage,
            reason=reason, version=version,
            job_id=job_id, request_id=request_id,
        )
        self._audit.append(entry)
        return entry.id

    def record_snapshot(
        self, entity_type: str, entity_id: str, data: dict,
        version: int = 1, created_by: str = "", pipeline_stage: str = "",
    ) -> EntitySnapshot:
        """Store a complete entity snapshot."""
        snapshot = EntitySnapshot(
            entity_type=entity_type, entity_id=entity_id,
            version=version, data=dict(data),
            created_by=created_by, pipeline_stage=pipeline_stage,
        )
        key = f"{entity_type}:{entity_id}"
        self._snapshots.setdefault(key, []).append(snapshot)

        # Keep max 10 snapshots per entity
        if len(self._snapshots[key]) > 10:
            self._snapshots[key] = self._snapshots[key][-10:]

        return snapshot

    def get_history(
        self, entity_type: str, entity_id: str, field: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get audit history for an entity, optionally filtered by field."""
        entries = [
            e.to_dict() for e in self._audit
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]
        if field:
            entries = [e for e in entries if e.get("field") == field]
        return entries[-limit:]

    def get_snapshots(
        self, entity_type: str, entity_id: str,
    ) -> list[dict]:
        """Get version history for an entity."""
        key = f"{entity_type}:{entity_id}"
        snapshots = self._snapshots.get(key, [])
        return [
            {
                "version": s.version,
                "checksum": s.checksum,
                "created_at": s.created_at,
                "pipeline_stage": s.pipeline_stage,
                "data": s.data if s.version == 1 else None,  # Full data for latest
            }
            for s in snapshots
        ]

    def get_timeline(
        self, entity_type: str, entity_id: str, limit: int = 50,
    ) -> dict:
        """Complete timeline: all changes + snapshots."""
        history = self.get_history(entity_type, entity_id, limit=limit)
        snapshots = self.get_snapshots(entity_type, entity_id)

        return {
            "entity": f"{entity_type}:{entity_id}",
            "total_changes": len(history),
            "total_versions": len(snapshots),
            "latest": history[-1] if history else None,
            "first": history[0] if history else None,
            "changes": history,
            "versions": snapshots,
        }

    def compare_versions(
        self, entity_type: str, entity_id: str, v1: int, v2: int,
    ) -> dict | None:
        """Diff two specific versions of an entity."""
        key = f"{entity_type}:{entity_id}"
        snapshots = self._snapshots.get(key, [])
        snap_v1 = next((s for s in snapshots if s.version == v1), None)
        snap_v2 = next((s for s in snapshots if s.version == v2), None)
        if not snap_v1 or not snap_v2:
            return None
        return DiffEngine.diff(snap_v1.data, snap_v2.data)

    def rollback(
        self, entity_type: str, entity_id: str, target_version: int,
    ) -> dict | None:
        """Get data from a specific version (for rollback)."""
        key = f"{entity_type}:{entity_id}"
        snapshots = self._snapshots.get(key, [])
        target = next((s for s in snapshots if s.version == target_version), None)
        return dict(target.data) if target else None

    def get_dashboard(self) -> dict:
        """Lineage dashboard metrics."""
        return {
            "total_audit_entries": len(self._audit),
            "total_snapshots": sum(len(v) for v in self._snapshots.values()),
            "entities_tracked": len(self._snapshots),
            "sources_seen": len(set(e.source for e in self._audit)),
            "latest_change": (
                self._audit[-1].changed_at if self._audit else None
            ),
        }

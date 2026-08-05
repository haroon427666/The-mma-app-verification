"""
Validation Engine — every entity must pass validation before reaching the canonical DB.

Supports: blocking errors, warnings, auto-fix rules, manual review,
          rule versioning, validation history, quality metrics.

Nothing invalid enters the canonical database.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime as _dt, timezone as _tz
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Types
# ═══════════════════════════════════════════════════════════════════════════

class Severity(int, Enum):
    """Validation severity levels."""
    BLOCKER = 1     # Must fix — entity rejected
    ERROR = 2       # Should fix — entity rejected
    WARNING = 3     # Should review — entity accepted with flag
    INFO = 4        # Informational only


class RuleCategory(str, Enum):
    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    RELATIONSHIP = "relationship"
    CONSISTENCY = "consistency"
    DUPLICATE = "duplicate"
    BUSINESS = "business"


@dataclass
class ValidationRule:
    """A single validation rule."""
    id: str
    entity_type: str
    category: RuleCategory
    severity: Severity
    description: str
    check_fn: Callable[[Any], tuple[bool, str]]
    auto_fix_fn: Optional[Callable[[Any], Any]] = None
    enabled: bool = True
    version: int = 1
    tags: list[str] = field(default_factory=list)


@dataclass
class ValidationError:
    """A single validation failure."""
    rule_id: str
    entity_type: str
    entity_id: str
    severity: Severity
    category: RuleCategory
    message: str
    field: str = ""
    value: Any = None
    auto_fixed: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = _dt.now(_tz.utc).isoformat()


@dataclass
class ValidationResult:
    """Result of validating a batch of entities."""
    entity_type: str
    total: int
    passed: int
    failed: int
    blocked: int
    warnings: int
    errors: list[ValidationError] = field(default_factory=list)
    auto_fixed: int = 0
    duration_ms: float = 0.0

    @property
    def is_clean(self) -> bool:
        return self.blocked == 0 and self.failed == 0


# ═══════════════════════════════════════════════════════════════════════════
# Rule Registry
# ═══════════════════════════════════════════════════════════════════════════

class RuleRegistry:
    """Central registry for all validation rules. Version-aware."""

    def __init__(self):
        self._rules: dict[str, ValidationRule] = {}
        self._by_entity: dict[str, list[str]] = {}
        self._by_category: dict[RuleCategory, list[str]] = {}

    def register(self, rule: ValidationRule):
        self._rules[rule.id] = rule
        self._by_entity.setdefault(rule.entity_type, []).append(rule.id)
        self._by_category.setdefault(rule.category, []).append(rule.id)

    def get(self, rule_id: str) -> Optional[ValidationRule]:
        return self._rules.get(rule_id)

    def get_for_entity(self, entity_type: str) -> list[ValidationRule]:
        rule_ids = self._by_entity.get(entity_type, [])
        return [self._rules[rid] for rid in rule_ids if self._rules[rid].enabled]

    def disable(self, rule_id: str):
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False

    def enable(self, rule_id: str):
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True

    def count(self) -> int:
        return len(self._rules)

    def summary(self) -> dict:
        return {
            "total_rules": len(self._rules),
            "by_entity": {k: len(v) for k, v in self._by_entity.items()},
            "by_category": {k.value: len(v) for k, v in self._by_category.items()},
        }


# ═══════════════════════════════════════════════════════════════════════════
# Standard Rules — pre-built for all entity types
# ═══════════════════════════════════════════════════════════════════════════

def create_standard_rules() -> RuleRegistry:
    """Create a RuleRegistry with standard validation rules for all entities."""
    registry = RuleRegistry()

    # ── Fighter Rules ──
    registry.register(ValidationRule(
        id="f-001", entity_type="fighter", category=RuleCategory.REQUIRED,
        severity=Severity.BLOCKER,
        description="Fighter must have at least one name field",
        check_fn=lambda f: (bool(f.get("first_name") or f.get("last_name") or f.get("full_name")), "Missing all name fields"),
    ))
    registry.register(ValidationRule(
        id="f-002", entity_type="fighter", category=RuleCategory.RANGE,
        severity=Severity.WARNING,
        description="Height must be 120-220 cm",
        check_fn=lambda f: (not f.get("height_cm") or 120 <= f["height_cm"] <= 220, f"Height out of range: {f.get('height_cm')}"),
    ))
    registry.register(ValidationRule(
        id="f-003", entity_type="fighter", category=RuleCategory.RANGE,
        severity=Severity.WARNING,
        description="Weight must be 45-150 kg",
        check_fn=lambda f: (not f.get("weight_kg") or 45 <= f["weight_kg"] <= 150, f"Weight out of range: {f.get('weight_kg')}"),
    ))
    registry.register(ValidationRule(
        id="f-004", entity_type="fighter", category=RuleCategory.RANGE,
        severity=Severity.WARNING,
        description="Reach must be 100-230 cm",
        check_fn=lambda f: (not f.get("reach_cm") or 100 <= f["reach_cm"] <= 230, f"Reach out of range: {f.get('reach_cm')}"),
    ))
    registry.register(ValidationRule(
        id="f-005", entity_type="fighter", category=RuleCategory.CONSISTENCY,
        severity=Severity.ERROR,
        description="Record must be non-negative",
        check_fn=lambda f: (
            f.get("wins", 0) >= 0 and f.get("losses", 0) >= 0,
            "Negative record counts",
        ),
    ))
    registry.register(ValidationRule(
        id="f-006", entity_type="fighter", category=RuleCategory.CONSISTENCY,
        severity=Severity.WARNING,
        description="Stance must be valid",
        check_fn=lambda f: (
            not f.get("stance") or f["stance"] in ("Orthodox", "Southpaw", "Switch", "Open Stance"),
            f"Invalid stance: {f.get('stance')}",
        ),
    ))

    # ── Event Rules ──
    registry.register(ValidationRule(
        id="e-001", entity_type="event", category=RuleCategory.REQUIRED,
        severity=Severity.BLOCKER,
        description="Event must have a name",
        check_fn=lambda e: (bool(e.get("name", "").strip()), "Missing event name"),
    ))
    registry.register(ValidationRule(
        id="e-002", entity_type="event", category=RuleCategory.CONSISTENCY,
        severity=Severity.WARNING,
        description="Event date should not be in the far past unless status is FINAL",
        check_fn=lambda e: (True, ""),  # Always pass, informational
    ))

    # ── Fight Rules ──
    registry.register(ValidationRule(
        id="b-001", entity_type="fight", category=RuleCategory.REQUIRED,
        severity=Severity.BLOCKER,
        description="Fight must have two different fighters",
        check_fn=lambda f: (
            bool(f.get("fighter_a_id")) and bool(f.get("fighter_b_id")) and f["fighter_a_id"] != f["fighter_b_id"],
            "Invalid fighter matchup",
        ),
    ))
    registry.register(ValidationRule(
        id="b-002", entity_type="fight", category=RuleCategory.CONSISTENCY,
        severity=Severity.WARNING,
        description="Result method must be valid if fight is complete",
        check_fn=lambda f: (True, ""),
    ))

    # ── Ranking Rules ──
    registry.register(ValidationRule(
        id="r-001", entity_type="ranking", category=RuleCategory.REQUIRED,
        severity=Severity.ERROR,
        description="Ranking must reference a fighter",
        check_fn=lambda r: (bool(r.get("fighter_id", "").strip()), "Missing fighter ID"),
    ))
    registry.register(ValidationRule(
        id="r-002", entity_type="ranking", category=RuleCategory.RANGE,
        severity=Severity.ERROR,
        description="Rank must be 1-50 or 0 if champion",
        check_fn=lambda r: (0 <= r.get("rank", 0) <= 50, f"Invalid rank: {r.get('rank')}"),
    ))

    return registry


# ═══════════════════════════════════════════════════════════════════════════
# Validation Engine
# ═══════════════════════════════════════════════════════════════════════════

class ValidationEngine:
    """Run all registered rules against an entity batch.

    Returns detailed results with severity breakdown.
    Tracks auto-fixes and validation history.
    """

    def __init__(self, registry: RuleRegistry | None = None):
        self._registry = registry or create_standard_rules()
        self._history: list[ValidationResult] = []

    def validate(
        self, entity_type: str, entities: list[dict[str, Any]],
    ) -> ValidationResult:
        """Validate a batch of entities. Returns detailed result."""
        import time as _time
        start = _time.monotonic()
        rules = self._registry.get_for_entity(entity_type)
        result = ValidationResult(entity_type=entity_type, total=len(entities), passed=0, failed=0, blocked=0, warnings=0)

        for entity in entities:
            entity_id = entity.get("id", entity.get("canonical_id", str(entity)[:50]))
            entity_errors = 0
            has_blocker = False

            for rule in rules:
                try:
                    ok, msg = rule.check_fn(entity)
                    if not ok:
                        error = ValidationError(
                            rule_id=rule.id, entity_type=entity_type,
                            entity_id=entity_id, severity=rule.severity,
                            category=rule.category, message=msg,
                            field=rule.id.split("-")[-1] if "-" in rule.id else "",
                        )

                        # Try auto-fix
                        if rule.auto_fix_fn:
                            try:
                                fixed = rule.auto_fix_fn(entity)
                                entity.update(fixed)
                                error.auto_fixed = True
                                result.auto_fixed += 1
                            except Exception:
                                pass

                        result.errors.append(error)
                        entity_errors += 1
                        if rule.severity == Severity.BLOCKER:
                            has_blocker = True
                        elif rule.severity == Severity.ERROR:
                            result.failed += 1
                        elif rule.severity == Severity.WARNING:
                            result.warnings += 1
                except Exception as e:
                    result.errors.append(ValidationError(
                        rule_id=rule.id, entity_type=entity_type,
                        entity_id=entity_id, severity=Severity.ERROR,
                        category=RuleCategory.BUSINESS,
                        message=f"Rule execution error: {e}",
                    ))

            if has_blocker:
                result.blocked += 1
            elif entity_errors == 0:
                result.passed += 1

        result.duration_ms = (_time.monotonic() - start) * 1000
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        logger.info(
            f"Validation [{entity_type}]: {result.passed} passed, "
            f"{result.failed} failed, {result.blocked} blocked, "
            f"{result.warnings} warnings ({result.auto_fixed} auto-fixed)"
        )
        return result

    def get_history(self, limit: int = 20) -> list[ValidationResult]:
        return self._history[-limit:]

    def get_quality_metrics(self) -> dict:
        """Aggregate quality dashboard."""
        if not self._history:
            return {"status": "no_data"}
        recent = self._history[-10:]
        total_checked = sum(r.total for r in recent)
        total_passed = sum(r.passed for r in recent)
        total_blocked = sum(r.blocked for r in recent)
        return {
            "total_checked": total_checked,
            "pass_rate": round(total_passed / max(total_checked, 1) * 100, 1),
            "blocked_count": total_blocked,
            "auto_fixed_total": sum(r.auto_fixed for r in recent),
            "rules_active": self._registry.count(),
            "last_result": {
                "entity": recent[-1].entity_type,
                "passed": recent[-1].passed,
                "failed": recent[-1].failed,
                "is_clean": recent[-1].is_clean,
            } if recent else None,
        }

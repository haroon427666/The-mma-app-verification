"""
Dependency graph — topological sort, cycle detection, and plan validation.

Every SyncJob declares its dependencies via `depends_on: list[EntityType]`.
This module:
1. Builds a directed acyclic graph from job declarations
2. Produces a valid execution order (topological sort via Kahn's algorithm)
3. Validates that a SyncPlan's order satisfies all job dependencies
4. Detects cycles (invalid: event → competition → event)

FK rationale for every dependency is documented in the class docstring.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field

from src.sync.job import SyncJob
from src.sync.plan import SyncPlan
from src.sync.types import EntityType


# ── Dependency declarations ───────────────────────────────────────────────────
#
# Each entry: (entity → depends_on)
# Rationale is inline — every edge traces back to a DB foreign key or
# provider-level prerequisite (e.g. rankings need fighters to exist).

DEPENDENCY_MAP: dict[EntityType, list[EntityType]] = {
    # ── Root entities (no dependencies) ────────────────────────────────────
    EntityType.PROMOTION: [],
    #   No FKs. Root of the graph.

    EntityType.VENUE: [],
    #   No FKs. Venues can exist independently.
    #   NOTE: Venues are extracted from embedded competition data during event
    #   sync. A standalone Venue job fetches resolved $refs from stored event data
    #   rather than having its own dedicated provider endpoint.

    EntityType.WEIGHT_CLASS: [],
    #   No FKs. Weight classes are extracted from inline data in athlete and
    #   competition responses. No dedicated provider endpoint.

    # ── Fighter ────────────────────────────────────────────────────────────
    EntityType.FIGHTER: [
        EntityType.WEIGHT_CLASS,
    ],
    #   FK: fighters.weight_class_id → weight_classes.id (NULLABLE)
    #   Weight classes should exist before fighters reference them.
    #   Practically: fighter sync extracts weight classes from inline data,
    #   so the WeightClass job runs first to ensure FK targets exist.

    # ── Event ──────────────────────────────────────────────────────────────
    EntityType.EVENT: [
        EntityType.PROMOTION,
        EntityType.VENUE,
    ],
    #   FK: events.promotion_id → promotions.id (NOT NULL)
    #   FK: events.venue_id → venues.id (NULLABLE)
    #   Promotions MUST exist. Venues SHOULD exist.

    # ── Competition ────────────────────────────────────────────────────────
    EntityType.COMPETITION: [
        EntityType.EVENT,
        EntityType.FIGHTER,
        EntityType.WEIGHT_CLASS,
    ],
    #   FK: competitions.event_id → events.id (NOT NULL)
    #   FK: competitions.weight_class_id → weight_classes.id (NULLABLE)
    #   Competitors reference fighters: competitors.fighter_id → fighters.id
    #   Events MUST exist. Fighters MUST exist (competitor rows reference them).
    #   Weight classes SHOULD exist.

    # ── Broadcast ──────────────────────────────────────────────────────────
    EntityType.BROADCAST: [
        EntityType.EVENT,
    ],
    #   FK: broadcasts.event_id → events.id (NOT NULL)
    #   Events MUST exist.

    # ── Statistic ──────────────────────────────────────────────────────────
    EntityType.STATISTIC: [
        EntityType.FIGHTER,
        EntityType.COMPETITION,
    ],
    #   FK: statistics.competitor_id → competitors.id (NOT NULL)
    #   Competitors reference fighters + competitions.
    #   Fighters and Competitions MUST exist before statistics can be attached
    #   to their competitor rows.

    # ── Ranking ────────────────────────────────────────────────────────────
    EntityType.RANKING: [
        EntityType.PROMOTION,
        EntityType.FIGHTER,
        EntityType.WEIGHT_CLASS,
    ],
    #   FK: rankings.promotion_id → promotions.id (NOT NULL)
    #   FK: rankings.fighter_id → fighters.id (NOT NULL)
    #   FK: rankings.weight_class_id → weight_classes.id (NULLABLE)
    #   Promotions, fighters, and weight classes MUST exist.
}


# ── Dependency Graph ──────────────────────────────────────────────────────────


@dataclass
class DependencyGraph:
    """Directed acyclic graph of entity dependencies.

    Nodes: EntityType values.
    Edges: X → Y means "Y depends on X" (X must complete before Y).
    """

    _adjacency: dict[EntityType, list[EntityType]] = field(default_factory=dict)
    _in_degree: dict[EntityType, int] = field(default_factory=dict)
    _nodes: set[EntityType] = field(default_factory=set)

    @classmethod
    def from_map(
        cls, deps: dict[EntityType, list[EntityType]] | None = None
    ) -> "DependencyGraph":
        """Build graph from a dependency map.

        Args:
            deps: {entity → [dependencies]}. Defaults to DEPENDENCY_MAP.

        Returns:
            DependencyGraph ready for topological sort.
        """
        graph = cls()
        source = deps or DEPENDENCY_MAP

        for entity in source:
            graph.add_node(entity)

        for entity, dependencies in source.items():
            for dep in dependencies:
                graph.add_edge(dep, entity)

        return graph

    @classmethod
    def from_jobs(cls, jobs: dict[EntityType, SyncJob]) -> "DependencyGraph":
        """Build graph from a job registry. Reads depends_on from each job.

        Args:
            jobs: {EntityType → SyncJob} map from the engine.

        Returns:
            DependencyGraph with edges from job.depends_on declarations.
        """
        graph = cls()

        for entity_type in jobs:
            graph.add_node(entity_type)

        for entity_type, job in jobs.items():
            for dep in job.depends_on:
                graph.add_edge(dep, entity_type)

        return graph

    # ── Graph construction ─────────────────────────────────────────────────

    def add_node(self, entity: EntityType) -> None:
        """Add a node to the graph. Idempotent."""
        if entity not in self._nodes:
            self._nodes.add(entity)
            self._adjacency[entity] = []
            self._in_degree[entity] = 0

    def add_edge(self, from_entity: EntityType, to_entity: EntityType) -> None:
        """Add a directed edge: from_entity → to_entity.

        Means: to_entity DEPENDS ON from_entity.
        from_entity must complete before to_entity can start.
        """
        self.add_node(from_entity)
        self.add_node(to_entity)

        # Avoid duplicate edges
        if to_entity not in self._adjacency.get(from_entity, []):
            self._adjacency[from_entity].append(to_entity)
            self._in_degree[to_entity] = self._in_degree.get(to_entity, 0) + 1

    # ── Topological sort (Kahn's algorithm) ────────────────────────────────

    def topological_sort(self) -> list[EntityType]:
        """Produce a valid execution order.

        Uses Kahn's algorithm: repeatedly remove nodes with zero in-degree.
        If nodes remain after processing, there's a cycle.

        Returns:
            Ordered list of EntityType values.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        in_degree = dict(self._in_degree)
        queue: deque[EntityType] = deque()

        # Start with nodes that have no dependencies
        for node in self._nodes:
            if in_degree.get(node, 0) == 0:
                queue.append(node)

        result: list[EntityType] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(self._nodes):
            remaining = self._nodes - set(result)
            raise ValueError(
                f"Circular dependency detected among: "
                f"{[e.value for e in remaining]}"
            )

        return result

    # ── Cycle detection ────────────────────────────────────────────────────

    def has_cycle(self) -> bool:
        """Check if the graph contains any cycles."""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True

    def find_cycles(self) -> list[list[EntityType]]:
        """Find all cycles in the graph (expensive — call only for debugging)."""
        cycles: list[list[EntityType]] = []
        visited: set[EntityType] = set()
        path: list[EntityType] = []

        def dfs(node: EntityType) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycles.append(list(path[cycle_start:]))
                return
            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in self._adjacency.get(node, []):
                dfs(neighbor)

            path.pop()

        for node in self._nodes:
            if node not in visited:
                dfs(node)

        return cycles

    # ── Plan validation ────────────────────────────────────────────────────

    def validate_plan(self, plan: SyncPlan) -> tuple[bool, str]:
        """Check if a plan's order satisfies all job dependencies.

        A plan is valid if: for every job in the plan, all its dependencies
        that are ALSO in the plan appear before it in the plan's order.

        Dependencies NOT in the plan are ignored (they may already exist in
        the DB from a previous sync).

        Args:
            plan: A SyncPlan to validate.

        Returns:
            (is_valid, message) — True if the order satisfies all deps.
        """
        plan_set = set(plan.order)

        # Build reverse index: entity → [what it depends on]
        # (adjacency stores: dependency → [dependents], we need: dependent → [dependencies])
        depends_on: dict[EntityType, list[EntityType]] = defaultdict(list)
        for from_node, neighbors in self._adjacency.items():
            for to_node in neighbors:
                depends_on[to_node].append(from_node)

        for i, entity in enumerate(plan.order):
            deps = depends_on.get(entity, [])
            for dep in deps:
                if dep not in plan_set:
                    continue  # Dep not in plan — assumed satisfied externally
                dep_index = plan.order.index(dep)
                if dep_index >= i:
                    return False, (
                        f"{entity.value} depends on {dep.value}, "
                        f"but {dep.value} at position {dep_index} "
                        f"comes after {entity.value} at position {i}"
                    )

        return True, "Plan order satisfies all dependencies"

    # ── Visualization ──────────────────────────────────────────────────────

    def to_edges(self) -> list[tuple[str, str]]:
        """Return edges as (from, to) tuples for visualization."""
        edges: list[tuple[str, str]] = []
        for from_node, neighbors in self._adjacency.items():
            for to_node in neighbors:
                edges.append((from_node.value, to_node.value))
        return edges

    def to_dot(self) -> str:
        """Export as Graphviz DOT format."""
        lines = ["digraph sync_deps {"]
        lines.append("  rankdir=LR;")
        for from_node, neighbors in self._adjacency.items():
            for to_node in neighbors:
                lines.append(f'  "{from_node.value}" -> "{to_node.value}";')
        lines.append("}")
        return "\n".join(lines)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(neighbors) for neighbors in self._adjacency.values())

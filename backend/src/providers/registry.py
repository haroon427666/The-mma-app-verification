"""
Provider Registry.

Maps promotion slugs (e.g. "ufc", "bellator-mma") to provider instances.
The sync engine asks the registry "who handles UFC?" and gets the ESPN provider.
ONE Championship's ESPN league slug is "ofc" (research-verified) — NOT
"one-championship".

No service or sync code changes when a new provider is added.
"""

from collections import defaultdict

from src.providers.base import BaseDataProvider


class ProviderRegistry:
    """Central registry mapping promotion slugs to data providers."""

    def __init__(self) -> None:
        self._promotion_map: dict[str, BaseDataProvider] = {}
        self._providers: dict[str, BaseDataProvider] = {}  # by provider_slug
        # Reverse map: provider_slug → list of promotion slugs
        self._provider_promotions: dict[str, list[str]] = defaultdict(list)

    def register(
        self,
        provider: BaseDataProvider,
        promotion_slugs: list[str],
    ) -> None:
        """Register a provider for one or more promotions.

        Args:
            provider: A BaseDataProvider implementation.
            promotion_slugs: List of promotion slugs this provider handles
                            (e.g. ["ufc", "bellator-mma"] for ESPN).
        """
        self._providers[provider.provider_slug] = provider
        for slug in promotion_slugs:
            self._promotion_map[slug] = provider
            self._provider_promotions[provider.provider_slug].append(slug)

    def get_provider(self, promotion_slug: str) -> BaseDataProvider | None:
        """Get the provider responsible for a given promotion.

        Args:
            promotion_slug: e.g. "ufc", "bellator-mma"

        Returns:
            The BaseDataProvider instance, or None if no provider registered.
        """
        return self._promotion_map.get(promotion_slug)

    def get_provider_by_slug(self, provider_slug: str) -> BaseDataProvider | None:
        """Get a provider instance by its slug (e.g. 'espn')."""
        return self._providers.get(provider_slug)

    def get_all_providers(self) -> list[BaseDataProvider]:
        """Return all registered provider instances."""
        return list(self._providers.values())

    @property
    def promotion_count(self) -> int:
        """Number of promotions with registered providers."""
        return len(self._promotion_map)

    @property
    def provider_count(self) -> int:
        """Number of registered providers."""
        return len(self._providers)


# ── Global singleton ───────────────────────────────────────────────────────────
# Deliberately NOT a module-level singleton for horizontal scaling.
# Each FastAPI app instance creates its own ProviderRegistry at startup.

def create_registry() -> ProviderRegistry:
    """Factory function — creates a fresh ProviderRegistry."""
    return ProviderRegistry()

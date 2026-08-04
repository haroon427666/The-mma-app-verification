"""ESPN Data Provider Package.

Exports the ESPN provider and its configuration.
"""

from src.providers.espn.config import ESPNClientConfig
from src.providers.espn.provider import ESPNProvider

__all__ = ["ESPNClientConfig", "ESPNProvider"]


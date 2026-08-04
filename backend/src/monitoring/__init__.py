from src.monitoring.alerts import (
    Alert,
    AlertEngine,
    LoginStormDetector,
    SyncFailureTracker,
    TokenReuseDetector,
)
from src.monitoring.config_validator import ConfigError, ConfigResult, validate_config
from src.monitoring.health import (
    HealthCheck,
    HealthChecker,
    HealthStatus,
    check_database,
    check_provider_espn,
    check_redis,
    check_scheduler,
)
from src.monitoring.providers import ProviderMetrics, ProviderMonitor
from src.monitoring.scheduler_metrics import SchedulerMetricsCollector

try:
    from src.monitoring.database import install_connection_pool_monitor, install_slow_query_detector
except ImportError:
    install_slow_query_detector = None  # type: ignore
    install_connection_pool_monitor = None  # type: ignore

try:
    from src.monitoring.exception_tracker import ExceptionTrackerMiddleware, ProfilerMiddleware
except ImportError:
    ExceptionTrackerMiddleware = None  # type: ignore
    ProfilerMiddleware = None  # type: ignore

__all__ = [
    "Alert",
    "AlertEngine",
    "ConfigError",
    "ConfigResult",
    "ExceptionTrackerMiddleware",
    "HealthCheck",
    "HealthChecker",
    "HealthStatus",
    "LoginStormDetector",
    "ProfilerMiddleware",
    "ProviderMetrics",
    "ProviderMonitor",
    "SchedulerMetricsCollector",
    "SyncFailureTracker",
    "TokenReuseDetector",
    "check_database",
    "check_provider_espn",
    "check_redis",
    "check_scheduler",
    "install_connection_pool_monitor",
    "install_slow_query_detector",
    "validate_config",
]

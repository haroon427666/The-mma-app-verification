"""v1 API package — all routers."""

from src.api.v1.auth import router as auth_router
from src.api.v1.compare import router as compare_router
from src.api.v1.events import router as event_router
from src.api.v1.fighters import router as fighter_router
from src.api.v1.fights import router as fight_router
from src.api.v1.notifications import router as notification_router
from src.api.v1.other import (
    champion_router,
    health_router,
    promo_router,
    ranking_router,
    search_router,
    title_router,
    venue_router,
    wc_router,
)
from src.api.v1.recommendations import router as recommendations_router
from src.api.v1.search import router as search_ext_router
from src.api.v1.users import (
    fav_router,
    pref_router,
    session_router,
    user_router,
    watch_router,
)
from src.api.v1.watchlist import router as watchlist_router

routers = [
    health_router,
    auth_router,
    user_router, pref_router, fav_router, watch_router, session_router,
    fighter_router,
    event_router,
    fight_router,
    compare_router,
    ranking_router,
    champion_router,
    title_router,
    promo_router,
    venue_router,
    wc_router,
    search_router,
    search_ext_router,
    watchlist_router,
    notification_router,
    recommendations_router,
]

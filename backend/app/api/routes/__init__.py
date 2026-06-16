"""Route registration."""
from fastapi import APIRouter

from app.api.routes import (
    agents,
    chat,
    connectors,
    health,
    insights,
    knowledge,
    reports,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

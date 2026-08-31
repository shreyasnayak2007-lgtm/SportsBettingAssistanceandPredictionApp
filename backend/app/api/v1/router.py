from fastapi import APIRouter
from app.api.v1.endpoints import games, matchups

api_router = APIRouter()
api_router.include_router(games.router, prefix="/games", tags=["Games"])
api_router.include_router(matchups.router, prefix="/matchups", tags=["Matchups"])
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.services.live_games import get_today_games

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/today")
def today_games(game_date: date | None = Query(default=None)):
    try:
        return {"data": get_today_games(game_date), "source": "mlb_stats_api+pybaseball", "is_mock": False}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Live MLB data unavailable: {exc}") from exc

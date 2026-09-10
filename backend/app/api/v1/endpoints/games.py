from fastapi import APIRouter, HTTPException

from app.services.live_games import get_today_games

router = APIRouter()


@router.get('/today')
def today_games():
    try:
        return {'data': get_today_games()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail='MLB data provider unavailable') from exc

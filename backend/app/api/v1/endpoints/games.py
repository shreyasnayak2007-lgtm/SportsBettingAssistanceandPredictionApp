from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db.database import get_db
from app.db.models import Game, Team
from app.schemas.game import GameResponse

router = APIRouter(
    prefix="/games",
    tags=["Games"]
)

@router.get(
    "/today",
    response_model=list[GameResponse]
)
def get_today_games(
    db: Session = Depends(get_db)
):
    today = datetime.now(
        ZoneInfo("America/New_York")
    ).date()

    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)

    statement = (
        select(
            Game,
            HomeTeam,
            AwayTeam
        )
        .join(
            HomeTeam,
            Game.home_team_id == HomeTeam.id
        )
        .join(
            AwayTeam,
            Game.away_team_id == AwayTeam.id
        )
        .where(Game.game_date == today)
        .order_by(Game.id)
    )

    rows = db.execute(statement).all()

    games = []

    for game, home_team, away_team in rows:
        games.append({
            "id": game.id,
            "game_pk": game.game_pk,
            "game_date": game.game_date,
            "season": game.season,
            "status": game.status,

            "game_datetime": game.game_datetime,

            "current_inning": game.current_inning,
            "inning_state": game.inning_state,
            "outs": game.outs,

            "runner_on_first": bool(game.runner_on_first),
            "runner_on_second": bool(game.runner_on_second),
            "runner_on_third": bool(game.runner_on_third),

            "away_team": {
                "id": away_team.id,
                "mlb_team_id": away_team.mlb_team_id,
                "abbreviation": away_team.abbreviation,
                "name": away_team.name,
                "league": away_team.league,
                "division": away_team.division,
                "score": game.away_score,
            },

            "home_team": {
                "id": home_team.id,
                "mlb_team_id": home_team.mlb_team_id,
                "abbreviation": home_team.abbreviation,
                "name": home_team.name,
                "league": home_team.league,
                "division": home_team.division,
                "score": game.home_score,
            },

        })

    return games

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased

from app.db.database import get_db
from app.db.models import Game, StatcastPitch, Team
from app.schemas.game import GameResponse, GameStatsResponse

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

    game_pks = [game.game_pk for game, _, _ in rows]
    telemetry_by_game = {}
    if game_pks:
        aggregates = db.execute(
            select(
                StatcastPitch.game_pk,
                func.count(StatcastPitch.id),
                func.sum(case((StatcastPitch.events == "strikeout", 1), else_=0)),
                func.sum(case((StatcastPitch.events.in_(("walk", "intent_walk", "intentional_walk")), 1), else_=0)),
                func.sum(case((StatcastPitch.launch_speed.is_not(None), 1), else_=0)),
            )
            .where(StatcastPitch.game_pk.in_(game_pks))
            .group_by(StatcastPitch.game_pk)
        ).all()
        telemetry_by_game = {
            game_pk: (pitches, strikeouts or 0, walks or 0, balls_in_play or 0)
            for game_pk, pitches, strikeouts, walks, balls_in_play in aggregates
        }

    games = []

    for game, home_team, away_team in rows:
        pitch_total, strikeouts, walks, balls_in_play = telemetry_by_game.get(
            game.game_pk, (0, 0, 0, 0)
        )
        pitch_sample = db.scalars(
            select(StatcastPitch)
            .where(StatcastPitch.game_pk == game.game_pk)
            .order_by(StatcastPitch.at_bat_number.desc(), StatcastPitch.pitch_number.desc())
            .limit(3)
        ).all()
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
            "stats": GameStatsResponse(
                pitches=pitch_total,
                strikeouts=strikeouts,
                walks=walks,
                balls_in_play=balls_in_play,
                source="real" if pitch_total else "unavailable",
                sample=[
                    {
                        "pitcher_id": pitch.pitcher_id,
                        "batter_id": pitch.batter_id,
                        "pitch_type": pitch.pitch_type,
                        "release_speed": pitch.release_speed,
                        "events": pitch.events,
                        "description": pitch.description,
                    }
                    for pitch in reversed(pitch_sample)
                ],
            ),

        })

    return games

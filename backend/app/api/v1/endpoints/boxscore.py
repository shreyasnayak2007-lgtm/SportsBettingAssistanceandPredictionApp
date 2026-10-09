from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Game, Player, StatcastPitch, Team
from app.schemas.boxscore import BoxScoreBattingLine, BoxScoreResponse, BoxScoreTeam

router = APIRouter(prefix="/boxscore", tags=["Boxscore"])

HIT_EVENTS = {"single", "double", "triple", "home_run"}
NON_AT_BAT_EVENTS = {
    "walk", "intent_walk", "intentional_walk", "hit_by_pitch", "sac_fly",
    "sac_bunt", "catcher_interf",
}


def _batting_lines(pitches, players):
    final_events = {}
    for pitch in pitches:
        if pitch.events:
            final_events[(pitch.game_pk, pitch.at_bat_number)] = pitch

    by_batter = defaultdict(list)
    for pitch in final_events.values():
        if pitch.batter_id is not None:
            by_batter[pitch.batter_id].append(pitch.events.lower())

    names = {player.mlbam_id: player.full_name for player in players}
    lines = []
    for mlbam_id, events in sorted(by_batter.items()):
        hits = sum(event in HIT_EVENTS for event in events)
        at_bats = sum(event not in NON_AT_BAT_EVENTS for event in events)
        lines.append(BoxScoreBattingLine(
            mlbam_id=mlbam_id,
            name=names.get(mlbam_id) or f"Player {mlbam_id}",
            at_bats=at_bats,
            hits=hits,
            singles=events.count("single"),
            doubles=events.count("double"),
            triples=events.count("triple"),
            home_runs=events.count("home_run"),
            walks=events.count("walk") + events.count("intent_walk")
            + events.count("intentional_walk"),
            strikeouts=events.count("strikeout"),
        ))
    return lines


def _team_response(team: Team, score, batting_lines):
    return BoxScoreTeam(
        id=team.id,
        mlb_team_id=team.mlb_team_id,
        abbreviation=team.abbreviation,
        name=team.name,
        score=score,
        hits=sum(line.hits for line in batting_lines),
        runs=score,
        batting=batting_lines,
    )


@router.get("", response_model=BoxScoreResponse)
def get_boxscore(
    game_pk: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    game = db.scalar(select(Game).where(Game.game_pk == game_pk))
    if game is None:
        raise HTTPException(status_code=404, detail=f"Game {game_pk} not found")

    home_team = db.get(Team, game.home_team_id)
    away_team = db.get(Team, game.away_team_id)
    if home_team is None or away_team is None:
        raise HTTPException(
            status_code=500,
            detail=f"Teams for game {game_pk} could not be loaded",
        )

    pitches = db.scalars(
        select(StatcastPitch)
        .where(StatcastPitch.game_pk == game_pk)
        .order_by(StatcastPitch.at_bat_number, StatcastPitch.pitch_number)
    ).all()
    home_players = db.scalars(
        select(Player).where(Player.team_id == game.home_team_id)
    ).all()
    away_players = db.scalars(
        select(Player).where(Player.team_id == game.away_team_id)
    ).all()
    home_batting = _batting_lines(pitches, home_players)
    away_batting = _batting_lines(pitches, away_players)

    return BoxScoreResponse(
        game_pk=game.game_pk,
        game_date=game.game_date,
        game_datetime=game.game_datetime,
        season=game.season,
        status=game.status,
        current_inning=game.current_inning,
        inning_state=game.inning_state,
        outs=game.outs,
        runners={
            "first": bool(game.runner_on_first),
            "second": bool(game.runner_on_second),
            "third": bool(game.runner_on_third),
        },
        away_team=_team_response(away_team, game.away_score, away_batting),
        home_team=_team_response(home_team, game.home_score, home_batting),
    )

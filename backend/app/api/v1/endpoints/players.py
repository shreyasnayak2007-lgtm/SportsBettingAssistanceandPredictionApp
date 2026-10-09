from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import BattingSeasonStat, PitchingSeasonStat, Player, StatcastPitch
from app.schemas.player import PlayerResponse
from app.schemas.pitcher import PitcherSeasonStatsResponse
from app.schemas.player_stats import (
    BattingSeasonStatsResponse,
    PitchingSeasonStatsResponse as PlayerPitchingSeasonStatsResponse,
    PlayerSeasonStatsResponse,
)


router = APIRouter()


@router.get("/mlbam/{mlbam_id}", response_model=PlayerResponse)
def get_player_by_mlbam_id(
    mlbam_id: int,
    db: Session = Depends(get_db),
):
    # PostgreSQL INTEGER range check
    if mlbam_id < 1 or mlbam_id > 2147483647:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    player = (
        db.query(Player)
        .filter(Player.mlbam_id == mlbam_id)
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    return player


@router.get(
    "/mlbam/{mlbam_id}/pitching-stats",
    response_model=PitcherSeasonStatsResponse,
)
def get_pitcher_season_stats(
    mlbam_id: int,
    season: int = Query(..., ge=1900, le=2100),
    db: Session = Depends(get_db),
):
    """Return the pitcher metrics used by the simulation for one season."""
    player = db.query(Player).filter(Player.mlbam_id == mlbam_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    start_date = date(season, 1, 1)
    end_date = date(season, 12, 31)
    season_record = (
        db.query(PitchingSeasonStat)
        .filter(
            PitchingSeasonStat.player_id == player.id,
            PitchingSeasonStat.season == season,
        )
        .first()
    )
    pitches = (
        db.query(StatcastPitch)
        .filter(
            StatcastPitch.pitcher_id == mlbam_id,
            StatcastPitch.game_date >= start_date,
            StatcastPitch.game_date <= end_date,
        )
        .all()
    )
    if not pitches and season_record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No pitching data found for {mlbam_id} in {season}",
        )

    events = [pitch.events.lower() for pitch in pitches if pitch.events]
    hits = sum(event in {"single", "double", "triple", "home_run"} for event in events)
    strikeouts = events.count("strikeout")
    walks = events.count("walk")
    singles = events.count("single")
    doubles = events.count("double")
    triples = events.count("triple")
    home_runs = events.count("home_run")
    at_bats = hits + sum(
        event in {"field_out", "force_out", "grounded_into_double_play", "strikeout"}
        for event in events
    )
    batters_faced = len({(pitch.game_pk, pitch.at_bat_number) for pitch in pitches})
    release_speeds = [pitch.release_speed for pitch in pitches if pitch.release_speed is not None]
    whiffs = sum(
        "swinging_strike" in (pitch.description or "")
        for pitch in pitches
    )

    return PitcherSeasonStatsResponse(
        mlbam_id=mlbam_id,
        season=season,
        pitches=len(pitches) if pitches else (season_record.pitches or 0),
        batters_faced=(season_record.batters_faced if season_record and season_record.batters_faced is not None else (batters_faced if pitches else None)),
        strikeouts=(season_record.strikeouts if season_record and season_record.strikeouts is not None else (strikeouts if pitches else None)),
        walks=(season_record.walks if season_record and season_record.walks is not None else (walks if pitches else None)),
        singles_allowed=(season_record.singles_allowed if season_record and season_record.singles_allowed is not None else (singles if pitches else None)),
        doubles_allowed=(season_record.doubles_allowed if season_record and season_record.doubles_allowed is not None else (doubles if pitches else None)),
        triples_allowed=(season_record.triples_allowed if season_record and season_record.triples_allowed is not None else (triples if pitches else None)),
        home_runs_allowed=(season_record.home_runs_allowed if season_record and season_record.home_runs_allowed is not None else (home_runs if pitches else None)),
        hits_allowed=(season_record.hits_allowed if season_record and season_record.hits_allowed is not None else (hits if pitches else None)),
        average_release_speed=(sum(release_speeds) / len(release_speeds))
        if release_speeds else None,
        whiff_rate=whiffs / len(pitches) if pitches else None,
        strikeout_rate=(season_record.strikeouts / season_record.batters_faced)
        if season_record and season_record.strikeouts is not None and season_record.batters_faced
        else (strikeouts / batters_faced if batters_faced else None),
        walk_rate=(season_record.walks / season_record.batters_faced)
        if season_record and season_record.walks is not None and season_record.batters_faced
        else (walks / batters_faced if batters_faced else None),
        batting_average_against=(
            season_record.batting_average_against
            if season_record else (hits / at_bats if at_bats else None)
        ),
        innings_pitched=(
            f"{season_record.innings_outs // 3}.{season_record.innings_outs % 3}"
            if season_record and season_record.innings_outs is not None else None
        ),
        earned_runs=season_record.earned_runs if season_record else None,
        era=season_record.era if season_record else None,
        era_note=None if season_record and season_record.era is not None else (
            "Import pitching season stats to include official ERA."
        ),
    )


@router.get(
    "/mlbam/{mlbam_id}/stats",
    response_model=PlayerSeasonStatsResponse,
)
def get_player_season_stats(
    mlbam_id: int,
    season: int = Query(..., ge=1900, le=2100),
    db: Session = Depends(get_db),
):
    """Return stored batting and pitching season totals for an MLBAM player."""
    player = db.query(Player).filter(Player.mlbam_id == mlbam_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    batting = db.query(BattingSeasonStat).filter(
        BattingSeasonStat.player_id == player.id,
        BattingSeasonStat.season == season,
    ).first()
    pitching = db.query(PitchingSeasonStat).filter(
        PitchingSeasonStat.player_id == player.id,
        PitchingSeasonStat.season == season,
    ).first()

    pitching_response = None
    if pitching is not None:
        outs = pitching.innings_outs
        innings_pitched = (
            f"{outs // 3}.{outs % 3}" if outs is not None else None
        )
        pitching_response = PlayerPitchingSeasonStatsResponse(
            **{
                **{
                    column.name: getattr(pitching, column.name)
                    for column in PitchingSeasonStat.__table__.columns
                    if column.name in PlayerPitchingSeasonStatsResponse.model_fields
                },
                "innings_pitched": innings_pitched,
            }
        )

    return PlayerSeasonStatsResponse(
        mlbam_id=mlbam_id,
        full_name=player.full_name,
        season=season,
        batting=(
            BattingSeasonStatsResponse.model_validate(batting, from_attributes=True)
            if batting else None
        ),
        pitching=pitching_response,
    )


@router.get("/", response_model=list[PlayerResponse])
def get_players(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    players = (
        db.query(Player)
        .order_by(Player.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return players


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    return player

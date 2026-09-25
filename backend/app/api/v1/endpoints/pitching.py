from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import PitchingSeasonStat, Player
from app.schemas.pitching import PitchingSeasonStatResponse


router = APIRouter()


@router.get("/", response_model=list[PitchingSeasonStatResponse])
def get_pitching_stats(
    season: int = 2026,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    stats = (
        db.query(PitchingSeasonStat)
        .filter(PitchingSeasonStat.season == season)
        .order_by(PitchingSeasonStat.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return stats


@router.get(
    "/player/{player_id}",
    response_model=PitchingSeasonStatResponse,
)
def get_pitching_stats_by_player_id(
    player_id: int,
    season: int = 2026,
    db: Session = Depends(get_db),
):
    pitching_stat = (
        db.query(PitchingSeasonStat)
        .filter(
            PitchingSeasonStat.player_id == player_id,
            PitchingSeasonStat.season == season,
        )
        .first()
    )

    if pitching_stat is None:
        raise HTTPException(
            status_code=404,
            detail="Pitching stats not found",
        )

    return pitching_stat


@router.get(
    "/mlbam/{mlbam_id}",
    response_model=PitchingSeasonStatResponse,
)
def get_pitching_stats_by_mlbam_id(
    mlbam_id: int,
    season: int = 2026,
    db: Session = Depends(get_db),
):
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

    pitching_stat = (
        db.query(PitchingSeasonStat)
        .filter(
            PitchingSeasonStat.player_id == player.id,
            PitchingSeasonStat.season == season,
        )
        .first()
    )

    if pitching_stat is None:
        raise HTTPException(
            status_code=404,
            detail="Pitching stats not found",
        )

    return pitching_stat

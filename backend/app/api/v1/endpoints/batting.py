from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import BattingSeasonStat, Player
from app.schemas.batting import BattingSeasonStatResponse


router = APIRouter()


@router.get("/", response_model=list[BattingSeasonStatResponse])
def get_batting_stats(
    season: int = 2026,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    stats = (
        db.query(BattingSeasonStat)
        .filter(BattingSeasonStat.season == season)
        .order_by(BattingSeasonStat.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return stats


@router.get(
    "/player/{player_id}",
    response_model=BattingSeasonStatResponse,
)
def get_batting_stats_by_player_id(
    player_id: int,
    season: int = 2026,
    db: Session = Depends(get_db),
):
    batting_stat = (
        db.query(BattingSeasonStat)
        .filter(
            BattingSeasonStat.player_id == player_id,
            BattingSeasonStat.season == season,
        )
        .first()
    )

    if batting_stat is None:
        raise HTTPException(
            status_code=404,
            detail="Batting stats not found",
        )

    return batting_stat


@router.get(
    "/mlbam/{mlbam_id}",
    response_model=BattingSeasonStatResponse,
)
def get_batting_stats_by_mlbam_id(
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

    batting_stat = (
        db.query(BattingSeasonStat)
        .filter(
            BattingSeasonStat.player_id == player.id,
            BattingSeasonStat.season == season,
        )
        .first()
    )

    if batting_stat is None:
        raise HTTPException(
            status_code=404,
            detail="Batting stats not found",
        )

    return batting_stat

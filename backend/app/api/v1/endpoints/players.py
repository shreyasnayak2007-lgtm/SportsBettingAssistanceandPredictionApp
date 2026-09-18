from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Player
from app.schemas.player import PlayerResponse


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

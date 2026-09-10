from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import StatcastPitch
from app.schemas.statcast import StatcastPitchResponse


router = APIRouter(
    prefix="/statcast",
    tags=["Statcast"]
)


@router.get(
    "/games/{game_pk}",
    response_model=list[StatcastPitchResponse]
)
def get_game_statcast(
    game_pk: int,
    db: Session = Depends(get_db)
):
    statement = (
        select(StatcastPitch)
        .where(StatcastPitch.game_pk == game_pk)
        .order_by(
            StatcastPitch.at_bat_number,
            StatcastPitch.pitch_number
        )
    )

    pitches = db.scalars(statement).all()

    if not pitches:
        raise HTTPException(
            status_code=404,
            detail=f"No Statcast data found for game {game_pk}"
        )

    return pitches

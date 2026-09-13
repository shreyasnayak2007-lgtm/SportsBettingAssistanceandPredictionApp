from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Team
from app.schemas.team import TeamResponse


router = APIRouter(
    prefix="/teams",
    tags=["Teams"]
)


@router.get(
    "",
    response_model=list[TeamResponse]
)
def get_all_teams(
    db: Session = Depends(get_db)
):
    statement = select(Team).order_by(Team.abbreviation)

    teams = db.scalars(statement).all()

    return teams


@router.get(
    "/{team_id}",
    response_model=TeamResponse
)
def get_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    statement = select(Team).where(
        Team.id == team_id
    )

    team = db.scalar(statement)

    if not team:
        raise HTTPException(
            status_code=404,
            detail=f"Team with ID {team_id} not found"
        )

    return team

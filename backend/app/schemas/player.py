from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PlayerResponse(BaseModel):
    id: int
    mlbam_id: int

    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None

    position: str | None = None
    jersey_number: str | None = None

    bat_side: str | None = None
    pitch_hand: str | None = None

    team_id: int | None = None
    active: bool | None = None

    birth_date: date | None = None
    height: str | None = None
    weight: int | None = None
    mlb_debut_date: date | None = None

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import date

from pydantic import BaseModel, ConfigDict


class StatcastPitchResponse(BaseModel):
    id: int
    game_pk: int
    game_date: date

    home_team: str | None
    away_team: str | None

    inning: int | None
    inning_topbot: str | None

    at_bat_number: int
    pitch_number: int

    pitcher_id: int | None
    batter_id: int | None

    pitch_type: str | None
    release_speed: float | None

    balls: int | None
    strikes: int | None

    events: str | None
    description: str | None

    launch_speed: float | None
    launch_angle: float | None
    estimated_woba: float | None

    model_config = ConfigDict(from_attributes=True)

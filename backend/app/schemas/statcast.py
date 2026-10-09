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
    release_spin_rate: float | None = None
    release_extension: float | None = None
    plate_x: float | None = None
    plate_z: float | None = None
    zone: int | None = None
    stand: str | None = None
    p_throws: str | None = None

    balls: int | None
    strikes: int | None

    events: str | None
    description: str | None

    launch_speed: float | None
    launch_angle: float | None
    launch_speed_angle: int | None = None
    hit_distance_sc: float | None = None
    estimated_ba: float | None = None
    estimated_woba: float | None
    barrel: bool | None = None
    raw_data: dict | None = None

    model_config = ConfigDict(from_attributes=True)

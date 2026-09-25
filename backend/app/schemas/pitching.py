from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PitchingSeasonStatResponse(BaseModel):
    id: int

    player_id: int
    season: int

    games: int | None = None
    games_started: int | None = None

    wins: int | None = None
    losses: int | None = None

    saves: int | None = None
    save_opportunities: int | None = None

    innings_pitched: str | None = None

    hits_allowed: int | None = None
    runs_allowed: int | None = None
    earned_runs: int | None = None
    home_runs_allowed: int | None = None

    walks: int | None = None
    strikeouts: int | None = None

    batters_faced: int | None = None
    hit_batters: int | None = None
    wild_pitches: int | None = None
    balks: int | None = None

    era: float | None = None
    whip: float | None = None

    strikeouts_per_9: float | None = None
    walks_per_9: float | None = None
    hits_per_9: float | None = None
    home_runs_per_9: float | None = None

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

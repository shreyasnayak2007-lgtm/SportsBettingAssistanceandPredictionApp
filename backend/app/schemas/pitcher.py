from pydantic import BaseModel


class PitcherSeasonStatsResponse(BaseModel):
    mlbam_id: int
    season: int
    pitches: int
    batters_faced: int | None
    strikeouts: int | None
    walks: int | None
    singles_allowed: int | None
    doubles_allowed: int | None
    triples_allowed: int | None
    home_runs_allowed: int | None
    hits_allowed: int | None
    average_release_speed: float | None
    whiff_rate: float | None
    strikeout_rate: float | None
    walk_rate: float | None
    batting_average_against: float | None
    innings_pitched: str | None = None
    earned_runs: int | None = None
    era: float | None = None
    era_note: str | None = None

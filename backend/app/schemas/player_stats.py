from pydantic import BaseModel


class BattingSeasonStatsResponse(BaseModel):
    games: int | None = None
    plate_appearances: int | None = None
    at_bats: int | None = None
    runs: int | None = None
    hits: int | None = None
    singles: int | None = None
    doubles: int | None = None
    triples: int | None = None
    home_runs: int | None = None
    rbi: int | None = None
    walks: int | None = None
    strikeouts: int | None = None
    stolen_bases: int | None = None
    caught_stealing: int | None = None
    batting_average: float | None = None
    on_base_percentage: float | None = None
    slugging_percentage: float | None = None
    ops: float | None = None
    woba: float | None = None
    wrc_plus: float | None = None
    war: float | None = None
    raw_data: dict | None = None


class PitchingSeasonStatsResponse(BaseModel):
    games: int | None = None
    games_started: int | None = None
    wins: int | None = None
    losses: int | None = None
    saves: int | None = None
    holds: int | None = None
    innings_outs: int | None = None
    innings_pitched: str | None = None
    hits_allowed: int | None = None
    runs_allowed: int | None = None
    earned_runs: int | None = None
    home_runs_allowed: int | None = None
    walks: int | None = None
    strikeouts: int | None = None
    hit_batters: int | None = None
    batters_faced: int | None = None
    era: float | None = None
    whip: float | None = None
    strikeouts_per_nine: float | None = None
    walks_per_nine: float | None = None
    hits_per_nine: float | None = None
    home_runs_per_nine: float | None = None
    raw_data: dict | None = None


class PlayerSeasonStatsResponse(BaseModel):
    mlbam_id: int
    full_name: str | None
    season: int
    batting: BattingSeasonStatsResponse | None
    pitching: PitchingSeasonStatsResponse | None

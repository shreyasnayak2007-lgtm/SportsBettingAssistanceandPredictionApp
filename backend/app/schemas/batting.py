from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BattingSeasonStatResponse(BaseModel):
    id: int

    player_id: int
    season: int

    fangraphs_id: int | None = None

    games: int | None = None
    plate_appearances: int | None = None
    at_bats: int | None = None

    runs: int | None = None
    hits: int | None = None
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

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

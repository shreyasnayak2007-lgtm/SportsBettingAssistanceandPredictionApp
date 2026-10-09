from datetime import date, datetime

from pydantic import BaseModel


class BoxScoreTeam(BaseModel):
    id: int
    mlb_team_id: int
    abbreviation: str
    name: str
    score: int | None
    hits: int
    runs: int | None
    batting: list["BoxScoreBattingLine"]


class BoxScoreBattingLine(BaseModel):
    mlbam_id: int
    name: str
    at_bats: int
    hits: int
    singles: int
    doubles: int
    triples: int
    home_runs: int
    walks: int
    strikeouts: int


class BoxScoreResponse(BaseModel):
    game_pk: int
    game_date: date
    game_datetime: datetime | None
    season: int
    status: str | None
    current_inning: int | None
    inning_state: str | None
    outs: int | None
    runners: dict[str, bool]
    away_team: BoxScoreTeam
    home_team: BoxScoreTeam

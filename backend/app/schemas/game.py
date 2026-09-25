from datetime import date, datetime

from pydantic import BaseModel


class GameTeamResponse(BaseModel):
    id: int
    mlb_team_id: int
    abbreviation: str
    name: str
    league: str | None
    division: str | None
    score: int | None


class GameResponse(BaseModel):
    id: int
    game_pk: int
    game_date: date
    game_datetime: datetime | None

    season: int
    status: str

    current_inning: int | None
    inning_state: str | None
    outs: int | None

    runner_on_first: bool
    runner_on_second: bool
    runner_on_third: bool

    away_team: GameTeamResponse
    home_team: GameTeamResponse

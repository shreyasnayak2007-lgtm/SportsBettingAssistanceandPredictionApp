from datetime import date

from pydantic import BaseModel


class GameTeamResponse(BaseModel):
    id: int
    mlb_team_id: int
    abbreviation: str
    name: str
    score: int | None


class GameResponse(BaseModel):
    id: int
    game_pk: int
    game_date: date
    season: int
    status: str

    away_team: GameTeamResponse
    home_team: GameTeamResponse

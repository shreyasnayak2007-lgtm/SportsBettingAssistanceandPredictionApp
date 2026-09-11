from pydantic import BaseModel, ConfigDict


class TeamResponse(BaseModel):
    id: int
    mlb_team_id: int
    abbreviation: str
    name: str
    league: str | None
    division: str | None

    model_config = ConfigDict(from_attributes=True)
    

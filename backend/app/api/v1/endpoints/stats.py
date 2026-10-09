from fastapi import APIRouter, Depends
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import (
    BattingSeasonStat,
    Game,
    PitchingSeasonStat,
    Player,
    StatcastPitch,
    Team,
)
from app.schemas.telemetry import StatsTelemetryResponse

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/telemetry", response_model=StatsTelemetryResponse)
def get_stats_telemetry(db: Session = Depends(get_db)):
    """Return row counts and freshness for the primary stats tables."""
    models = {
        "players": Player,
        "teams": Team,
        "games": Game,
        "statcast_pitches": StatcastPitch,
        "batting_season_stats": BattingSeasonStat,
        "pitching_season_stats": PitchingSeasonStat,
    }
    existing_tables = set(inspect(db.get_bind()).get_table_names())
    totals = {}
    unavailable_tables = []
    for table_name, model in models.items():
        if table_name not in existing_tables:
            totals[table_name] = 0
            unavailable_tables.append(table_name)
            continue
        row_count = db.scalar(select(func.count()).select_from(model)) or 0
        totals[table_name] = row_count
        if row_count == 0:
            unavailable_tables.append(table_name)

    latest_date = None
    if "statcast_pitches" in existing_tables:
        latest_date = db.scalar(select(func.max(StatcastPitch.game_date)))

    return StatsTelemetryResponse(
        status="ok",
        totals=totals,
        latest_statcast_date=latest_date,
        unavailable_tables=unavailable_tables,
    )

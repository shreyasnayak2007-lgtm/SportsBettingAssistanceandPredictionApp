from datetime import date

from pydantic import BaseModel


class StatsTelemetryResponse(BaseModel):
    status: str
    totals: dict[str, int]
    latest_statcast_date: date | None
    unavailable_tables: list[str]

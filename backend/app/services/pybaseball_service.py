import pandas as pd
from pybaseball import statcast, cache
import numpy as np
from datetime import date


cache.enable()


STATCAST_COLUMNS = [
    "game_pk",
    "game_date",
    "home_team",
    "away_team",
    "inning",
    "inning_topbot",
    "at_bat_number",
    "pitch_number",
    "pitcher",
    "batter",
    "pitch_type",
    "release_speed",
    "release_spin_rate",
    "release_extension",
    "plate_x",
    "plate_z",
    "zone",
    "stand",
    "p_throws",
    "balls",
    "strikes",
    "events",
    "description",
    "launch_speed",
    "launch_angle",
    "launch_speed_angle",
    "hit_distance_sc",
    "estimated_ba_using_speedangle",
    "estimated_woba_using_speedangle",
    "barrel",
]


def _json_safe(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    return value


def get_statcast_data(start_date: str, end_date: str, parallel: bool = False) -> pd.DataFrame:
    refresh_current_month = start_date[:7] == date.today().strftime("%Y-%m")
    if refresh_current_month:
        cache.disable()
    try:
        data = statcast(
            start_dt=start_date,
            end_dt=end_date,
            parallel=parallel,
        )
    finally:
        if refresh_current_month:
            cache.enable()

    return clean_statcast_data(data)


def clean_statcast_data(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame(columns=[
            "game_pk", "game_date", "at_bat_number", "pitch_number",
            "pitcher_id", "batter_id", "raw_data",
        ])

    raw_records = []
    for row in data.to_dict(orient="records"):
        raw_record = {}
        for key, value in row.items():
            safe_value = _json_safe(value)
            if safe_value is not None:
                raw_record[key] = safe_value
        raw_records.append(raw_record)
    # Keep only columns that actually exist in the response
    existing_columns = [
        column for column in STATCAST_COLUMNS
        if column in data.columns
    ]

    cleaned = data[existing_columns].copy()

    # Rename pybaseball columns to match our database model
    cleaned = cleaned.rename(columns={
        "pitcher": "pitcher_id",
        "batter": "batter_id",
        "p_throws": "p_throws",
        "estimated_woba_using_speedangle": "estimated_woba",
        "estimated_ba_using_speedangle": "estimated_ba",
    })

    cleaned["raw_data"] = raw_records

    # Convert game_date into a Python date
    cleaned["game_date"] = pd.to_datetime(
        cleaned["game_date"], errors="coerce"
    ).dt.date

    return cleaned

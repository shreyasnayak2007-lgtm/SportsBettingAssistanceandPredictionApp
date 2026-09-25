import pandas as pd
from pybaseball import statcast, cache
import requests


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
    "balls",
    "strikes",
    "events",
    "description",
    "launch_speed",
    "launch_angle",
    "estimated_woba_using_speedangle",
]


def get_statcast_data(start_date: str, end_date: str) -> pd.DataFrame:
    data = statcast(
        start_dt=start_date,
        end_dt=end_date
    )

    return clean_statcast_data(data)


def clean_statcast_data(data: pd.DataFrame) -> pd.DataFrame:
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
        "estimated_woba_using_speedangle": "estimated_woba",
    })

    # Convert game_date into a Python date
    cleaned["game_date"] = pd.to_datetime(
        cleaned["game_date"]
    ).dt.date

    return cleaned


def fetch_batting_stats_2026():
    response = requests.get(
        "https://statsapi.mlb.com/api/v1/stats",
        params={
            "stats": "season",
            "group": "hitting",
            "season": 2026,
            "sportIds": 1,
            "playerPool": "ALL",
            "limit": 2000,
        },
        timeout=(10, 60),
    )

    response.raise_for_status()

    data = response.json()

    stats_groups = data.get("stats", [])

    if not stats_groups:
        return []

    return stats_groups[0].get("splits", [])

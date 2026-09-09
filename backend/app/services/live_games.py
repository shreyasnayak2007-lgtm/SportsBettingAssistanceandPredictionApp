from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any

import pandas as pd
import requests
from pybaseball import statcast

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"


def _safe_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _team(game_team: dict[str, Any]) -> dict[str, Any]:
    team = game_team.get("team", {})
    return {
        "id": team.get("id"),
        "name": team.get("name", "Unknown team"),
        "abbreviation": team.get("abbreviation", "UNK"),
        "record": game_team.get("record", {}).get("wins", 0),
        "losses": game_team.get("record", {}).get("losses", 0),
    }


def _schedule(date_value: date) -> list[dict[str, Any]]:
    response = requests.get(
        MLB_SCHEDULE_URL,
        params={"sportId": 1, "date": date_value.isoformat(), "hydrate": "team,linescore"},
        timeout=15,
    )
    response.raise_for_status()
    return [game for day in response.json().get("dates", []) for game in day.get("games", [])]


@lru_cache(maxsize=8)
def _statcast_summary(start: str, end: str) -> dict[str, dict[str, Any]]:
    try:
        data = statcast(start_dt=start, end_dt=end)
        if data is None or data.empty or "game_pk" not in data.columns:
            return {}
        grouped: dict[str, dict[str, Any]] = {}
        for game_pk, frame in data.groupby("game_pk"):
            grouped[str(int(game_pk))] = {
                "pitches": int(len(frame)),
                "balls_in_play": int(frame.get("type", pd.Series(dtype=str)).eq("X").sum()),
                "strikeouts": int(frame.get("events", pd.Series(dtype=str)).eq("strikeout").sum()),
                "walks": int(frame.get("events", pd.Series(dtype=str)).isin(["walk", "intent_walk"]).sum()),
                "source": "pybaseball",
            }
        return grouped
    except Exception:
        return {}


def get_today_games(target: date | None = None) -> list[dict[str, Any]]:
    target = target or date.today()
    schedule_games = _schedule(target)
    statcast_data = _statcast_summary(target.isoformat(), (target + timedelta(days=1)).isoformat())
    games: list[dict[str, Any]] = []
    for game in schedule_games:
        away = _team(game.get("teams", {}).get("away", {}))
        home = _team(game.get("teams", {}).get("home", {}))
        status = game.get("status", {})
        linescore = game.get("linescore", {})
        game_pk = str(game.get("gamePk"))
        games.append({
            "game_id": game.get("gamePk"),
            "game_date": target.isoformat(),
            "game_time": game.get("gameDate"),
            "status": status.get("detailedState", "Scheduled"),
            "away_team": away,
            "home_team": home,
            "away_score": linescore.get("teams", {}).get("away", {}).get("runs"),
            "home_score": linescore.get("teams", {}).get("home", {}).get("runs"),
            "inning": linescore.get("currentInning"),
            "statcast": statcast_data.get(game_pk, {"source": "pybaseball", "available": False}),
            "source": "mlb_stats_api+pybaseball",
        })
    return games

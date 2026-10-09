from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

MLB_SCHEDULE_URL = 'https://statsapi.mlb.com/api/v1/schedule'


def _team_code(team: dict[str, Any]) -> str:
    return str(team.get('abbreviation') or team.get('teamName') or team.get('name') or '')


def _get_statcast_stats(game_date: str) -> dict[str, Any]:
    try:
        from pybaseball import statcast
        data = statcast(game_date, game_date)
        if data.empty:
            return {'source': 'unavailable', 'pitches': 0, 'strikeouts': 0, 'walks': 0, 'ballsInPlay': 0, 'sample': []}
        index_fields = ['game_pk', 'game_date', 'home_team', 'away_team', 'inning', 'inning_topbot', 'at_bat_number', 'pitch_number', 'pitcher', 'batter', 'pitch_type', 'release_speed', 'balls', 'strikes', 'events', 'description', 'launch_speed', 'launch_angle', 'estimated_woba']
        sample = data[index_fields].head(5).where(data[index_fields].notna(), None).to_dict(orient='records')
        return {
            'source': 'real',
            'pitches': int(len(data)),
            'strikeouts': int(data['events'].fillna('').astype(str).str.contains('strikeout', case=False).sum()),
            'walks': int(data['events'].fillna('').astype(str).str.contains('walk', case=False).sum()),
            'ballsInPlay': int(data['description'].fillna('').astype(str).str.contains('hit_into_play', case=False).sum()),
            'sample': sample,
        }
    except Exception:
        return {'source': 'unavailable', 'pitches': 0, 'strikeouts': 0, 'walks': 0, 'ballsInPlay': 0, 'sample': []}


def get_today_games() -> list[dict[str, Any]]:
    today = datetime.now(ZoneInfo('America/New_York')).date().isoformat()
    params = {'sportId': 1, 'date': today, 'hydrate': 'team,linescore'}
    with httpx.Client(timeout=15) as client:
        payload = client.get(MLB_SCHEDULE_URL, params=params).raise_for_status()
        data = payload.json()

    statcast_stats = _get_statcast_stats(today)
    games: list[dict[str, Any]] = []
    for date_block in data.get('dates', []):
        for game in date_block.get('games', []):
            away = game.get('teams', {}).get('away', {}).get('team', {})
            home = game.get('teams', {}).get('home', {}).get('team', {})
            status = str(game.get('status', {}).get('abstractGameState', 'Preview')).lower()
            games.append({
                'gamePk': game.get('gamePk'),
                'awayTeam': _team_code(away),
                'homeTeam': _team_code(home),
                'awayTeamLogo': f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{away.get('id')}.svg",
                'homeTeamLogo': f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{home.get('id')}.svg",
                'status': 'live' if status == 'live' else 'final' if status == 'final' else 'upcoming',
                'inning': game.get('linescore', {}).get('currentInning'),
                'awayScore': game.get('teams', {}).get('away', {}).get('score', 0),
                'homeScore': game.get('teams', {}).get('home', {}).get('score', 0),
                'time': game.get('gameDate', today),
                'source': 'real',
                'stats': statcast_stats,
            })
    return games

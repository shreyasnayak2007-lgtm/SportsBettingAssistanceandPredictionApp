from datetime import date
from typing import Any

import httpx

MLB_SCHEDULE_URL = 'https://statsapi.mlb.com/api/v1/schedule'


def _team_code(team: dict[str, Any]) -> str:
    return str(team.get('abbreviation') or team.get('teamName') or team.get('name') or '')


def _get_statcast_stats(game_date: str) -> dict[str, int]:
    try:
        from pybaseball import statcast
        data = statcast(game_date, game_date)
        return {
            'pitches': int(len(data)),
            'strikeouts': int(data.get('events', '').astype(str).str.contains('strikeout', case=False).sum()) if len(data) else 0,
            'walks': int(data.get('events', '').astype(str).str.contains('walk', case=False).sum()) if len(data) else 0,
            'ballsInPlay': int(data.get('description', '').astype(str).str.contains('hit_into_play', case=False).sum()) if len(data) else 0,
        }
    except Exception:
        return {'pitches': 0, 'strikeouts': 0, 'walks': 0, 'ballsInPlay': 0}


def get_today_games() -> list[dict[str, Any]]:
    today = date.today().isoformat()
    params = {'sportId': 1, 'date': today, 'hydrate': 'team'}
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
                'stats': {**statcast_stats, 'source': 'real' if statcast_stats['pitches'] else 'mock'},
            })
    return games

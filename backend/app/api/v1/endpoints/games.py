from fastapi import APIRouter, HTTPException
from app.services.live_games import get_today_games

router = APIRouter()


@router.get('/today')
def today_games():
    try:
        games = get_today_games()

        # Transform to match UI expectations
        enriched_games = []
        for game in games:
            enriched_games.append({
                'gamePk': game.get('game_pk') or game.get('gamePk'),
                'homeTeam': game.get('homeTeam'),
                'awayTeam': game.get('awayTeam'),
                'homeTeamLogo': get_team_logo(game.get('homeTeam')),
                'awayTeamLogo': get_team_logo(game.get('awayTeam')),
                'homeScore': game.get('homeScore', 0),
                'awayScore': game.get('awayScore', 0),
                'status': game.get('status', 'upcoming'),
                'inning': game.get('inning'),
                'time': game.get('time'),
                'pitches': game.get('stats', {}).get('sample', []),
                'odds': {
                    'spread': 'Mock data',
                    'overUnder': 'Mock data',
                    'moneyline': 'Mock data'
                }
            })

        return {'data': enriched_games}
    except Exception as exc:
        raise HTTPException(status_code=502, detail='MLB data provider unavailable') from exc


def get_team_logo(team_abbr: str) -> str:
    """Map team abbreviation to logo emoji/icon"""
    logos = {
        'NYY': '🆈', 'BOS': '🅱️', 'TB': '🆃', 'BAL': '🅾️', 'TOR': '🆃',
        'MIN': '🅼', 'CWS': '🅲', 'KC': '🅺', 'DET': '🅳', 'CLE': '🅲',
        'LAA': '🅰️', 'SEA': '🆂', 'OAK': '🅰️', 'TEX': '🆃', 'HOU': '🅰️',
        'NYM': '🅼', 'ATL': '🅰️', 'WSH': '🆆', 'PHI': '🅿️', 'MIA': '🅼',
        'ARI': '🅰️', 'LAD': '🅻', 'SD': '🆂', 'SF': '🆂', 'COL': '🅲',
        'MIL': '🅼', 'PIT': '🅿️', 'CHC': '🅲', 'STL': '🆂', 'CIN': '🅲'
    }
    return logos.get(team_abbr, team_abbr)
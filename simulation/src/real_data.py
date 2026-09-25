import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class RealDataProvider:
    """Load game participants from the backend, then MLB's public API."""

    def __init__(self, data_dir: Path = None, api_base_url: str = None):
        self.data_dir = data_dir or Path(__file__).resolve().parents[1] / 'data'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.api_base_url = (
            api_base_url or os.getenv(
                'SPORTS_BETTING_API_URL',
                'http://localhost:8000/api/v1'
            )
        ).rstrip('/')

    def load_game_inputs(self, game_date: Optional[str] = None,
                         away_team: Optional[str] = None,
                         home_team: Optional[str] = None) -> Dict:
        """Return real teams, lineups, and pitchers for a game."""
        requested_date = game_date or date.today().isoformat()
        cache_suffix = '_'.join(
            part.lower().replace(' ', '-')
            for part in [away_team or 'first', home_team or 'game']
        )
        cache_filename = f'game_inputs_{requested_date}_{cache_suffix}.json'

        try:
            if not away_team and not home_team:
                game = self._load_from_backend()
                game['source'] = 'backend'
                self._save_json(cache_filename, game)
                return game
        except Exception as error:
            logger.warning("Backend game data unavailable: %s", error)

        cached_game = self._load_json(cache_filename)
        if cached_game:
            logger.info("Using cached real game data for %s", requested_date)
            return cached_game

        game = self._load_from_mlb(requested_date, away_team, home_team)
        game['source'] = 'mlb_api'
        self._save_json(cache_filename, game)
        return game

    def _load_from_backend(self) -> Dict:
        games = self._request_json('/games/today')
        if not games:
            raise ValueError('Backend returned no games for today')

        game = games[0]
        players = self._load_backend_players()
        away = self._build_backend_team(game['away_team'], players)
        home = self._build_backend_team(game['home_team'], players)

        return {
            'game_pk': game.get('game_pk'),
            'game_date': str(game.get('game_date', date.today().isoformat())),
            'away_team': away,
            'home_team': home,
            'away_pitchers': away.pop('pitchers'),
            'home_pitchers': home.pop('pitchers'),
        }

    def _load_backend_players(self) -> List[Dict]:
        players = []
        skip = 0
        limit = 100

        while True:
            page = self._request_json(
                '/players/',
                {'skip': skip, 'limit': limit}
            )
            players.extend(page)
            if len(page) < limit:
                return players
            skip += limit

    @staticmethod
    def _build_backend_team(team: Dict, players: List[Dict]) -> Dict:
        team_players = [
            player for player in players
            if player.get('team_id') == team['id']
            and player.get('active') is not False
        ]
        pitchers = [
            player for player in team_players
            if str(player.get('position', '')).upper() in {'P', 'TWP'}
        ]
        hitters = [
            player for player in team_players
            if player not in pitchers
        ]

        if len(hitters) < 9 or not pitchers:
            raise ValueError(f"Backend roster is incomplete for {team['name']}")

        return {
            'team_name': team['name'],
            'team_id': team.get('mlb_team_id'),
            'lineup': [RealDataProvider._batter(player) for player in hitters[:9]],
            'pitchers': [RealDataProvider._pitcher(player) for player in pitchers],
        }

    @staticmethod
    def _batter(player: Dict) -> Dict:
        return {
            'batter_id': player['mlbam_id'],
            'hand': player.get('bat_side') or 'R',
            'name': player.get('full_name') or RealDataProvider._name(player),
        }

    @staticmethod
    def _pitcher(player: Dict) -> Dict:
        return {
            'pitcher_id': player['mlbam_id'],
            'hand': player.get('pitch_hand') or 'R',
            'name': player.get('full_name') or RealDataProvider._name(player),
        }

    @staticmethod
    def _name(player: Dict) -> str:
        return ' '.join(
            part for part in [player.get('first_name'), player.get('last_name')]
            if part
        ) or f"Player {player['mlbam_id']}"

    def _load_from_mlb(self, game_date: str,
                       away_team: Optional[str] = None,
                       home_team: Optional[str] = None) -> Dict:
        schedule = self._request_external(
            '/schedule',
            {'sportId': 1, 'date': game_date}
        )
        dates = schedule.get('dates', [])
        if not dates or not dates[0].get('games'):
            raise RuntimeError(f'No MLB games found for {game_date}')

        games = dates[0]['games']
        game = next(
            (
                candidate for candidate in games
                if self._matches_team(candidate['teams']['away']['team'], away_team)
                and self._matches_team(candidate['teams']['home']['team'], home_team)
            ),
            None,
        ) if away_team or home_team else games[0]
        if game is None:
            requested_matchup = f'{away_team or "any team"} @ {home_team or "any team"}'
            raise RuntimeError(f'No MLB game found for {requested_matchup} on {game_date}')

        boxscore = self._request_external(f"/game/{game['gamePk']}/boxscore")
        return {
            'game_pk': game['gamePk'],
            'game_date': game_date,
            'away_team': self._mlb_team(game, boxscore, 'away'),
            'home_team': self._mlb_team(game, boxscore, 'home'),
            'away_pitchers': self._mlb_pitchers(game, boxscore, 'away'),
            'home_pitchers': self._mlb_pitchers(game, boxscore, 'home'),
        }

    @staticmethod
    def _matches_team(team: Dict, requested_name: Optional[str]) -> bool:
        if not requested_name:
            return True
        requested_name = requested_name.lower()
        abbreviation = str(team.get('abbreviation', '')).lower()
        return requested_name in team['name'].lower() or requested_name == abbreviation

    def _mlb_team(self, game: Dict, boxscore: Dict, side: str) -> Dict:
        team = game['teams'][side]['team']
        team_boxscore = boxscore['teams'][side]
        players = team_boxscore.get('players', {})
        batting_order = team_boxscore.get('battingOrder', [])
        lineup = []

        for player_id in batting_order:
            player = players.get(f'ID{player_id}')
            if player and player.get('position', {}).get('abbreviation') != 'P':
                person = player['person']
                lineup.append({
                    'batter_id': person['id'],
                    'hand': player.get('batSide', {}).get('code', 'R'),
                    'name': person['fullName'],
                })

        if len(lineup) < 9:
            lineup = self._roster_lineup(team['id'])

        return {
            'team_name': team['name'],
            'team_id': team['id'],
            'lineup': lineup[:9],
        }

    def _roster_lineup(self, team_id: int) -> List[Dict]:
        lineup = []
        for player in self._mlb_roster(team_id):
            if player.get('position', {}).get('abbreviation') == 'P':
                continue
            person = player['person']
            lineup.append({
                'batter_id': person['id'],
                'hand': player.get('batSide', {}).get('code', 'R'),
                'name': person['fullName'],
            })
            if len(lineup) == 9:
                break
        if len(lineup) < 9:
            raise RuntimeError(f'MLB roster has no complete lineup for team {team_id}')
        return lineup

    def _mlb_pitchers(self, game: Dict, boxscore: Dict, side: str) -> List[Dict]:
        scheduled_pitcher = game['teams'][side].get('probablePitcher')
        if scheduled_pitcher:
            return [{
                'pitcher_id': scheduled_pitcher['id'],
                'hand': scheduled_pitcher.get('pitchHand', {}).get('code', 'R'),
                'name': scheduled_pitcher['fullName'],
            }]

        pitchers = []
        for player in boxscore['teams'][side].get('pitchers', []):
            details = boxscore['teams'][side].get('players', {}).get(f'ID{player}')
            if details:
                pitchers.append({
                    'pitcher_id': details['person']['id'],
                    'hand': details.get('pitchHand', {}).get('code', 'R'),
                    'name': details['person']['fullName'],
                })

        if not pitchers:
            for player in self._mlb_roster(game['teams'][side]['team']['id']):
                if player.get('position', {}).get('abbreviation') != 'P':
                    continue
                pitchers.append({
                    'pitcher_id': player['person']['id'],
                    'hand': player.get('pitchHand', {}).get('code', 'R'),
                    'name': player['person']['fullName'],
                })
                if pitchers:
                    break

        if not pitchers:
            raise RuntimeError(f'MLB roster has no {side} pitcher')
        return pitchers

    def _mlb_roster(self, team_id: int) -> List[Dict]:
        roster = self._request_external(
            f'/teams/{team_id}/roster',
            {'rosterType': 'active'}
        )
        return roster.get('roster', [])

    def _request_json(self, path: str, params: Dict = None) -> Dict:
        return self._request_url(f'{self.api_base_url}{path}', params)

    @staticmethod
    def _request_external(path: str, params: Dict = None) -> Dict:
        return RealDataProvider._request_url(
            f'https://statsapi.mlb.com/api/v1{path}', params
        )

    @staticmethod
    def _request_url(url: str, params: Dict = None) -> Dict:
        if params:
            url = f'{url}?{urlencode(params)}'
        request = Request(url, headers={'Accept': 'application/json'})
        with urlopen(request, timeout=15) as response:
            return json.load(response)

    def _load_json(self, filename: str) -> Optional[Dict]:
        path = self.data_dir / filename
        if not path.exists():
            return None
        try:
            with path.open() as file:
                return json.load(file)
        except (OSError, ValueError) as error:
            logger.warning("Could not read cached game data: %s", error)
            return None

    def _save_json(self, filename: str, payload: Dict) -> None:
        with (self.data_dir / filename).open('w') as file:
            json.dump(payload, file, indent=2)

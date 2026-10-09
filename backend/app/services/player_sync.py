from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import Player, Team

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import requests


MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
CURRENT_SEASON = 2026

def create_retry_session():
    retry_strategy = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    return session


SESSION = create_retry_session()

def parse_date(value):
    """Convert MLB's YYYY-MM-DD strings into Python date objects."""
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def fetch_team_player_map():
    """
    Build a mapping of:
        mlbam_id -> {
            team_id,
            jersey_number
        }

    Uses each MLB team's 40-man roster.
    """

    teams_response = SESSION.get(
        f"{MLB_API_BASE}/teams",
        params={
            "sportId": 1,
            "season": CURRENT_SEASON,
        },
        timeout=(10, 30),
    )

    teams_response.raise_for_status()

    teams = teams_response.json().get("teams", [])

    player_team_map = {}

    for team in teams:
        team_id = team["id"]

        roster_response = SESSION.get(
            f"{MLB_API_BASE}/teams/{team_id}/roster",
            params={
                "rosterType": "40Man",
                "season": CURRENT_SEASON,
            },
            timeout=(10, 60),
        )

        roster_response.raise_for_status()

        roster = roster_response.json().get("roster", [])

        for roster_player in roster:
            person = roster_player.get("person", {})
            mlbam_id = person.get("id")

            if mlbam_id is None:
                continue

            player_team_map[mlbam_id] = {
                "mlb_team_id": team_id,
                "jersey_number": roster_player.get("jerseyNumber"),
            }

    return player_team_map


def fetch_mlb_players():
    """
    Fetch MLB players for the current season and normalize them
    into the format expected by our Player database model.
    """

    response = SESSION.get(
        f"{MLB_API_BASE}/sports/1/players",
        params={
            "season": CURRENT_SEASON,
        },
        timeout=(10, 60),
    )

    response.raise_for_status()

    raw_players = response.json().get("people", [])

    # Get current team + jersey number information separately.
    team_map = fetch_team_player_map()

    players = []

    for player in raw_players:
        mlbam_id = player.get("id")

        if mlbam_id is None:
            continue

        team_info = team_map.get(mlbam_id, {})

        primary_position = player.get("primaryPosition", {})
        bat_side = player.get("batSide", {})
        pitch_hand = player.get("pitchHand", {})

        normalized_player = {
            "mlbam_id": mlbam_id,

            "first_name": player.get("firstName"),
            "last_name": player.get("lastName"),
            "full_name": player.get("fullName"),

            "position": primary_position.get("abbreviation"),

            "jersey_number": team_info.get("jersey_number"),

            "bat_side": bat_side.get("code"),
            "pitch_hand": pitch_hand.get("code"),

            "mlb_team_id": team_info.get("mlb_team_id"),

            "active": player.get("active"),

            "birth_date": parse_date(
                player.get("birthDate")
            ),

            "height": player.get("height"),
            "weight": player.get("weight"),

            "mlb_debut_date": parse_date(
                player.get("mlbDebutDate")
            ),
        }

        players.append(normalized_player)

    return players

def sync_players():
    db = SessionLocal()

    try:
        print("Fetching MLB players...")
        players_data = fetch_mlb_players()

        print(f"Fetched {len(players_data)} players.")

        # MLB team ID -> our internal teams.id
        teams = db.query(Team).all()

        team_id_map = {
            team.mlb_team_id: team.id
            for team in teams
        }

        added = 0
        updated = 0

        for player_data in players_data:
            mlbam_id = player_data["mlbam_id"]

            player = (
                db.query(Player)
                .filter(Player.mlbam_id == mlbam_id)
                .first()
            )

            mlb_team_id = player_data.get("mlb_team_id")

            internal_team_id = (
                team_id_map.get(mlb_team_id)
                if mlb_team_id is not None
                else None
            )

            if player is None:
                player = Player(
                    mlbam_id=mlbam_id,
                    first_name=player_data.get("first_name"),
                    last_name=player_data.get("last_name"),
                    full_name=player_data.get("full_name"),
                    position=player_data.get("position"),
                    jersey_number=player_data.get("jersey_number"),
                    bat_side=player_data.get("bat_side"),
                    pitch_hand=player_data.get("pitch_hand"),
                    team_id=internal_team_id,
                    active=player_data.get("active"),
                    birth_date=player_data.get("birth_date"),
                    height=player_data.get("height"),
                    weight=player_data.get("weight"),
                    mlb_debut_date=player_data.get("mlb_debut_date"),
                )

                db.add(player)
                added += 1

            else:
                player.first_name = player_data.get("first_name")
                player.last_name = player_data.get("last_name")
                player.full_name = player_data.get("full_name")
                player.position = player_data.get("position")
                player.jersey_number = player_data.get("jersey_number")
                player.bat_side = player_data.get("bat_side")
                player.pitch_hand = player_data.get("pitch_hand")
                player.team_id = internal_team_id
                player.active = player_data.get("active")
                player.birth_date = player_data.get("birth_date")
                player.height = player_data.get("height")
                player.weight = player_data.get("weight")
                player.mlb_debut_date = player_data.get("mlb_debut_date")

                updated += 1

        db.commit()

        print("\nPlayer sync complete.")
        print(f"Added:   {added}")
        print(f"Updated: {updated}")
        print(f"Total:   {len(players_data)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    sync_players()

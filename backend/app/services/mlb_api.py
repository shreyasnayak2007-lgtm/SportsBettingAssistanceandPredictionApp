import requests


MLB_API_BASE_URL = "https://statsapi.mlb.com/api/v1"


def get_mlb_teams():
    response = requests.get(
        f"{MLB_API_BASE_URL}/teams",
        params={"sportId": 1},
        timeout=10
    )

    response.raise_for_status()

    return response.json()["teams"]

def get_mlb_games(start_date: str, end_date: str):
    response = requests.get(
        f"{MLB_API_BASE_URL}/schedule",
        params={
            "sportId": 1,
            "startDate": start_date,
            "endDate": end_date,
            "hydrate": "linescore",
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_mlb_live_game(game_pk: int):
    response = requests.get(
        f"{MLB_API_BASE_URL.rsplit('/v1', 1)[0]}/v1.1/game/{game_pk}/feed/live",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()

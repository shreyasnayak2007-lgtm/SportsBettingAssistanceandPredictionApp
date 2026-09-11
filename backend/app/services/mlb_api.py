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
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()

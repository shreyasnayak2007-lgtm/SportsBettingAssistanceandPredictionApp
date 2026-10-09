from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import Game, Team
from app.services.mlb_api import get_mlb_games, get_mlb_live_game
from datetime import date, datetime


def sync_games(
    start_date: str,
    end_date: str,
    verbose: bool = True
):
    data = get_mlb_games(start_date, end_date)

    db = SessionLocal()

    try:
        # Map MLB team ID -> our internal database team ID
        teams = db.scalars(select(Team)).all()

        team_id_map = {
            team.mlb_team_id: team.id
            for team in teams
        }

        synced_count = 0

        for date_group in data.get("dates", []):
            game_date = date.fromisoformat(date_group["date"])

            for game in date_group.get("games", []):
                linescore = game.get("linescore", {})
                home = game["teams"]["home"]
                away = game["teams"]["away"]

                home_mlb_id = home["team"]["id"]
                away_mlb_id = away["team"]["id"]

                home_team_id = team_id_map.get(home_mlb_id)
                away_team_id = team_id_map.get(away_mlb_id)

                if home_team_id is None or away_team_id is None:
                    print(
                        f"Skipping game {game['gamePk']}: "
                        "team not found in database."
                    )
                    continue

                runner_state = {
                    "first": False,
                    "second": False,
                    "third": False,
                }

                if game["status"].get("abstractGameState") == "Live":
                    try:
                        live_game = get_mlb_live_game(game["gamePk"])
                        runner_state = _get_current_runner_state(live_game)
                    except Exception as error:
                        print(
                            f"Could not load runners for game {game['gamePk']}: "
                            f"{error}"
                        )

                values = {
                    "game_pk": game["gamePk"],
                    "game_date": game_date,

                    "game_datetime": datetime.fromisoformat(
                        game["gameDate"].replace("Z", "+00:00")
                    ),

                    "season": int(
                        game.get("season", game_date.year)
                    ),

                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,

                    "home_score": home.get("score"),
                    "away_score": away.get("score"),

                    "status": game["status"]["detailedState"],

                    "current_inning": linescore.get(
                        "currentInning"
                    ),

                    "inning_state": linescore.get(
                        "inningState"
                    ),

                    "outs": linescore.get("outs"),

                        "runner_on_first": runner_state["first"],
                        "runner_on_second": runner_state["second"],
                        "runner_on_third": runner_state["third"],
                }

                statement = insert(Game).values(**values)

                statement = statement.on_conflict_do_update(
                    index_elements=["game_pk"],
                    set_={
                        "game_date": values["game_date"],
                        "game_datetime": values["game_datetime"],

                        "season": values["season"],

                        "home_team_id": values["home_team_id"],
                        "away_team_id": values["away_team_id"],

                        "home_score": values["home_score"],
                        "away_score": values["away_score"],

                        "status": values["status"],

                        "current_inning": values["current_inning"],
                        "inning_state": values["inning_state"],
                        "outs": values["outs"],

                        "runner_on_first": values["runner_on_first"],
                        "runner_on_second": values["runner_on_second"],
                        "runner_on_third": values["runner_on_third"],
                    }
                )

                db.execute(statement)
                synced_count += 1

        db.commit()

        if verbose:
            print(
                f"Successfully synced {synced_count} games "
                f"from {start_date} to {end_date}."
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def _get_current_runner_state(live_game: dict) -> dict[str, bool]:
    """Reconstruct base occupancy from MLB's live play-by-play movements."""
    plays = live_game.get("liveData", {}).get("plays", {}).get("allPlays", [])
    bases: dict[str, int] = {}
    current_half = None

    for play in plays:
        about = play.get("about", {})
        half = (about.get("inning"), about.get("isTopInning"))
        if half != current_half:
            bases = {}
            current_half = half

        for runner in play.get("runners", []):
            details = runner.get("details", {})
            runner_id = details.get("runner", {}).get("id")
            movement = runner.get("movement", {})
            start = movement.get("start")
            end = movement.get("end")

            if runner_id is not None:
                for base, occupant in list(bases.items()):
                    if occupant == runner_id:
                        del bases[base]

            if movement.get("isOut") or end in (None, "4B"):
                continue

            if runner_id is not None and end in ("1B", "2B", "3B"):
                bases[end] = runner_id

    return {
        "first": "1B" in bases,
        "second": "2B" in bases,
        "third": "3B" in bases,
    }


if __name__ == "__main__":
    today = datetime.now(
        ZoneInfo("America/New_York")
    ).date().isoformat()

    sync_games(
        today,
        today
    )

from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import Game, Team
from app.services.mlb_api import get_mlb_games
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
                offense = linescore.get("offense", {})
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

                    "runner_on_first": (
                            offense.get("first") is not None
                    ),

                    "runner_on_second": (
                            offense.get("second") is not None
                    ),

                    "runner_on_third": (
                            offense.get("third") is not None
                    ),
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


if __name__ == "__main__":
    today = datetime.now(
        ZoneInfo("America/New_York")
    ).date().isoformat()

    sync_games(
        today,
        today
    )

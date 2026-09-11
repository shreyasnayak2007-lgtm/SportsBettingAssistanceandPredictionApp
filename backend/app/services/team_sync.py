from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import Team
from app.services.mlb_api import get_mlb_teams


def sync_teams():
    teams = get_mlb_teams()

    db = SessionLocal()

    try:
        for team in teams:

            values = {
                "mlb_team_id": team["id"],
                "abbreviation": team["abbreviation"],
                "name": team["name"],
                "league": team.get("league", {}).get("name"),
                "division": team.get("division", {}).get("name"),
            }

            statement = insert(Team).values(**values)

            statement = statement.on_conflict_do_update(
                index_elements=["mlb_team_id"],
                set_={
                    "abbreviation": values["abbreviation"],
                    "name": values["name"],
                    "league": values["league"],
                    "division": values["division"],
                }
            )

            db.execute(statement)

        db.commit()

        print(f"Successfully synced {len(teams)} MLB teams.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sync_teams()

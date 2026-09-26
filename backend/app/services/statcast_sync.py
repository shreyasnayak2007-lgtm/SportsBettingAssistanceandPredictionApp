from datetime import date

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import StatcastPitch
from app.services.pybaseball_service import get_statcast_data


def clean_value(value):
    """
    Convert pandas/NumPy missing values into None so PostgreSQL
    receives proper NULL values.
    """
    if pd.isna(value):
        return None

    return value


def sync_statcast(start_date: str, end_date: str):
    db = SessionLocal()

    try:
        print(
            f"Fetching Statcast data from "
            f"{start_date} to {end_date}..."
        )

        data = get_statcast_data(
            start_date=start_date,
            end_date=end_date,
        )

        if data.empty:
            print("No Statcast data returned.")
            return

        print(f"Fetched {len(data)} pitches.")

        rows = []

        for _, row in data.iterrows():
            rows.append({
                "game_pk": int(row["game_pk"]),
                "game_date": row["game_date"],

                "home_team": clean_value(row.get("home_team")),
                "away_team": clean_value(row.get("away_team")),

                "inning": clean_value(row.get("inning")),
                "inning_topbot": clean_value(
                    row.get("inning_topbot")
                ),

                "at_bat_number": int(row["at_bat_number"]),
                "pitch_number": int(row["pitch_number"]),

                "pitcher_id": clean_value(
                    row.get("pitcher_id")
                ),
                "batter_id": clean_value(
                    row.get("batter_id")
                ),

                "pitch_type": clean_value(
                    row.get("pitch_type")
                ),
                "release_speed": clean_value(
                    row.get("release_speed")
                ),

                "balls": clean_value(row.get("balls")),
                "strikes": clean_value(row.get("strikes")),

                "events": clean_value(row.get("events")),
                "description": clean_value(
                    row.get("description")
                ),

                "launch_speed": clean_value(
                    row.get("launch_speed")
                ),
                "launch_angle": clean_value(
                    row.get("launch_angle")
                ),

                "estimated_woba": clean_value(
                    row.get("estimated_woba")
                ),
            })

        stmt = insert(StatcastPitch).values(rows)

        stmt = stmt.on_conflict_do_update(
            constraint="unique_pitch",
            set_={
                "game_date": stmt.excluded.game_date,
                "home_team": stmt.excluded.home_team,
                "away_team": stmt.excluded.away_team,

                "inning": stmt.excluded.inning,
                "inning_topbot": stmt.excluded.inning_topbot,

                "pitcher_id": stmt.excluded.pitcher_id,
                "batter_id": stmt.excluded.batter_id,

                "pitch_type": stmt.excluded.pitch_type,
                "release_speed": stmt.excluded.release_speed,

                "balls": stmt.excluded.balls,
                "strikes": stmt.excluded.strikes,

                "events": stmt.excluded.events,
                "description": stmt.excluded.description,

                "launch_speed": stmt.excluded.launch_speed,
                "launch_angle": stmt.excluded.launch_angle,

                "estimated_woba": stmt.excluded.estimated_woba,
            },
        )

        db.execute(stmt)
        db.commit()

        print("\nStatcast sync complete.")
        print(f"Processed: {len(rows)} pitches")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sync_statcast(
        start_date="2026-09-24",
        end_date="2026-09-24",
    )

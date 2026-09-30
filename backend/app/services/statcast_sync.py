import sys
from datetime import date, timedelta

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import StatcastPitch
from app.services.pybaseball_service import get_statcast_data


BATCH_SIZE = 1000


def clean_value(value):
    """
    Convert pandas/NumPy missing values into None
    and NumPy scalar values into normal Python values.
    """
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def sync_statcast_day(day: str):
    db = SessionLocal()

    try:
        print(f"\nFetching Statcast data for {day}...")

        data = get_statcast_data(
            start_date=day,
            end_date=day,
        )

        if data.empty:
            print(f"No Statcast data returned for {day}.")
            return 0

        print(f"Fetched {len(data)} pitches.")

        rows = []

        for _, row in data.iterrows():
            rows.append({
                "game_pk": int(row["game_pk"]),
                "game_date": row["game_date"],

                "home_team": clean_value(
                    row.get("home_team")
                ),
                "away_team": clean_value(
                    row.get("away_team")
                ),

                "inning": clean_value(
                    row.get("inning")
                ),
                "inning_topbot": clean_value(
                    row.get("inning_topbot")
                ),

                "at_bat_number": int(
                    row["at_bat_number"]
                ),
                "pitch_number": int(
                    row["pitch_number"]
                ),

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

                "balls": clean_value(
                    row.get("balls")
                ),
                "strikes": clean_value(
                    row.get("strikes")
                ),

                "events": clean_value(
                    row.get("events")
                ),
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

        total_batches = (
            len(rows) + BATCH_SIZE - 1
        ) // BATCH_SIZE

        for batch_number, start in enumerate(
            range(0, len(rows), BATCH_SIZE),
            start=1,
        ):
            batch = rows[start:start + BATCH_SIZE]

            stmt = insert(
                StatcastPitch
            ).values(batch)

            stmt = stmt.on_conflict_do_update(
                constraint="unique_pitch",
                set_={
                    "game_date":
                        stmt.excluded.game_date,

                    "home_team":
                        stmt.excluded.home_team,

                    "away_team":
                        stmt.excluded.away_team,

                    "inning":
                        stmt.excluded.inning,

                    "inning_topbot":
                        stmt.excluded.inning_topbot,

                    "pitcher_id":
                        stmt.excluded.pitcher_id,

                    "batter_id":
                        stmt.excluded.batter_id,

                    "pitch_type":
                        stmt.excluded.pitch_type,

                    "release_speed":
                        stmt.excluded.release_speed,

                    "balls":
                        stmt.excluded.balls,

                    "strikes":
                        stmt.excluded.strikes,

                    "events":
                        stmt.excluded.events,

                    "description":
                        stmt.excluded.description,

                    "launch_speed":
                        stmt.excluded.launch_speed,

                    "launch_angle":
                        stmt.excluded.launch_angle,

                    "estimated_woba":
                        stmt.excluded.estimated_woba,
                },
            )

            db.execute(stmt)

            print(
                f"Processed batch "
                f"{batch_number}/{total_batches} "
                f"({len(batch)} pitches)"
            )

        # Commit this day independently.
        db.commit()

        print(
            f"Completed {day}: "
            f"{len(rows)} pitches processed."
        )

        return len(rows)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def sync_statcast_range(
    start_date: str,
    end_date: str,
):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start > end:
        raise ValueError(
            "start_date cannot be after end_date"
        )

    current = start
    total_processed = 0
    days_processed = 0

    while current <= end:
        day_string = current.isoformat()

        processed = sync_statcast_day(
            day_string
        )

        total_processed += processed
        days_processed += 1

        current += timedelta(days=1)

    print("\nStatcast range sync complete.")
    print(f"Days checked:      {days_processed}")
    print(f"Pitches processed: {total_processed}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: py -m app.services.statcast_sync "
            "YYYY-MM-DD YYYY-MM-DD"
        )
        sys.exit(1)

    sync_statcast_range(
        start_date=sys.argv[1],
        end_date=sys.argv[2],
    )

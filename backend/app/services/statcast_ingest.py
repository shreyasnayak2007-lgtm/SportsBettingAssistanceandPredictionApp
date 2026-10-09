from datetime import date, datetime
import argparse
import calendar

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import StatcastPitch
from app.services.pybaseball_service import get_statcast_data


def dataframe_to_records(data: pd.DataFrame) -> list[dict]:
    """
    Convert pandas DataFrame values into normal Python values
    that PostgreSQL can safely accept.
    """

    def clean(value):
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        if pd.isna(value):
            return None
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, (date, datetime)):
            return value
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    return [
        {key: clean(value) for key, value in record.items()}
        for record in data.to_dict(orient="records")
    ]


def save_statcast_data(data: pd.DataFrame) -> int:
    if data.empty:
        return 0

    records = dataframe_to_records(data)

    db = SessionLocal()

    try:
        inserted_count = 0
        chunk_size = 1000

        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]

            dialect = db.bind.dialect.name
            if dialect == "postgresql":
                statement = postgresql_insert(StatcastPitch).values(chunk)
            elif dialect == "sqlite":
                statement = sqlite_insert(StatcastPitch).values(chunk)
            else:
                for record in chunk:
                    existing = db.scalar(select(StatcastPitch).where(
                        StatcastPitch.game_pk == record["game_pk"],
                        StatcastPitch.at_bat_number == record["at_bat_number"],
                        StatcastPitch.pitch_number == record["pitch_number"],
                    ))
                    if existing is None:
                        db.add(StatcastPitch(**record))
                        inserted_count += 1
                    else:
                        for key, value in record.items():
                            setattr(existing, key, value)
                        inserted_count += 1
                continue

            update_fields = {
                column.name: getattr(statement.excluded, column.name)
                for column in StatcastPitch.__table__.columns
                if column.name not in {"id", "game_pk", "at_bat_number", "pitch_number"}
            }
            statement = statement.on_conflict_do_update(
                index_elements=["game_pk", "at_bat_number", "pitch_number"],
                set_=update_fields,
            )

            result = db.execute(statement)

            if result.rowcount is not None:
                inserted_count += result.rowcount

        db.commit()

        return inserted_count

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def import_statcast_data(
    start_date: str,
    end_date: str
) -> int:

    print(
        f"Downloading Statcast data "
        f"from {start_date} to {end_date}..."
    )

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must not be earlier than start_date")

    total_upserted = 0
    cursor = start
    while cursor <= end:
        month_end = cursor.replace(
            day=calendar.monthrange(cursor.year, cursor.month)[1]
        )
        chunk_end = min(end, month_end)
        print(f"Downloading Statcast data from {cursor} to {chunk_end}...")
        data = get_statcast_data(cursor.isoformat(), chunk_end.isoformat())
        upserted = save_statcast_data(data)
        total_upserted += upserted
        print(f"Retrieved {len(data)} pitches; upserted {upserted}.")
        cursor = date.fromordinal(chunk_end.toordinal() + 1)

    return total_upserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import monthly Statcast pitch data")
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    import_statcast_data(args.start_date, args.end_date)

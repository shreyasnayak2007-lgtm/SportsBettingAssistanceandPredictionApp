import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from app.db.database import SessionLocal
from app.db.models import StatcastPitch
from app.services.pybaseball_service import get_statcast_data


def dataframe_to_records(data: pd.DataFrame) -> list[dict]:
    """
    Convert pandas DataFrame values into normal Python values
    that PostgreSQL can safely accept.
    """

    data = data.astype(object)

    data = data.where(
        pd.notna(data),
        None
    )

    return data.to_dict(orient="records")


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

            statement = insert(StatcastPitch).values(chunk)

            statement = statement.on_conflict_do_nothing(
                index_elements=[
                    "game_pk",
                    "at_bat_number",
                    "pitch_number"
                ]
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
) -> None:

    print(
        f"Downloading Statcast data "
        f"from {start_date} to {end_date}..."
    )

    data = get_statcast_data(
        start_date,
        end_date
    )

    print(f"Retrieved {len(data)} pitches.")

    inserted = save_statcast_data(data)

    print(
        f"Inserted {inserted} new pitches "
        f"into PostgreSQL."
    )


if __name__ == "__main__":
    import_statcast_data(
        "2025-07-01",
        "2025-07-01"
    )

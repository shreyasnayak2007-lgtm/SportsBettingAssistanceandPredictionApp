from sqlalchemy import inspect, text

from app.db.database import Base, engine
from app.db import models


def migrate_existing_player_schema():
    if engine is None:
        return

    columns = {column["name"] for column in inspect(engine).get_columns("players")}
    additions = {
        "full_name": "VARCHAR(100)",
        "bat_side": "VARCHAR(1)",
        "pitch_hand": "VARCHAR(1)",
        "active": "BOOLEAN",
        "birth_date": "DATE",
        "height": "VARCHAR(10)",
        "weight": "INTEGER",
        "mlb_debut_date": "DATE",
        "updated_at": "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP"
        if engine.dialect.name == "postgresql"
        else "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    }

    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE players ADD COLUMN {name} {definition}"))


def migrate_existing_stats_schema():
    if engine is None:
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    additions = {
        "batting_season_stats": {
            "singles": "INTEGER",
            "raw_data": "JSON",
        },
        "statcast_pitches": {
            "release_spin_rate": "FLOAT",
            "release_extension": "FLOAT",
            "plate_x": "FLOAT",
            "plate_z": "FLOAT",
            "zone": "INTEGER",
            "stand": "VARCHAR(1)",
            "p_throws": "VARCHAR(1)",
            "launch_speed_angle": "INTEGER",
            "hit_distance_sc": "FLOAT",
            "estimated_ba": "FLOAT",
            "barrel": "BOOLEAN",
            "raw_data": "JSON",
        },
        "pitching_season_stats": {
            "pitches": "INTEGER",
            "singles_allowed": "INTEGER",
            "doubles_allowed": "INTEGER",
            "triples_allowed": "INTEGER",
            "batting_average_against": "FLOAT",
            "raw_data": "JSON",
        },
    }

    with engine.begin() as connection:
        for table_name, table_additions in additions.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, definition in table_additions.items():
                if column_name not in existing_columns:
                    connection.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN "
                        f"{column_name} {definition}"
                    ))


def create_tables():
    Base.metadata.create_all(bind=engine)
    migrate_existing_player_schema()
    migrate_existing_stats_schema()
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()

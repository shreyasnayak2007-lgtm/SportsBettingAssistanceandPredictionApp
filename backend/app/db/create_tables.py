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


def create_tables():
    Base.metadata.create_all(bind=engine)
    migrate_existing_player_schema()
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()

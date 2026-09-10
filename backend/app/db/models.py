from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    UniqueConstraint
)

from app.db.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    abbreviation = Column(String(5), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    league = Column(String(10))
    division = Column(String(20))


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    # MLB's ID for the player
    mlbam_id = Column(Integer, unique=True, nullable=False, index=True)

    first_name = Column(String(50))
    last_name = Column(String(50))
    position = Column(String(20))

    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)

    # MLB's unique ID for the game
    game_pk = Column(Integer, unique=True, nullable=False, index=True)

    game_date = Column(Date, nullable=False, index=True)
    season = Column(Integer, nullable=False)

    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))

    home_score = Column(Integer)
    away_score = Column(Integer)

    status = Column(String(30))


class StatcastPitch(Base):
    __tablename__ = "statcast_pitches"

    id = Column(Integer, primary_key=True, index=True)

    game_pk = Column(Integer, nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)

    home_team = Column(String(5))
    away_team = Column(String(5))

    inning = Column(Integer)
    inning_topbot = Column(String(10))

    at_bat_number = Column(Integer, nullable=False)
    pitch_number = Column(Integer, nullable=False)

    # These are MLBAM player IDs from Statcast
    pitcher_id = Column(Integer, index=True)
    batter_id = Column(Integer, index=True)

    pitch_type = Column(String(10))
    release_speed = Column(Float)

    balls = Column(Integer)
    strikes = Column(Integer)

    events = Column(String(50))
    description = Column(String(100))

    launch_speed = Column(Float)
    launch_angle = Column(Float)

    estimated_woba = Column(Float)

    __table_args__ = (
        UniqueConstraint(
            "game_pk",
            "at_bat_number",
            "pitch_number",
            name="unique_pitch"
        ),
    )

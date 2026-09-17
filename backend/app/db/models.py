from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.sql import func

from app.db.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    mlb_team_id = Column(
        Integer,
        unique=True,
        nullable=False,
        index=True
    )

    abbreviation = Column(
        String(5),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(String(100), nullable=False)
    league = Column(String(50))
    division = Column(String(50))


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    # Official MLB player ID
    mlbam_id = Column(Integer, unique=True, nullable=False, index=True)

    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    full_name = Column(String(100), nullable=True)

    position = Column(String(20), nullable=True)

    # String instead of Integer so values such as "00" are preserved
    jersey_number = Column(String(3), nullable=True)

    # Batting side: L, R, S
    bat_side = Column(String(1), nullable=True)

    # Throwing hand: L, R
    pitch_hand = Column(String(1), nullable=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=True
    )

    active = Column(Boolean, nullable=True)

    birth_date = Column(Date, nullable=True)
    height = Column(String(10), nullable=True)
    weight = Column(Integer, nullable=True)

    mlb_debut_date = Column(Date, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)

    game_pk = Column(
        Integer,
        unique=True,
        nullable=False,
        index=True
    )

    game_date = Column(
        Date,
        nullable=False,
        index=True
    )

    # Exact scheduled start time from MLB.
    # Stored with timezone information.
    game_datetime = Column(
        DateTime(timezone=True),
        nullable=True
    )

    season = Column(
        Integer,
        nullable=False
    )

    home_team_id = Column(
        Integer,
        ForeignKey("teams.id")
    )

    away_team_id = Column(
        Integer,
        ForeignKey("teams.id")
    )

    home_score = Column(Integer)
    away_score = Column(Integer)

    status = Column(String(30))

    # Live game information
    current_inning = Column(Integer)
    inning_state = Column(String(20))
    outs = Column(Integer)

    runner_on_first = Column(
        Boolean,
        default=False
    )

    runner_on_second = Column(
        Boolean,
        default=False
    )

    runner_on_third = Column(
        Boolean,
        default=False
    )


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

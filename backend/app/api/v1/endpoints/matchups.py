# backend/app/api/v1/endpoints/matchups.py
"""
Matchups endpoint: serves detailed game matchup information
including lineups, BvP stats, rolling trends, and badges.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Game, Player, Team, StatcastPitch
#from app.services.statscast import get_bvp_stats, get_rolling_trends
#from app.services.badge_engine import evaluate_badges
#from app.services.pybaseball_service import get_park_factor

router = APIRouter()


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class Badge(BaseModel):
    """Performance badge for a batter in this matchup"""
    type: Literal["hot_streak", "handedness", "ballpark", "bvp_advantage"]
    strength: Literal["strong", "moderate", "weak"]
    value: str
    tooltip: str

    class Config:
        json_schema_extra = {
            "example": {
                "type": "hot_streak",
                "strength": "strong",
                "value": "8-20 last 10 games",
                "tooltip": "This batter is hot recently"
            }
        }


class BvPStats(BaseModel):
    """Batter vs Pitcher career statistics"""
    careerAB: int
    careerH: int
    careerAVG: float
    careerSLG: float
    careerOBP: float
    vsRHP: dict  # {AB, H, AVG, SLG, OBP}
    vsLHP: dict

    class Config:
        json_schema_extra = {
            "example": {
                "careerAB": 1523,
                "careerH": 412,
                "careerAVG": 0.271,
                "careerSLG": 0.445,
                "careerOBP": 0.334,
                "vsRHP": {"AB": 1000, "H": 285, "AVG": 0.285, "SLG": 0.470, "OBP": 0.350},
                "vsLHP": {"AB": 523, "H": 127, "AVG": 0.243, "SLG": 0.385, "OBP": 0.305}
            }
        }


class RollingMetric(BaseModel):
    """Rolling 20-game metric for a batter"""
    gameDate: date
    result: Literal["W", "L"]
    hits: int
    runs: int
    rbi: int
    avg: float
    hardHitRate: float

    class Config:
        json_schema_extra = {
            "example": {
                "gameDate": "2025-07-01",
                "result": "W",
                "hits": 2,
                "runs": 1,
                "rbi": 1,
                "avg": 0.285,
                "hardHitRate": 0.42
            }
        }


class BatterDetail(BaseModel):
    """Complete batter information for matchup view"""
    mlbamId: int
    name: str
    position: str
    handedness: Literal["L", "R", "S"]
    jerseyNumber: int
    bvpStats: BvPStats
    rollingTrends: list[RollingMetric]
    badges: list[Badge]

    class Config:
        json_schema_extra = {
            "example": {
                "mlbamId": 573262,
                "name": "Mitch Garver",
                "position": "C",
                "handedness": "R",
                "jerseyNumber": 18,
                "bvpStats": {},
                "rollingTrends": [],
                "badges": []
            }
        }


class PitcherInfo(BaseModel):
    """Pitcher information for matchup"""
    mlbamId: int
    name: str
    position: str = "P"
    handedness: Literal["L", "R"]
    jerseyNumber: int
    season_era: float
    last_7_days_performance: dict


class MatchupResponse(BaseModel):
    """Complete matchup detail response"""
    gamePk: int
    gameDate: date
    awayTeam: str
    homeTeam: str
    ballparkName: str
    ballparkFactor: float
    homePitcher: Optional[PitcherInfo]
    awayPitcher: Optional[PitcherInfo]
    awayLineup: list[BatterDetail]
    homeLineup: list[BatterDetail]

    class Config:
        json_schema_extra = {
            "example": {
                "gamePk": 777278,
                "gameDate": "2025-07-01",
                "awayTeam": "SF",
                "homeTeam": "AZ",
                "ballparkName": "Chase Field",
                "ballparkFactor": 1.08,
                "homePitcher": None,
                "awayPitcher": None,
                "awayLineup": [],
                "homeLineup": []
            }
        }


# ============================================================
# TEAM ID TO BALLPARK MAPPING
# ============================================================

BALLPARK_NAMES = {
    108: "Angel Stadium",
    109: "Chase Field",
    110: "Oriole Park at Camden Yards",
    111: "Fenway Park",
    112: "Wrigley Field",
    113: "Great American Ball Park",
    114: "Progressive Field",
    115: "Coors Field",
    116: "Comerica Park",
    117: "Minute Maid Park",
    118: "Kauffman Stadium",
    119: "Dodger Stadium",
    120: "Miller Park",  # Now American Family Field
    121: "Citi Field",
    133: "Target Field",
    134: "PNC Park",
    135: "Petco Park",
    136: "Citizens Bank Park",
    137: "PNC Park (Pittsburgh)",
    138: "Tropicana Field",
    139: "Tropicana Field",
    140: "Globe Life Field",
    141: "Globe Life Field",
    142: "Twins Stadium",  # Now Target Field
    143: "Citizens Bank Park",
    144: "SunTrust Park",  # Now Truist Park
    145: "Guaranteed Rate Field",
    146: "loanDepot park",
    147: "Yankee Stadium",
    158: "Sahlen Field",
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/{game_pk}", response_model=MatchupResponse)
def get_matchup_detail(
        game_pk: int,
        db: Session = Depends(get_db)
):
    """
    Get detailed matchup information for a specific game.

    Returns:
    - Game metadata
    - Home and away lineups with batter details
    - BvP stats for each batter
    - Rolling 20-game trends
    - Performance badges
    - Ballpark information

    Example:
        GET /api/v1/matchups/777278
    """

    # ========================================================
    # FETCH GAME FROM DATABASE
    # ========================================================

    game = db.query(Game).filter(
        Game.game_pk == game_pk
    ).first()

    if not game:
        raise HTTPException(
            status_code=404,
            detail=f"Game {game_pk} not found"
        )

    home_team = db.query(Team).filter(Team.id == game.home_team_id).first()
    away_team = db.query(Team).filter(Team.id == game.away_team_id).first()

    if home_team is None or away_team is None:
        raise HTTPException(
            status_code=500,
            detail=f"Teams for game {game_pk} could not be loaded"
        )

    # ========================================================
    # BUILD LINEUPS
    # ========================================================

    # Home batters hitting against away pitcher(s)
    home_lineup = _build_lineup(
        batting_team_id=game.home_team_id,
        pitching_team=away_team,
        game_date=game.game_date,
        db=db
    )

    # Away batters hitting against home pitcher(s)
    away_lineup = _build_lineup(
        batting_team_id=game.away_team_id,
        pitching_team=home_team,
        game_date=game.game_date,
        db=db
    )

    # ========================================================
    # GET BALLPARK INFO
    # ========================================================

    ballpark_name = BALLPARK_NAMES.get(
        home_team.mlb_team_id,
        f"{home_team.name} Stadium"
    )

    # Ballpark factor: 1.0 is neutral
    # > 1.0 favors hitters (higher scoring)
    # < 1.0 favors pitchers (lower scoring)
    ballpark_factor = _get_ballpark_factor(home_team.mlb_team_id)

    # ========================================================
    # RETURN RESPONSE
    # ========================================================

    return MatchupResponse(
        gamePk=game.game_pk,
        gameDate=game.game_date,
        awayTeam=away_team.abbreviation,
        homeTeam=home_team.abbreviation,
        ballparkName=ballpark_name,
        ballparkFactor=ballpark_factor,
        homePitcher=None,  # TODO: wire when pitcher data available
        awayPitcher=None,  # TODO: wire when pitcher data available
        awayLineup=away_lineup,
        homeLineup=home_lineup
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _build_lineup(
        batting_team_id: int,
        pitching_team: Team,
        game_date: date,
        db: Session
) -> list[BatterDetail]:
    """
    Build complete lineup for a team in a specific matchup.

    Args:
        batting_team_id: Team ID of batters
        pitching_team: Team object of pitchers (for BvP context)
        game_date: Date of game
        db: Database session

    Returns:
        List of BatterDetail objects ordered by typical lineup
    """

    # Query batters on this team, excluding pitchers
    batters = db.query(Player).filter(
        Player.team_id == batting_team_id,
        Player.position.in_(["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"])
    ).order_by(
        Player.position  # Rough lineup order
    ).all()

    if not batters:
        # No players found, return empty lineup
        return []

    lineup = []

    for batter in batters:
        try:
            # Get career BvP stats vs this pitching team
            bvp_stats = _get_bvp_stats(
                batter.mlbam_id,
                pitching_team.id,
                db
            )

            # Get rolling 20-game trends
            rolling_trends = _get_rolling_trends(
                batter.mlbam_id,
                game_date,
                db
            )

            # Evaluate performance badges
            badges = _evaluate_badges(
                batter.mlbam_id,
                bvp_stats,
                rolling_trends,
                pitching_team,
                game_date,
                db
            )

            batter_detail = BatterDetail(
                mlbamId=batter.mlbam_id,
                name=f"{batter.first_name} {batter.last_name}".strip(),
                position=batter.position or "DH",
                handedness=batter.bat_side or "R",
                jerseyNumber=batter.jersey_number or 0,
                bvpStats=bvp_stats,
                rollingTrends=rolling_trends,
                badges=badges
            )

            lineup.append(batter_detail)

        except Exception as e:
            # Log error and continue with next batter
            print(f"Error building detail for batter {batter.mlbam_id}: {str(e)}")
            continue

    return lineup


def _get_bvp_stats(
        batter_mlbam_id: int,
        pitching_team_id: int,
        db: Session
) -> BvPStats:
    """Aggregate the batter's recorded PA outcomes against this team's pitchers."""
    pitching_players = db.query(Player).filter(
        Player.team_id == pitching_team_id,
        Player.position.in_(["P", "TWP"]),
    ).all()
    pitcher_ids = [player.mlbam_id for player in pitching_players]
    if not pitcher_ids:
        return _empty_bvp_stats()

    pitches = db.query(StatcastPitch).filter(
        StatcastPitch.batter_id == batter_mlbam_id,
        StatcastPitch.pitcher_id.in_(pitcher_ids),
        StatcastPitch.events.is_not(None),
    ).order_by(
        StatcastPitch.game_date,
        StatcastPitch.game_pk,
        StatcastPitch.at_bat_number,
        StatcastPitch.pitch_number,
    ).all()

    pitcher_hands = {
        pitcher.mlbam_id: pitcher.pitch_hand for pitcher in pitching_players
    }
    final_pa = {}
    for pitch in pitches:
        key = (pitch.game_pk, pitch.at_bat_number)
        final_pa[key] = pitch

    events = [
        (pitch.events.lower(), (pitch.p_throws or pitcher_hands.get(pitch.pitcher_id) or "R").upper())
        for pitch in final_pa.values()
    ]

    def summarize(pa_events):
        non_at_bat = {
            "walk", "intent_walk", "intentional_walk", "hit_by_pitch",
            "sac_fly", "sac_bunt", "catcher_interf",
        }
        hit_bases = {"single": 1, "double": 2, "triple": 3, "home_run": 4}
        hits = sum(event in hit_bases for event in pa_events)
        at_bats = sum(event not in non_at_bat for event in pa_events)
        walks = sum(event in {"walk", "intent_walk", "intentional_walk"} for event in pa_events)
        hit_by_pitch = pa_events.count("hit_by_pitch")
        sac_flies = pa_events.count("sac_fly")
        total_bases = sum(hit_bases.get(event, 0) for event in pa_events)
        plate_appearances_for_obp = at_bats + walks + hit_by_pitch + sac_flies
        return {
            "AB": at_bats,
            "H": hits,
            "AVG": hits / at_bats if at_bats else 0.0,
            "SLG": total_bases / at_bats if at_bats else 0.0,
            "OBP": (hits + walks + hit_by_pitch) / plate_appearances_for_obp
            if plate_appearances_for_obp else 0.0,
        }

    all_events = [event for event, _ in events]
    right_events = [event for event, hand in events if hand == "R"]
    left_events = [event for event, hand in events if hand == "L"]
    career = summarize(all_events)
    return BvPStats(
        careerAB=career["AB"],
        careerH=career["H"],
        careerAVG=career["AVG"],
        careerSLG=career["SLG"],
        careerOBP=career["OBP"],
        vsRHP=summarize(right_events),
        vsLHP=summarize(left_events),
    )


def _empty_bvp_stats() -> BvPStats:
    empty_split = {"AB": 0, "H": 0, "AVG": 0.0, "SLG": 0.0, "OBP": 0.0}
    return BvPStats(
        careerAB=0,
        careerH=0,
        careerAVG=0.0,
        careerSLG=0.0,
        careerOBP=0.0,
        vsRHP=empty_split.copy(),
        vsLHP=empty_split.copy(),
    )


def _get_rolling_trends(
        batter_mlbam_id: int,
        game_date: date,
        db: Session
) -> list[RollingMetric]:
    """Return up to 20 recorded game-level hitting lines, newest first."""
    pitches = db.query(StatcastPitch).filter(
        StatcastPitch.batter_id == batter_mlbam_id,
        StatcastPitch.game_date < game_date,
        StatcastPitch.events.is_not(None),
    ).order_by(
        StatcastPitch.game_date.desc(),
        StatcastPitch.game_pk,
        StatcastPitch.at_bat_number,
        StatcastPitch.pitch_number,
    ).all()

    game_events = {}
    for pitch in pitches:
        game_events[(pitch.game_pk, pitch.game_date)] = game_events.get(
            (pitch.game_pk, pitch.game_date), []
        )
        game_events[(pitch.game_pk, pitch.game_date)].append(pitch)

    trends = []
    for (game_pk, played_date), game_pitches in list(game_events.items())[:20]:
        final_pa = {}
        for pitch in game_pitches:
            final_pa[(pitch.game_pk, pitch.at_bat_number)] = pitch
        events = [pitch.events.lower() for pitch in final_pa.values()]
        hits = sum(event in {"single", "double", "triple", "home_run"} for event in events)
        at_bats = sum(event not in {
            "walk", "intent_walk", "intentional_walk", "hit_by_pitch",
            "sac_fly", "sac_bunt", "catcher_interf",
        } for event in events)
        hard_hit_balls = sum(
            pitch.launch_speed is not None and pitch.launch_speed >= 95
            for pitch in game_pitches
        )
        balls_in_play = sum(pitch.launch_speed is not None for pitch in game_pitches)
        trends.append(RollingMetric(
            gameDate=played_date,
            result="W" if hits else "L",
            hits=hits,
            runs=0,
            rbi=0,
            avg=hits / at_bats if at_bats else 0.0,
            hardHitRate=hard_hit_balls / balls_in_play if balls_in_play else 0.0,
        ))
    return trends


def _evaluate_badges(
        batter_mlbam_id: int,
        bvp_stats: BvPStats,
        rolling_trends: list[RollingMetric],
        pitching_team: Team,
        game_date: date,
        db: Session
) -> list[Badge]:
    """
    Evaluate which badges apply to this batter in this matchup.

    Badge types:
    - hot_streak: Recent performance
    - handedness: Favorable handedness matchup
    - ballpark: Favorable ballpark
    - bvp_advantage: Strong BvP history

    TODO: Implement badge_engine.evaluate_badges()
    """

    badges = []

    if len(rolling_trends) >= 5 and sum(item.avg for item in rolling_trends[:5]) / 5 > 0.280:
        badges.append(Badge(
            type="hot_streak",
            strength="moderate",
            value="Above .280 over last 5 recorded games",
            tooltip="Average in the five most recent recorded games exceeds .280",
        ))

    if bvp_stats.careerAB >= 10 and bvp_stats.careerAVG > 0.300:
        badges.append(Badge(
            type="bvp_advantage",
            strength="moderate",
            value=f".{int(bvp_stats.careerAVG * 1000)} career vs team",
            tooltip=f"Career {bvp_stats.careerAVG:.3f} vs this pitching team"
        ))

    return badges


def _get_ballpark_factor(team_id: int) -> float:
    """
    Get ballpark factor for a team's home stadium.

    > 1.0 = hitter-friendly
    < 1.0 = pitcher-friendly
    1.0 = neutral

    TODO: Load from database or pybaseball
    """

    # PLACEHOLDER: Return neutral factor
    # In production, load from pybaseball or database

    return 1.0
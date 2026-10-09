import argparse
import json
import logging
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import BattingSeasonStat, PitchingSeasonStat, Player, Team

logger = logging.getLogger(__name__)
MLB_STATS_API = "https://statsapi.mlb.com/api/v1/stats"
PAGE_SIZE = 1000


def _fetch_season_splits(season: int, group: str) -> list[dict[str, Any]]:
    splits = []
    offset = 0
    while True:
        params = urlencode({
            "stats": "season",
            "group": group,
            "season": season,
            "sportIds": 1,
            "playerPool": "ALL",
            "limit": PAGE_SIZE,
            "offset": offset,
        })
        request = Request(
            f"{MLB_STATS_API}?{params}",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)

        sections = payload.get("stats", [])
        page = sections[0].get("splits", []) if sections else []
        if not page:
            break
        splits.extend(page)
        offset += len(page)
        total = payload.get("totalSplits")
        if total is None and sections:
            total = sections[0].get("totalSplits")
        if (total is not None and offset >= int(total)) or len(page) < PAGE_SIZE:
            break
    return splits


def _number(stats: dict, key: str, cast=float):
    value = stats.get(key)
    if value in (None, "", "--", "-"):
        return None
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def _ensure_player(db: Session, split: dict, teams_by_mlb_id: dict[int, int]) -> Player:
    source_player = split.get("player", {})
    mlbam_id = source_player.get("id")
    if mlbam_id is None:
        raise ValueError("MLB stats split is missing player.id")

    player = db.scalar(select(Player).where(Player.mlbam_id == mlbam_id))
    team_mlb_id = split.get("team", {}).get("id")
    team_id = teams_by_mlb_id.get(team_mlb_id)
    if player is None:
        player = Player(
            mlbam_id=mlbam_id,
            first_name=source_player.get("firstName"),
            last_name=source_player.get("lastName"),
            full_name=source_player.get("fullName"),
            position=split.get("position", {}).get("abbreviation"),
            team_id=team_id,
            active=True,
        )
        db.add(player)
        db.flush()
    elif player.team_id is None and team_id is not None:
        player.team_id = team_id
    return player


def _upsert_batting(db: Session, player: Player, season: int, stats: dict) -> None:
    hits = _number(stats, "hits", int)
    doubles = _number(stats, "doubles", int)
    triples = _number(stats, "triples", int)
    home_runs = _number(stats, "homeRuns", int)
    values = {
        "games": _number(stats, "gamesPlayed", int),
        "plate_appearances": _number(stats, "plateAppearances", int),
        "at_bats": _number(stats, "atBats", int),
        "runs": _number(stats, "runs", int),
        "hits": hits,
        "singles": hits - (doubles or 0) - (triples or 0) - (home_runs or 0)
        if hits is not None else None,
        "doubles": doubles,
        "triples": triples,
        "home_runs": home_runs,
        "rbi": _number(stats, "rbi", int),
        "walks": _number(stats, "baseOnBalls", int),
        "strikeouts": _number(stats, "strikeOuts", int),
        "stolen_bases": _number(stats, "stolenBases", int),
        "caught_stealing": _number(stats, "caughtStealing", int),
        "batting_average": _number(stats, "avg"),
        "on_base_percentage": _number(stats, "obp"),
        "slugging_percentage": _number(stats, "slg"),
        "ops": _number(stats, "ops"),
        "woba": _number(stats, "woba"),
        "wrc_plus": _number(stats, "wrcPlus"),
        "war": _number(stats, "war"),
        "raw_data": stats,
    }
    row = db.scalar(select(BattingSeasonStat).where(
        BattingSeasonStat.player_id == player.id,
        BattingSeasonStat.season == season,
    ))
    if row is None:
        row = BattingSeasonStat(player_id=player.id, season=season)
        db.add(row)
    for key, value in values.items():
        setattr(row, key, value)


def _innings_to_outs(stats: dict) -> int | None:
    outs = _number(stats, "outs", int)
    if outs is not None:
        return outs
    innings = stats.get("inningsPitched")
    if innings in (None, "", "--"):
        return None
    try:
        whole, _, fraction = str(innings).partition(".")
        return int(whole) * 3 + int((fraction or "0")[:1])
    except (TypeError, ValueError):
        return None


def _upsert_pitching(db: Session, player: Player, season: int, stats: dict) -> None:
    hits_allowed = _number(stats, "hits", int)
    doubles_allowed = _number(stats, "doubles", int)
    triples_allowed = _number(stats, "triples", int)
    home_runs_allowed = _number(stats, "homeRuns", int)
    values = {
        "games": _number(stats, "gamesPitched", int) or _number(stats, "gamesPlayed", int),
        "games_started": _number(stats, "gamesStarted", int),
        "wins": _number(stats, "wins", int),
        "losses": _number(stats, "losses", int),
        "saves": _number(stats, "saves", int),
        "holds": _number(stats, "holds", int),
        "pitches": _number(stats, "numberOfPitches", int),
        "innings_outs": _innings_to_outs(stats),
        "singles_allowed": (
            hits_allowed - (doubles_allowed or 0) - (triples_allowed or 0)
            - (home_runs_allowed or 0) if hits_allowed is not None else None
        ),
        "doubles_allowed": doubles_allowed,
        "triples_allowed": triples_allowed,
        "hits_allowed": hits_allowed,
        "runs_allowed": _number(stats, "runs", int),
        "earned_runs": _number(stats, "earnedRuns", int),
        "home_runs_allowed": home_runs_allowed,
        "walks": _number(stats, "baseOnBalls", int),
        "strikeouts": _number(stats, "strikeOuts", int),
        "hit_batters": _number(stats, "hitBatsmen", int),
        "batters_faced": _number(stats, "battersFaced", int),
        "era": _number(stats, "era"),
        "whip": _number(stats, "whip"),
        "batting_average_against": _number(stats, "avg"),
        "strikeouts_per_nine": _number(stats, "strikeoutsPer9Inn"),
        "walks_per_nine": _number(stats, "walksPer9Inn"),
        "hits_per_nine": _number(stats, "hitsPer9Inn"),
        "home_runs_per_nine": _number(stats, "homeRunsPer9"),
        "raw_data": stats,
    }
    row = db.scalar(select(PitchingSeasonStat).where(
        PitchingSeasonStat.player_id == player.id,
        PitchingSeasonStat.season == season,
    ))
    if row is None:
        row = PitchingSeasonStat(player_id=player.id, season=season)
        db.add(row)
    for key, value in values.items():
        setattr(row, key, value)


def ingest_season_stats(season: int, group: str = "both") -> dict[str, int]:
    """Fetch official MLB season totals and upsert them by MLBAM player ID."""
    if group not in {"both", "hitting", "pitching"}:
        raise ValueError("group must be 'both', 'hitting', or 'pitching'")
    groups = ("hitting", "pitching") if group == "both" else (group,)
    downloaded = {name: _fetch_season_splits(season, name) for name in groups}
    processed = {name: 0 for name in groups}
    db = SessionLocal()
    try:
        teams_by_mlb_id = {
            team.mlb_team_id: team.id for team in db.scalars(select(Team)).all()
        }
        for name, splits in downloaded.items():
            for split in splits:
                stats = split.get("stat", {})
                if not stats or split.get("player", {}).get("id") is None:
                    continue
                player = _ensure_player(db, split, teams_by_mlb_id)
                if name == "hitting":
                    _upsert_batting(db, player, season, stats)
                else:
                    _upsert_pitching(db, player, season, stats)
                processed[name] += 1
        db.commit()
        return processed
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import MLB season batting/pitching statistics"
    )
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--group", choices=("both", "hitting", "pitching"), default="both")
    args = parser.parse_args()
    if args.end_year < args.start_year:
        parser.error("--end-year must be greater than or equal to --start-year")
    for season in range(args.start_year, args.end_year + 1):
        counts = ingest_season_stats(season, args.group)
        logger.info("Imported season %s: %s", season, counts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

from app.db.database import SessionLocal
from app.db.models import Player, PitchingSeasonStat
from app.services.pybaseball_service import fetch_pitching_stats_2026


CURRENT_SEASON = 2026


def to_float(value):
    """
    Convert MLB string statistics such as '3.42' into floats.

    MLB may return placeholders such as '.---' or '-.--'.
    Those should become None.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sync_pitching_stats():
    db = SessionLocal()

    try:
        print("Fetching MLB pitching stats...")

        pitching_data = fetch_pitching_stats_2026()

        # Safety check:
        # Never delete existing pitching data if MLB unexpectedly
        # returns an empty response.
        if not pitching_data:
            raise RuntimeError(
                "MLB returned no pitching data. "
                "Aborting sync to avoid deleting existing rows."
            )

        print(f"Fetched {len(pitching_data)} pitching stat rows.")

        # MLBAM ID -> our internal players.id
        players = db.query(Player).all()

        player_id_map = {
            player.mlbam_id: player.id
            for player in players
        }

        added = 0
        updated = 0
        skipped = 0
        deleted = 0

        # Used to identify stale rows later.
        seen_player_ids = set()

        for row in pitching_data:
            player_data = row.get("player", {})
            stat = row.get("stat", {})

            mlbam_id = player_data.get("id")

            if mlbam_id is None:
                skipped += 1
                continue

            internal_player_id = player_id_map.get(mlbam_id)

            # Player does not exist in our master players table.
            if internal_player_id is None:
                print(
                    f"Skipping {player_data.get('fullName')} "
                    f"(MLBAM {mlbam_id}) - player not found"
                )
                skipped += 1
                continue

            seen_player_ids.add(internal_player_id)

            pitching_stat = (
                db.query(PitchingSeasonStat)
                .filter(
                    PitchingSeasonStat.player_id == internal_player_id,
                    PitchingSeasonStat.season == CURRENT_SEASON,
                )
                .first()
            )

            values = {
                "games": stat.get("gamesPlayed"),
                "games_started": stat.get("gamesStarted"),

                "wins": stat.get("wins"),
                "losses": stat.get("losses"),

                "saves": stat.get("saves"),
                "save_opportunities": stat.get("saveOpportunities"),

                # Keep this as a string because "6.2" means
                # 6 innings + 2 outs, not 6.2 decimal innings.
                "innings_pitched": stat.get("inningsPitched"),

                "hits_allowed": stat.get("hits"),
                "runs_allowed": stat.get("runs"),
                "earned_runs": stat.get("earnedRuns"),
                "home_runs_allowed": stat.get("homeRuns"),

                "walks": stat.get("baseOnBalls"),
                "strikeouts": stat.get("strikeOuts"),

                "batters_faced": stat.get("battersFaced"),
                "hit_batters": stat.get("hitBatsmen"),
                "wild_pitches": stat.get("wildPitches"),
                "balks": stat.get("balks"),

                "era": to_float(stat.get("era")),
                "whip": to_float(stat.get("whip")),

                "strikeouts_per_9": to_float(
                    stat.get("strikeoutsPer9Inn")
                ),
                "walks_per_9": to_float(
                    stat.get("walksPer9Inn")
                ),
                "hits_per_9": to_float(
                    stat.get("hitsPer9Inn")
                ),
                "home_runs_per_9": to_float(
                    stat.get("homeRunsPer9")
                ),
            }

            if pitching_stat is None:
                pitching_stat = PitchingSeasonStat(
                    player_id=internal_player_id,
                    season=CURRENT_SEASON,
                    **values,
                )

                db.add(pitching_stat)
                added += 1

            else:
                for field, value in values.items():
                    setattr(pitching_stat, field, value)

                updated += 1

        # Only remove stale pitching rows if every MLB pitcher
        # successfully matched our master players table.
        if skipped == 0:
            deleted = (
                db.query(PitchingSeasonStat)
                .filter(
                    PitchingSeasonStat.season == CURRENT_SEASON,
                    ~PitchingSeasonStat.player_id.in_(
                        list(seen_player_ids)
                    ),
                )
                .delete(synchronize_session=False)
            )
        else:
            print(
                "\nWarning: stale pitching rows were NOT deleted "
                "because one or more players were skipped."
            )

        db.commit()

        print("\nPitching stats sync complete.")
        print(f"Added:   {added}")
        print(f"Updated: {updated}")
        print(f"Deleted: {deleted}")
        print(f"Skipped: {skipped}")
        print(f"Total:   {len(pitching_data)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sync_pitching_stats()

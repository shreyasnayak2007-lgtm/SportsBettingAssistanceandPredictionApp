from app.db.database import SessionLocal
from app.db.models import Player, BattingSeasonStat
from app.services.pybaseball_service import fetch_batting_stats_2026


CURRENT_SEASON = 2026


def to_float(value):
    """
    Convert MLB string statistics such as '.275' into floats.

    MLB sometimes returns placeholders such as '.---' or '-.--'.
    Those should become None.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sync_batting_stats():
    db = SessionLocal()

    try:
        print("Fetching MLB batting stats...")

        batting_data = fetch_batting_stats_2026()

        # Safety check:
        # Never delete existing batting data if MLB unexpectedly
        # returns an empty response.
        if not batting_data:
            raise RuntimeError(
                "MLB returned no batting data. "
                "Aborting sync to avoid deleting existing rows."
            )

        print(f"Fetched {len(batting_data)} batting stat rows.")

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

        # Keep track of every current-season player returned by MLB.
        # This allows us to remove old rows that are no longer present
        # in MLB's current response.
        seen_player_ids = set()

        for row in batting_data:
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

            # This player exists in MLB's current batting response.
            seen_player_ids.add(internal_player_id)

            batting_stat = (
                db.query(BattingSeasonStat)
                .filter(
                    BattingSeasonStat.player_id == internal_player_id,
                    BattingSeasonStat.season == CURRENT_SEASON,
                )
                .first()
            )

            values = {
                "games": stat.get("gamesPlayed"),
                "plate_appearances": stat.get("plateAppearances"),
                "at_bats": stat.get("atBats"),

                "runs": stat.get("runs"),
                "hits": stat.get("hits"),
                "doubles": stat.get("doubles"),
                "triples": stat.get("triples"),
                "home_runs": stat.get("homeRuns"),

                "rbi": stat.get("rbi"),
                "walks": stat.get("baseOnBalls"),
                "strikeouts": stat.get("strikeOuts"),

                "stolen_bases": stat.get("stolenBases"),
                "caught_stealing": stat.get("caughtStealing"),

                "batting_average": to_float(stat.get("avg")),
                "on_base_percentage": to_float(stat.get("obp")),
                "slugging_percentage": to_float(stat.get("slg")),
                "ops": to_float(stat.get("ops")),
            }

            if batting_stat is None:
                batting_stat = BattingSeasonStat(
                    player_id=internal_player_id,
                    season=CURRENT_SEASON,
                    **values,
                )

                db.add(batting_stat)
                added += 1

            else:
                for field, value in values.items():
                    setattr(batting_stat, field, value)

                updated += 1

        # Only delete stale rows if every MLB batting player
        # successfully matched a player in our master table.
        #
        # This protects us from accidentally deleting valid data
        # if the players table is temporarily missing someone.
        if skipped == 0:
            deleted = (
                db.query(BattingSeasonStat)
                .filter(
                    BattingSeasonStat.season == CURRENT_SEASON,
                    ~BattingSeasonStat.player_id.in_(
                        list(seen_player_ids)
                    ),
                )
                .delete(synchronize_session=False)
            )
        else:
            print(
                "\nWarning: stale batting rows were NOT deleted "
                "because one or more players were skipped."
            )

        db.commit()

        print("\nBatting stats sync complete.")
        print(f"Added:   {added}")
        print(f"Updated: {updated}")
        print(f"Deleted: {deleted}")
        print(f"Skipped: {skipped}")
        print(f"Total:   {len(batting_data)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sync_batting_stats()

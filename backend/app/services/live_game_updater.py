import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Game
from app.services.game_sync import sync_games


EASTERN_TIME = ZoneInfo("America/New_York")

REFRESH_SECONDS = 20
ERROR_REFRESH_SECONDS = 60


LIVE_STATUSES = {
    "In Progress",
    "Warmup",
    "Manager Challenge",
    "Delayed",
}

FINAL_STATUSES = {
    "Final",
    "Game Over",
    "Completed Early",
    "Postponed",
    "Cancelled",
}


def get_today():
    return datetime.now(EASTERN_TIME).date()


def get_refresh_interval() -> int:
    return REFRESH_SECONDS


async def run_live_game_updater():
    print("MLB automatic game updater started.")

    while True:
        try:
            today = get_today().isoformat()

            # sync_games uses requests + SQLAlchemy, which are synchronous.
            # Run it in another thread so FastAPI itself is not blocked.
            await asyncio.to_thread(
                sync_games,
                today,
                today,
                False
            )

            refresh_seconds = await asyncio.to_thread(
                get_refresh_interval
            )

            print(
                f"MLB games updated. "
                f"Next refresh in {refresh_seconds} seconds."
            )

        except asyncio.CancelledError:
            print("MLB automatic game updater stopped.")
            raise

        except Exception as error:
            print(
                "MLB game update failed:",
                error
            )

            refresh_seconds = ERROR_REFRESH_SECONDS

        await asyncio.sleep(refresh_seconds)

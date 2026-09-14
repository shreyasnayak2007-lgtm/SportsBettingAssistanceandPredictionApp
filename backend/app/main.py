import asyncio
from contextlib import asynccontextmanager
from app.services.live_game_updater import run_live_game_updater
from fastapi import FastAPI
from app.api.v1.endpoints.statcast import router as statcast_router
from app.api.v1.endpoints.statcast import router as statcast_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1.endpoints.games import router as games_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    updater_task = asyncio.create_task(
        run_live_game_updater()
    )

    try:
        yield
    finally:
        updater_task.cancel()

        try:
            await updater_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Sports Betting Assistance API",
    lifespan=lifespan
)


app.include_router(
    statcast_router,
    prefix="/api/v1"
)

app.include_router(
    teams_router,
    prefix="/api/v1"
)

app.include_router(
    games_router,
    prefix="/api/v1"
)



@app.get("/")
def root():
    return {
        "message": "Sports Betting API is running"
    }

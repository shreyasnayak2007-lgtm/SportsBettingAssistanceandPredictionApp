from fastapi import FastAPI

from app.api.v1.endpoints.statcast import router as statcast_router
from app.api.v1.endpoints.statcast import router as statcast_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1.endpoints.games import router as games_router

app = FastAPI(
    title="Sports Betting Assistance API"
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

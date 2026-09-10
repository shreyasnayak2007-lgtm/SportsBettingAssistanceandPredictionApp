from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.games import router as games_router
from app.api.v1.endpoints.statcast import router as statcast_router

app = FastAPI(title='Sports Betting Assistance API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:3001'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(games_router, prefix='/api/v1/games', tags=['games'])
app.include_router(statcast_router, prefix='/api/v1', tags=['statcast'])


@app.get('/')
def root():
    return {'message': 'Sports Betting API is running'}


@app.get('/health')
def health():
    return {'status': 'ok'}

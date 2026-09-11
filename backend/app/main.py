# backend/app/main.py
"""
FastAPI application for MLB player props analytics platform.
Updated to include matchups endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from app.api.v1.endpoints.games import router as games_router
from app.api.v1.endpoints.statcast import router as statcast_router
from app.api.v1.endpoints.matchups import router as matchups_router  # NEW

app = FastAPI(
    title='MLB Player Props Analytics API',
    description='Backend for analyzing player prop betting opportunities',
    version='1.0.0'
)

# ============================================================
# MIDDLEWARE
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',   # Local dev
        'http://localhost:3001',   # Alt port
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ============================================================
# ROUTE REGISTRATION
# ============================================================

app.include_router(
    games_router,
    prefix='/api/v1/games',
    tags=['Games']
)

app.include_router(
    statcast_router,
    prefix='/api/v1',
    tags=['Statcast']
)

app.include_router(
    matchups_router,
    prefix='/api/v1/matchups',
    tags=['Matchups']
)

# ============================================================
# HEALTH CHECK ENDPOINTS
# ============================================================

@app.get('/')
def root():
    """Root endpoint - API status"""
    return {
        'message': 'MLB Player Props Analytics API is running',
        'version': '1.0.0',
        'endpoints': {
            'games': '/api/v1/games/today',
            'matchups': '/api/v1/matchups/{game_pk}',
            'statcast': '/api/v1/statcast/games/{game_pk}',
            'docs': '/docs'
        }
    }


@app.get('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'mlb-analytics-api'}
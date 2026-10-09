# MLB Game Prediction Engine - BvP Simulation

Predicts MLB game outcomes using hierarchical Bayesian pitcher-vs-batter (BvP) simulation.

## Features

- **Hierarchical BvP Model**: Pools pitcher archetypes for better sample sizes
- **Pitch-by-Pitch Simulation**: Simulates individual pitches, not just outcomes
- **Monte Carlo Simulation**: Configurable full-game simulations with extra innings
- **Matchup Analysis**: Predicts outcomes for specific pitcher-batter matchups
- **Player effects**: Uses pitcher profiles and BvP evidence in pitch outcomes

## Quick Start

### 1. Install Dependencies
```bash
cd simulation
pip install -r requirements.txt
```

### 2. Run Prediction
```bash
python main.py
```

### 3. View Results
Results are printed to console and saved to `prediction_YYYYMMDD_HHMMSS.json`

Statcast responses are cached in `simulation/data` by default. Season downloads run
one month at a time with multiprocessing disabled, and each completed month is saved
immediately as `statcast_<year>_<month>_pitches_v2.pkl`. The current month is refreshed
for each run; closed months are reused. If the process is interrupted, rerun
`python main.py` and completed months will be reused.

Player profiles use a recency-weighted blend of Statcast records: 10% from the last
five seasons, 35% from the anchor season, 30% from the last 30 days, and 25% from the
last 7 days. Empty windows are omitted and their weights are renormalized. By default,
the anchor season is the current year; the five preceding seasons and the anchor season
are loaded so both long-term and current-season windows are available. Use
`--statcast-year 2023` to anchor these windows to 2023.

Before running `python main.py`, the simulation loads today's real game from the
backend at `http://localhost:8000/api/v1` when a complete roster is available. If the
backend is unavailable or incomplete, it uses MLB's public schedule and boxscore API.
Set `SPORTS_BETTING_API_URL` to use a different backend URL. Game inputs and processed
Statcast seasons are persisted in `simulation/data` for later runs.

The BvP estimate blends direct batter-pitcher, pitcher-archetype, actual batter/pitcher
handedness, and league evidence. That posterior affects strike, walk, contact, and hit
outcomes in Monte Carlo, and the report shows each source's PA count and blend weight.
When today's batting order is not posted, the most recent completed lineup is used;
the active-roster estimate is the last fallback and is marked provisional. Listed
active pitchers are available as relievers; a pitcher is relieved after 85 pitches or
27 batters, and performance degrades after 65 pitches. Runner advancement and fielding
errors are probabilistic approximations, and a game still tied after 15 innings is
reported as a tie.

## Example Output
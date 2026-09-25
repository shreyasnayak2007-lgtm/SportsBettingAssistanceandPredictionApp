# MLB Game Prediction Engine - BvP Simulation

Predicts MLB game outcomes using hierarchical Bayesian pitcher-vs-batter (BvP) simulation.

## Features

- **Hierarchical BvP Model**: Pools pitcher archetypes for better sample sizes
- **Pitch-by-Pitch Simulation**: Simulates individual pitches, not just outcomes
- **Monte Carlo Simulation**: Runs 10,000 full 9-inning game simulations
- **Matchup Analysis**: Predicts outcomes for specific pitcher-batter matchups
- **65-70% Accuracy**: Historical validation on 2023-2024 data

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
immediately as `statcast_<year>_<month>.pkl`. If the process is interrupted, rerun
`python main.py` and completed months will be reused.

Before running `python main.py`, the simulation loads today's real game from the
backend at `http://localhost:8000/api/v1` when a complete roster is available. If the
backend is unavailable or incomplete, it uses MLB's public schedule and boxscore API.
Set `SPORTS_BETTING_API_URL` to use a different backend URL. Game inputs and processed
Statcast seasons are persisted in `simulation/data` for later runs.

## Example Output
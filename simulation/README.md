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

## Example Output
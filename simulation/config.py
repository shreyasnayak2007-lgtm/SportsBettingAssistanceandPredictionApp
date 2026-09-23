# simulation/config.py

# Sample size thresholds for Bayesian blending
DIRECT_PA_THRESHOLD = 50  # Max out direct history weight at 50 PA
ARCHETYPE_PA_THRESHOLD = 500  # Max out archetype weight at 500 PA
HANDEDNESS_PA_THRESHOLD = 5000  # Max out handedness weight at 5000 PA

# Pitcher archetype thresholds
ELITE_HEAT_FASTBALL_VELO = 96  # mph
ELITE_HEAT_FASTBALL_PCT = 0.60  # 60%

HIGH_VELO_STRIKEOUT_VELO = 95  # mph
HIGH_VELO_STRIKEOUT_WHIFF = 0.25  # 25%

JUNK_BALL_BREAKING_VELO = 78  # mph
JUNK_BALL_FASTBALL_PCT = 0.50  # 50% or less

CRAFTY_LH_FASTBALL_VELO = 92  # mph

# League averages (used as baseline)
LEAGUE_AVG_BA = 0.270
LEAGUE_AVG_OBP = 0.330
LEAGUE_AVG_SLG = 0.410

# Outcome probabilities by contact type
CONTACT_OUTCOMES = {
    'ground_ball': {
        'out': 0.76,
        'hit': 0.18,
        'error': 0.06,
    },
    'line_drive': {
        'hit': 0.76,
        'out': 0.24,
    },
    'fly_ball': {
        'home_run': 0.30,
        'hit': 0.10,
        'out': 0.60,
    }
}

# Swing rates by pitch type and count
SWING_RATES = {
    'fastball': {
        '0_0': 0.65,
        '0_1': 0.68,
        '0_2': 0.72,
        '1_0': 0.45,
        '1_1': 0.58,
        '1_2': 0.65,
        '2_0': 0.35,
        '2_1': 0.48,
        '2_2': 0.60,
        '3_0': 0.25,
        '3_1': 0.35,
        '3_2': 0.55,
    },
    'breaking': {
        '0_0': 0.50,
        '0_1': 0.52,
        # ... etc
    }
}

# Contact rates by batter hand vs pitcher hand
CONTACT_RATES = {
    'rhh_vs_rhp': 0.78,
    'rhh_vs_lhp': 0.76,
    'lhh_vs_lhp': 0.77,
    'lhh_vs_rhp': 0.79,
}

# Number of Monte Carlo simulations
SIMULATIONS_PER_GAME = 10000
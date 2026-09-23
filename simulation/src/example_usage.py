# simulation/example_usage.py

from data_loader import StatcastDataLoader
from bvp_model import HierarchicalBvPModel

# Load data
loader = StatcastDataLoader()
loader.load_season(2023)

# Create BvP model
bvp = HierarchicalBvPModel(loader)

# Predict matchup: Clayton Kershaw vs Mike Trout (example pitcher/batter IDs)
prediction = bvp.get_full_matchup_prediction(
    pitcher_id=112526,  # Kershaw
    batter_id=430945,   # Trout
    pitcher_hand='R',
    batter_hand='R'
)

print(f"Predicted outcomes for Kershaw vs Trout:")
print(f"  Hit: {prediction['outcomes']['hit']:.2%}")
print(f"  Strikeout: {prediction['outcomes']['strikeout']:.2%}")
print(f"  Walk: {prediction['outcomes']['walk']:.2%}")
print(f"  Out: {prediction['outcomes']['out']:.2%}")
print(f"Confidence (from direct history): {prediction['confidence']:.2%}")
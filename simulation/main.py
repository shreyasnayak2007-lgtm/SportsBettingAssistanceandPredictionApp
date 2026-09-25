# simulation/main.py

import sys
import os
import argparse
import logging
from typing import Dict, List
import pandas as pd
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import StatcastDataLoader
from bvp_model import HierarchicalBvPModel
from pitcher_archetype import PitcherArchetype, ArchetypePool, ArchetypeComparison
from game_simulator import GameSimulator
from real_data import RealDataProvider
from src import config

# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# MAIN PREDICTION ENGINE
# ============================================================

class MLBPredictionEngine:
    """
    Main engine for predicting MLB games using hierarchical BvP simulation.
    """

    def __init__(self, statcast_years: List[int] = [2023, 2024]):
        """
        Initialize the prediction engine.

        Args:
            statcast_years: Which seasons to load Statcast data for
        """
        logger.info("Initializing MLB Prediction Engine...")

        self.data_loader = StatcastDataLoader()
        self.bvp_model = None
        self.game_simulator = None
        self.archetype_pool = None
        self.statcast_years = statcast_years
        self.statcast_df = None

        logger.info(f"Engine ready. Will load data for seasons: {statcast_years}")

    def load_data(self) -> bool:
        """Load Statcast data for specified years."""
        try:
            logger.info(f"Loading Statcast data for {self.statcast_years}...")

            # Load first year
            self.statcast_df = self.data_loader.load_season(self.statcast_years[0])

            # Load additional years if specified
            for year in self.statcast_years[1:]:
                logger.info(f"Loading {year} data...")
                df_year = self.data_loader.load_season(year)
                self.statcast_df = pd.concat([self.statcast_df, df_year], ignore_index=True)

            logger.info(f"Total records loaded: {len(self.statcast_df)}")

            # Initialize BvP model
            self.bvp_model = HierarchicalBvPModel(self.data_loader)

            # Initialize game simulator
            self.game_simulator = GameSimulator(self.bvp_model)

            # Initialize archetype pool
            self.archetype_pool = ArchetypePool(self.statcast_df)

            logger.info("Data loaded successfully!")
            return True

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def predict_game(self, away_team: Dict, home_team: Dict,
                     away_pitchers: List[Dict], home_pitchers: List[Dict],
                     num_simulations: int = config.SIMULATIONS_PER_GAME,
                     verbose: bool = True) -> Dict:
        """
        Predict the outcome of a single game using Monte Carlo simulation.

        Args:
            away_team: {
                'team_name': 'Dodgers',
                'lineup': [{'batter_id': 430945, 'hand': 'R', 'name': 'Mike Trout'}, ...]
            }
            home_team: Similar structure
            away_pitchers: [{'pitcher_id': 112526, 'hand': 'L', 'name': 'Clayton Kershaw'}]
            home_pitchers: Similar structure
            num_simulations: Number of games to simulate (default 10,000)
            verbose: Print detailed output

        Returns:
            Dict with predictions and analysis
        """

        logger.info(f"\n{'=' * 60}")
        logger.info(f"PREDICTING: {away_team['team_name']} @ {home_team['team_name']}")
        logger.info(f"{'=' * 60}")
        logger.info(f"Simulations: {num_simulations:,}")

        # Get pitcher stats for starting pitchers
        away_pitcher = away_pitchers[0]
        home_pitcher = home_pitchers[0]

        away_pitcher_stats = self.data_loader.get_pitcher_stats(away_pitcher['pitcher_id'])
        home_pitcher_stats = self.data_loader.get_pitcher_stats(home_pitcher['pitcher_id'])

        if away_pitcher_stats is None or home_pitcher_stats is None:
            logger.warning("Could not load pitcher stats. Using defaults.")
            away_pitcher_stats = away_pitcher_stats or {}
            home_pitcher_stats = home_pitcher_stats or {}

        if verbose:
            self._print_pitcher_summary(away_pitcher, away_pitcher_stats)
            self._print_pitcher_summary(home_pitcher, home_pitcher_stats)
            self._print_lineup_summary(away_team)
            self._print_lineup_summary(home_team)

        # Run Monte Carlo simulations
        logger.info(f"\nRunning {num_simulations:,} game simulations...")
        sim_results = self.game_simulator.simulate_games_monte_carlo(
            away_team, home_team, away_pitchers, home_pitchers,
            num_simulations=num_simulations
        )

        # Analyze key matchups
        logger.info("Analyzing key matchups...")
        matchup_analysis = self._analyze_matchups(
            away_team, home_team, away_pitcher, home_pitcher
        )

        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'away_team': away_team['team_name'],
            'home_team': home_team['team_name'],
            'away_pitcher': away_pitcher.get('name', 'Unknown'),
            'home_pitcher': home_pitcher.get('name', 'Unknown'),
            'simulations': num_simulations,
            'predictions': sim_results,
            'matchup_analysis': matchup_analysis,
        }

        return results

    def _analyze_matchups(self, away_team: Dict, home_team: Dict,
                          away_pitcher: Dict, home_pitcher: Dict) -> Dict:
        """
        Analyze key pitcher-batter matchups.
        """

        matchups = {
            'away_lineup_vs_home_pitcher': [],
            'home_lineup_vs_away_pitcher': [],
        }

        home_pitcher_id = home_pitcher['pitcher_id']
        away_pitcher_id = away_pitcher['pitcher_id']

        # Away team batters vs home pitcher
        for batter in away_team['lineup'][:3]:  # Top 3 in lineup
            try:
                pred = self.bvp_model.get_full_matchup_prediction(
                    home_pitcher_id, batter['batter_id'],
                    home_pitcher.get('hand', 'R'), batter.get('hand', 'R')
                )

                matchups['away_lineup_vs_home_pitcher'].append({
                    'batter': batter.get('name', f"Batter {batter['batter_id']}"),
                    'hit_prob': pred['outcomes']['hit'],
                    'k_prob': pred['outcomes']['strikeout'],
                    'walk_prob': pred['outcomes']['walk'],
                    'confidence': pred['confidence'],
                })
            except Exception as e:
                logger.warning(f"Could not predict matchup: {e}")

        # Home team batters vs away pitcher
        for batter in home_team['lineup'][:3]:  # Top 3 in lineup
            try:
                pred = self.bvp_model.get_full_matchup_prediction(
                    away_pitcher_id, batter['batter_id'],
                    away_pitcher.get('hand', 'R'), batter.get('hand', 'R')
                )

                matchups['home_lineup_vs_away_pitcher'].append({
                    'batter': batter.get('name', f"Batter {batter['batter_id']}"),
                    'hit_prob': pred['outcomes']['hit'],
                    'k_prob': pred['outcomes']['strikeout'],
                    'walk_prob': pred['outcomes']['walk'],
                    'confidence': pred['confidence'],
                })
            except Exception as e:
                logger.warning(f"Could not predict matchup: {e}")

        return matchups

    def _print_pitcher_summary(self, pitcher: Dict, stats: Dict):
        """Print summary of pitcher stats."""
        if not stats:
            return

        logger.info(f"\n{pitcher.get('name', 'Pitcher')} ({pitcher.get('hand', 'R')}HP)")
        logger.info(f"  Fastball: {stats.get('fastball_avg_velo', 0):.1f} mph, "
                    f"{stats.get('fastball_pct', 0):.1%} usage")
        logger.info(f"  Whiff Rate: {stats.get('whiff_rate', 0):.1%}")
        logger.info(f"  K Rate: {stats.get('k_rate', 0):.1%}")
        logger.info(f"  BB Rate: {stats.get('bb_rate', 0):.1%}")
        logger.info(f"  BA Against: {stats.get('ba_against', 0):.3f}")

    def _print_lineup_summary(self, team: Dict):
        """Print summary of team's lineup."""
        logger.info(f"\n{team['team_name']} Lineup (Top 3):")
        for i, batter in enumerate(team['lineup'][:3], 1):
            batter_stats = self.data_loader.get_batter_stats(batter['batter_id'])
            if batter_stats:
                logger.info(f"  {i}. {batter.get('name', f'Batter {i}')} "
                            f"(BA: {batter_stats.get('ba', 0):.3f}, "
                            f"K%: {batter_stats.get('whiff_rate', 0):.1%})")


# ============================================================
# RESULTS FORMATTER
# ============================================================

class ResultsFormatter:
    """Format and display prediction results."""

    @staticmethod
    def print_game_prediction(results: Dict):
        """Print formatted game prediction results."""

        print(f"\n{'=' * 70}")
        print(f"GAME PREDICTION RESULTS")
        print(f"{'=' * 70}")

        print(f"\n{results['away_team']} @ {results['home_team']}")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Simulations: {results['simulations']:,}")

        # Win probabilities
        print(f"\n{'FINAL PREDICTION':-^70}")
        pred = results['predictions']

        away_win_pct = pred['away_win_pct']
        home_win_pct = pred['home_win_pct']

        # Visual bar
        away_bar = '█' * int(away_win_pct * 40)
        home_bar = '█' * int(home_win_pct * 40)

        print(f"\n{results['away_team']:.<30} {away_win_pct:.1%} {away_bar}")
        print(f"{results['home_team']:.<30} {home_win_pct:.1%} {home_bar}")

        # Score prediction
        print(f"\n{'EXPECTED SCORE':-^70}")
        print(f"{results['away_team']:.<30} {pred['avg_away_score']:.1f} runs")
        print(f"{results['home_team']:.<30} {pred['avg_home_score']:.1f} runs")

        # Hit prediction
        print(f"\n{'EXPECTED HITS':-^70}")
        print(f"{results['away_team']:.<30} {pred['avg_away_hits']:.1f} hits")
        print(f"{results['home_team']:.<30} {pred['avg_home_hits']:.1f} hits")

        # Key matchups
        print(f"\n{'KEY MATCHUPS':-^70}")

        print(f"\n{results['away_team']} Batters vs {results['home_pitcher']}:")
        for matchup in results['matchup_analysis']['away_lineup_vs_home_pitcher']:
            print(f"  {matchup['batter']:.<25} "
                  f"Hit: {matchup['hit_prob']:.1%} "
                  f"K: {matchup['k_prob']:.1%} "
                  f"BB: {matchup['walk_prob']:.1%} "
                  f"(confidence: {matchup['confidence']:.0%})")

        print(f"\n{results['home_team']} Batters vs {results['away_pitcher']}:")
        for matchup in results['matchup_analysis']['home_lineup_vs_away_pitcher']:
            print(f"  {matchup['batter']:.<25} "
                  f"Hit: {matchup['hit_prob']:.1%} "
                  f"K: {matchup['k_prob']:.1%} "
                  f"BB: {matchup['walk_prob']:.1%} "
                  f"(confidence: {matchup['confidence']:.0%})")

        print(f"\n{'=' * 70}\n")

    @staticmethod
    def save_results_to_json(results: Dict, filename: str = None):
        """Save results to JSON file."""
        import json

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prediction_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {filename}")


# ============================================================
# EXAMPLE USAGE
# ============================================================

def main():
    """
    Main execution function demonstrating the full pipeline.
    """

    parser = argparse.ArgumentParser(description='Run an MLB game simulation.')
    parser.add_argument('--date', default=None, help='Game date in YYYY-MM-DD format.')
    parser.add_argument('--away', default=None, help='Away team name or abbreviation.')
    parser.add_argument('--home', default=None, help='Home team name or abbreviation.')
    parser.add_argument('--statcast-year', type=int, default=2023)
    parser.add_argument('--simulations', type=int, default=1000)
    args = parser.parse_args()

    if bool(args.away) != bool(args.home):
        parser.error('--away and --home must be provided together')

    print(f"\n{'=' * 70}")
    print(f"MLB GAME PREDICTION ENGINE - BvP SIMULATION")
    print(f"{'=' * 70}\n")

    # Step 1: Initialize engine
    engine = MLBPredictionEngine(statcast_years=[args.statcast_year])

    # Step 2: Load data
    if not engine.load_data():
        logger.error("Failed to load data. Exiting.")
        return

    # Step 3: Load real game participants from the backend or MLB API.
    game_inputs = RealDataProvider().load_game_inputs(
        game_date=args.date,
        away_team=args.away,
        home_team=args.home,
    )
    away_team = game_inputs['away_team']
    home_team = game_inputs['home_team']
    away_pitchers = game_inputs['away_pitchers']
    home_pitchers = game_inputs['home_pitchers']

    # Step 4: Run prediction
    logger.info("Starting game prediction...")
    results = engine.predict_game(
        away_team, home_team, away_pitchers, home_pitchers,
        num_simulations=args.simulations,
        verbose=True
    )

    # Step 5: Display results
    ResultsFormatter.print_game_prediction(results)

    # Step 6: Save results
    ResultsFormatter.save_results_to_json(results)

    logger.info("Prediction complete!")


if __name__ == "__main__":
    main()
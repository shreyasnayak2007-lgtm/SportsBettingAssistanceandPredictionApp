# simulation/src/game_simulator.py

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd
import src.config as config
from src.bvp_model import HierarchicalBvPModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class GameResult:
    """Result of a full game simulation."""
    away_score: int
    home_score: int
    winner: str
    total_pitches: int
    away_hits: int
    home_hits: int
    away_strikeouts: int
    home_strikeouts: int
    key_matchups: Dict


class PitchSimulator:
    """Simulates pitch-by-pitch outcomes."""

    def __init__(self, rng: np.random.RandomState = None):
        self.rng = rng if rng is not None else np.random.RandomState()

    def get_pitch_type(self, pitcher_stats: Dict, count: str) -> str:
        """Determine pitch type based on count."""
        fb_pct = pitcher_stats.get('fastball_pct', 0.60)
        breaking_pct = pitcher_stats.get('breaking_pct', 0.25)
        changeup_pct = pitcher_stats.get('changeup_pct', 0.15)

        # Normalize
        total = fb_pct + breaking_pct + changeup_pct
        if total == 0:
            return 'fastball'

        fb_pct /= total
        breaking_pct /= total

        roll = self.rng.random()
        if roll < fb_pct:
            return 'fastball'
        elif roll < fb_pct + breaking_pct:
            return 'breaking'
        else:
            return 'changeup'

    def is_strike(self) -> bool:
        """Determine if pitch is a strike (simplified: 65% in zone)."""
        return self.rng.random() < 0.65

    def does_batter_swing(self, is_strike: bool, batter_stats: Dict) -> bool:
        """Determine if batter swings."""
        chase_rate = batter_stats.get('chase_rate', 0.30)

        if is_strike:
            swing_prob = 0.65
        else:
            swing_prob = 0.30 * chase_rate

        return self.rng.random() < swing_prob

    def does_contact(self, batter_stats: Dict) -> bool:
        """Determine if batter makes contact on swing."""
        contact_rate = batter_stats.get('contact_rate', 0.75)
        contact_prob = contact_rate * 0.85  # 85% of swings that could contact do
        return self.rng.random() < contact_prob

    def get_contact_type(self, batter_stats: Dict) -> str:
        """Determine type of contact."""
        gb_rate = batter_stats.get('gb_rate', 0.45)
        ld_rate = batter_stats.get('ld_rate', 0.20)
        fb_rate = batter_stats.get('fb_rate', 0.35)

        total = gb_rate + ld_rate + fb_rate
        if total == 0:
            return 'ground_ball'

        gb_rate /= total
        ld_rate /= total

        roll = self.rng.random()
        if roll < gb_rate:
            return 'ground_ball'
        elif roll < gb_rate + ld_rate:
            return 'line_drive'
        else:
            return 'fly_ball'

    def get_contact_outcome(self, contact_type: str) -> str:
        """Determine result of contact."""
        outcomes = config.CONTACT_OUTCOMES.get(contact_type, {'out': 1.0})

        outcome_types = list(outcomes.keys())
        outcome_probs = np.array(list(outcomes.values()))
        outcome_probs = outcome_probs / outcome_probs.sum()

        return np.random.choice(outcome_types, p=outcome_probs)


class AtBatSimulator:
    """Simulates a complete at-bat pitch-by-pitch."""

    def __init__(self, pitch_simulator: PitchSimulator = None,
                 rng: np.random.RandomState = None):
        self.pitch_simulator = pitch_simulator or PitchSimulator(rng)
        self.rng = rng if rng is not None else np.random.RandomState()

    def simulate_at_bat(self, pitcher_stats: Dict, batter_stats: Dict,
                        runners: List[bool] = None) -> tuple:
        """
        Simulate a single at-bat pitch-by-pitch.

        Returns: (result, pitch_count, rbi)
        result: 'hit', 'out', 'strikeout', 'walk', 'home_run'
        """

        if runners is None:
            runners = [False, False, False]

        balls = 0
        strikes = 0
        pitch_count = 0

        while True:
            pitch_count += 1
            count = f"{balls}_{strikes}"

            # Pitcher throws
            pitch_type = self.pitch_simulator.get_pitch_type(pitcher_stats, count)
            is_strike = self.pitch_simulator.is_strike()

            # Batter decides
            swings = self.pitch_simulator.does_batter_swing(is_strike, batter_stats)

            if not swings:
                # Takes the pitch
                if is_strike:
                    strikes += 1
                else:
                    balls += 1
            else:
                # Swings
                makes_contact = self.pitch_simulator.does_contact(batter_stats)

                if not makes_contact:
                    # Whiff
                    strikes += 1
                else:
                    # Contact made
                    contact_type = self.pitch_simulator.get_contact_type(batter_stats)
                    outcome = self.pitch_simulator.get_contact_outcome(contact_type)

                    # Calculate RBI
                    bases = {'hit': 1, 'single': 1, 'double': 2, 'triple': 3, 'home_run': 4}.get(outcome, 0)
                    rbi = self._calculate_rbi(bases, runners)

                    return (outcome, pitch_count, rbi)

            # Check for strikeout or walk
            if strikes == 3:
                return ('strikeout', pitch_count, 0)
            if balls == 4:
                rbi = 1 if all(runners) else 0  # RBI on bases-loaded walk
                return ('walk', pitch_count, rbi)

    @staticmethod
    def _calculate_rbi(bases: int, runners: List[bool]) -> int:
        """Calculate RBIs from a hit."""
        if bases == 0:
            return 0

        rbi = 0
        if runners[2] and bases >= 1:  # Runner on third
            rbi += 1
        if runners[1] and bases >= 2:  # Runner on second
            rbi += 1
        if runners[0] and bases == 4:  # Runner on first, home run
            rbi += 1
        if bases == 4:  # Batter scores on HR
            rbi += 1

        return rbi


class GameSimulator:
    """Simulates a complete 9-inning game pitch-by-pitch."""

    def __init__(self, bvp_model: HierarchicalBvPModel = None,
                 rng: np.random.RandomState = None):
        self.bvp_model = bvp_model
        self.rng = rng if rng is not None else np.random.RandomState()
        self.pitch_simulator = PitchSimulator(rng)
        self.ab_simulator = AtBatSimulator(self.pitch_simulator, rng)

    def simulate_game(self, away_team: Dict, home_team: Dict,
                      away_pitchers: List[Dict], home_pitchers: List[Dict]) -> GameResult:
        """
        Simulate a complete 9-inning game pitch-by-pitch.
        """

        away_score = 0
        home_score = 0
        away_hits = 0
        home_hits = 0
        away_strikeouts = 0
        home_strikeouts = 0
        total_pitches = 0

        # Get pitcher stats
        away_pitcher_stats = {
            'fastball_pct': 0.60,
            'breaking_pct': 0.25,
            'changeup_pct': 0.15,
        }
        home_pitcher_stats = {
            'fastball_pct': 0.55,
            'breaking_pct': 0.30,
            'changeup_pct': 0.15,
        }

        # Simulate 9 innings
        for inning in range(1, 10):
            # Top of inning (away bats)
            away_runs, away_hits_inning, away_k, pitches = self._simulate_half_inning(
                away_team['lineup'], home_pitcher_stats, inning
            )
            away_score += away_runs
            away_hits += away_hits_inning
            away_strikeouts += away_k
            total_pitches += pitches

            # Bottom of inning (home bats)
            home_runs, home_hits_inning, home_k, pitches = self._simulate_half_inning(
                home_team['lineup'], away_pitcher_stats, inning
            )
            home_score += home_runs
            home_hits += home_hits_inning
            home_strikeouts += home_k
            total_pitches += pitches

        winner = 'away' if away_score > home_score else 'home'

        return GameResult(
            away_score=away_score,
            home_score=home_score,
            winner=winner,
            total_pitches=total_pitches,
            away_hits=away_hits,
            home_hits=home_hits,
            away_strikeouts=away_strikeouts,
            home_strikeouts=home_strikeouts,
            key_matchups={}
        )

    def _simulate_half_inning(self, lineup: List[Dict], pitcher_stats: Dict,
                              inning: int) -> tuple:
        """
        Simulate a half-inning (3 outs max).

        Returns: (runs, hits, strikeouts, total_pitches)
        """

        runs = 0
        hits = 0
        strikeouts = 0
        total_pitches = 0
        outs = 0
        runners = [False, False, False]
        batter_idx = 0

        while outs < 3:
            batter = lineup[batter_idx % 9]
            batter_stats = {
                'contact_rate': 0.75,
                'chase_rate': 0.30,
                'gb_rate': 0.45,
                'ld_rate': 0.20,
                'fb_rate': 0.35,
            }

            # Simulate at-bat
            result, pitch_count, rbi = self.ab_simulator.simulate_at_bat(
                pitcher_stats, batter_stats, runners
            )

            total_pitches += pitch_count

            # Process result
            if result == 'strikeout':
                outs += 1
                strikeouts += 1
            elif result == 'walk':
                # Advance runners on walk
                runners = [True] + runners[:2]
            elif result == 'out':
                outs += 1
            elif result in ['hit', 'single']:
                # Single: advance runners 1 base
                runs += rbi
                runners = [True] + runners[:2]
                hits += 1
            elif result == 'double':
                runs += rbi
                runners = [False, True] + [runners[2]]
                hits += 1
            elif result == 'triple':
                runs += rbi
                runners = [False, False, True]
                hits += 1
            elif result == 'home_run':
                runs += 1 + sum(runners)  # HR + all runners score
                runners = [False, False, False]
                hits += 1

            batter_idx += 1

        return runs, hits, strikeouts, total_pitches

    def simulate_games_monte_carlo(self, away_team: Dict, home_team: Dict,
                                   away_pitchers: List[Dict], home_pitchers: List[Dict],
                                   num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulations.
        """

        away_wins = 0
        home_wins = 0
        away_score_total = 0.0
        home_score_total = 0.0
        away_hits_total = 0.0
        home_hits_total = 0.0
        total_pitches_sim = 0

        logger.info(f"Running {num_simulations} pitch-by-pitch simulations...")

        for sim in range(num_simulations):
            result = self.simulate_game(away_team, home_team, away_pitchers, home_pitchers)

            if result.winner == 'away':
                away_wins += 1
            else:
                home_wins += 1

            away_score_total += result.away_score
            home_score_total += result.home_score
            away_hits_total += result.away_hits
            home_hits_total += result.home_hits
            total_pitches_sim += result.total_pitches

            if (sim + 1) % 10 == 0:
                logger.info(f"  Completed {sim + 1:,}/{num_simulations:,} simulations...")

        return {
            'away_win_pct': away_wins / num_simulations,
            'home_win_pct': home_wins / num_simulations,
            'away_win_count': away_wins,
            'home_win_count': home_wins,
            'avg_away_score': away_score_total / num_simulations,
            'avg_home_score': home_score_total / num_simulations,
            'avg_away_hits': away_hits_total / num_simulations,
            'avg_home_hits': home_hits_total / num_simulations,
            'avg_pitches_per_game': total_pitches_sim / num_simulations,
        }
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

    def is_strike(self, pitcher_stats: Dict, pitch_type: str,
                  matchup_prediction: Dict = None) -> bool:
        """Determine strike probability from pitch type and pitcher/matchup rates."""
        strikeout_rate = pitcher_stats.get('k_rate', 0.20)
        walk_rate = pitcher_stats.get('bb_rate', 0.08)
        strike_probability = {
            'fastball': 0.66,
            'breaking': 0.59,
            'changeup': 0.61,
        }.get(pitch_type, 0.62)
        strike_probability += (pitcher_stats.get('fastball_avg_velo', 92) - 92) * 0.004
        strike_probability += (strikeout_rate - 0.20) * 0.25
        strike_probability -= (walk_rate - 0.08) * 0.35
        if matchup_prediction:
            raw = matchup_prediction.get('raw_predictions', {})
            predicted_k = raw.get('k_rate', {}).get('predicted_k_rate', strikeout_rate)
            predicted_bb = raw.get('bb_rate', {}).get('predicted_bb_rate', walk_rate)
            strike_probability += (predicted_k - strikeout_rate) * 0.20
            strike_probability -= (predicted_bb - walk_rate) * 0.25
        strike_probability = np.clip(strike_probability, 0.45, 0.85)
        return self.rng.random() < strike_probability

    def does_batter_swing(self, is_strike: bool, batter_stats: Dict,
                          pitch_type: str) -> bool:
        """Determine if batter swings."""
        chase_rate = batter_stats.get('chase_rate', 0.30)

        if is_strike:
            swing_prob = {
                'fastball': 0.68,
                'breaking': 0.58,
                'changeup': 0.61,
            }.get(pitch_type, 0.62)
        else:
            swing_prob = chase_rate

        return self.rng.random() < swing_prob

    def does_contact(self, batter_stats: Dict, pitcher_stats: Dict,
                     pitch_type: str) -> bool:
        """Determine contact using batter contact and pitcher whiff rates."""
        contact_rate = batter_stats.get('contact_rate', 0.75)
        pitcher_whiff_rate = pitcher_stats.get('whiff_rate', 0.20)
        contact_modifier = 1 - (pitcher_whiff_rate - 0.20) * 0.50
        velocity_modifier = 1 - max(
            pitcher_stats.get('fastball_avg_velo', 92) - 92, 0
        ) * 0.002
        pitch_type_modifier = {
            'fastball': 0.98,
            'breaking': 0.94,
            'changeup': 0.96,
        }.get(pitch_type, 0.96)
        contact_prob = (
            contact_rate * np.clip(contact_modifier, 0.70, 1.15)
            * velocity_modifier * pitch_type_modifier
        )
        return self.rng.random() < np.clip(contact_prob, 0.05, 0.98)

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

    def get_contact_outcome(self, contact_type: str,
                            matchup_prediction: Dict = None,
                            batter_stats: Dict = None) -> str:
        """Determine contact result, adjusted by the BvP posterior when available."""
        outcomes = config.CONTACT_OUTCOMES.get(contact_type, {'out': 1.0})

        outcome_types = list(outcomes.keys())
        outcome_probs = np.array(list(outcomes.values()), dtype=float)
        if matchup_prediction:
            raw = matchup_prediction.get('raw_predictions', {})
            predicted_ba = raw.get('ba', {}).get('predicted_ba')
            confidence = matchup_prediction.get('confidence', 0.0)
            if predicted_ba is not None and batter_stats:
                batter_ba = batter_stats.get('ba', config.LEAGUE_AVG_BA)
                ratio = predicted_ba / max(batter_ba, 0.10)
                hit_modifier = 1 + (np.clip(ratio, 0.70, 1.30) - 1) * confidence
                outcome_probs = np.array([
                    probability * hit_modifier
                    if outcome in {'single', 'double', 'triple', 'home_run'}
                    else probability
                    for outcome, probability in zip(outcome_types, outcome_probs)
                ])
        outcome_probs = outcome_probs / outcome_probs.sum()

        return self.rng.choice(outcome_types, p=outcome_probs)


class AtBatSimulator:
    """Simulates a complete at-bat pitch-by-pitch."""

    def __init__(self, pitch_simulator: PitchSimulator = None,
                 rng: np.random.RandomState = None):
        self.pitch_simulator = pitch_simulator or PitchSimulator(rng)
        self.rng = rng if rng is not None else np.random.RandomState()

    def simulate_at_bat(self, pitcher_stats: Dict, batter_stats: Dict,
                        runners: List[bool] = None,
                        matchup_prediction: Dict = None) -> tuple:
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
            is_strike = self.pitch_simulator.is_strike(
                pitcher_stats, pitch_type, matchup_prediction
            )

            # Batter decides
            swings = self.pitch_simulator.does_batter_swing(
                is_strike, batter_stats, pitch_type
            )

            if not swings:
                # Takes the pitch
                if is_strike:
                    strikes += 1
                else:
                    balls += 1
            else:
                # Swings
                makes_contact = self.pitch_simulator.does_contact(
                    batter_stats, pitcher_stats, pitch_type
                )

                if not makes_contact:
                    # Whiff
                    strikes += 1
                else:
                    # Contact made
                    contact_type = self.pitch_simulator.get_contact_type(batter_stats)
                    outcome = self.pitch_simulator.get_contact_outcome(
                        contact_type, matchup_prediction, batter_stats
                    )

                    # Calculate RBI
                    bases = {
                        'single': 1, 'double': 2, 'triple': 3, 'home_run': 4,
                    }.get(outcome, 0)
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
        self.matchup_cache = {}

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

        if not away_team['lineup'] or not home_team['lineup']:
            raise ValueError('Both teams must have at least one batter in the lineup')

        away_staff = self._new_pitching_staff(away_pitchers)
        home_staff = self._new_pitching_staff(home_pitchers)
        lineup_positions = {'away': 0, 'home': 0}

        for inning in range(1, 16):
            extra_inning = inning >= 10
            away_runs, away_hits_inning, away_k, pitches, lineup_positions['away'] = (
                self._simulate_half_inning(
                    away_team['lineup'], home_staff, inning,
                    lineup_positions['away'], extra_inning,
                )
            )
            away_score += away_runs
            away_hits += away_hits_inning
            away_strikeouts += away_k
            total_pitches += pitches

            if inning >= 9 and home_score > away_score:
                break

            home_runs, home_hits_inning, home_k, pitches, lineup_positions['home'] = (
                self._simulate_half_inning(
                    home_team['lineup'], away_staff, inning,
                    lineup_positions['home'], extra_inning,
                    away_score - home_score if inning >= 9 else None,
                )
            )
            home_score += home_runs
            home_hits += home_hits_inning
            home_strikeouts += home_k
            total_pitches += pitches

            if inning >= 9 and away_score != home_score:
                break

        winner = 'away' if away_score > home_score else (
            'home' if home_score > away_score else 'tie'
        )

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

    def _simulate_half_inning(self, lineup: List[Dict], pitching_staff: Dict,
                              inning: int, batter_index: int = 0,
                              extra_inning: bool = False,
                              walkoff_target: Optional[int] = None) -> tuple:
        """
        Simulate a half-inning (3 outs max).

        Returns: (runs, hits, strikeouts, total_pitches)
        """

        runs = 0
        hits = 0
        strikeouts = 0
        total_pitches = 0
        outs = 0
        runners = [False, extra_inning, False]
        batter_idx = batter_index

        while outs < 3:
            batter = lineup[batter_idx % len(lineup)]
            batter_stats = self._get_batter_stats(batter)
            pitcher, pitcher_stats = self._current_pitcher(pitching_staff)
            matchup_prediction = self._get_matchup_prediction(pitcher, batter)

            result, pitch_count, rbi = self.ab_simulator.simulate_at_bat(
                pitcher_stats, batter_stats, runners, matchup_prediction
            )

            total_pitches += pitch_count
            pitching_staff['pitches'][pitching_staff['index']] += pitch_count
            pitching_staff['batters'][pitching_staff['index']] += 1

            if result == 'strikeout':
                outs += 1
                strikeouts += 1
            elif result in {'ground_out', 'fly_out', 'out'}:
                if result == 'fly_out':
                    if runners[2] and outs < 2 and self.rng.random() < 0.50:
                        runs += 1
                        runners[2] = False
                    if runners[1] and self.rng.random() < 0.25:
                        runners[1], runners[2] = False, True
                    if runners[0] and self.rng.random() < 0.10:
                        runners[0], runners[1] = False, True
                elif result == 'ground_out':
                    if runners[0] and outs < 2 and self.rng.random() < 0.20:
                        outs += 1
                        runners[0] = False
                    elif runners[0] and self.rng.random() < 0.20:
                        runners[0], runners[1] = False, True
                    elif runners[1] and not runners[2] and self.rng.random() < 0.10:
                        runners[1], runners[2] = False, True
                outs += 1
            elif result == 'walk':
                runs_delta, runners = self._advance_walk(runners)
                runs += runs_delta
            elif result in {'single', 'hit'}:
                runs += int(runners[2])
                runners = [True, runners[0], runners[1]]
                hits += 1
            elif result == 'double':
                runs += int(runners[2]) + int(runners[1])
                runners = [False, True, runners[0]]
                hits += 1
            elif result == 'triple':
                runs += sum(runners)
                runners = [False, False, True]
                hits += 1
            elif result == 'home_run':
                runs += 1 + sum(runners)
                runners = [False, False, False]
                hits += 1
            elif result == 'error':
                runs += int(runners[2])
                runners = [True, runners[0], runners[1]]

            batter_idx += 1
            if walkoff_target is not None and runs > walkoff_target:
                break

        return runs, hits, strikeouts, total_pitches, batter_idx % len(lineup)

    @staticmethod
    def _advance_walk(runners: List[bool]) -> tuple:
        first, second, third = runners
        runs = int(first and second and third)
        if first:
            return runs, [True, True, second or third]
        return runs, [True, second, third]

    @staticmethod
    def _new_pitching_staff(pitchers: List[Dict]) -> Dict:
        roster = pitchers or [{'pitcher_id': None, 'name': 'League-average pitcher'}]
        return {
            'pitchers': roster,
            'index': 0,
            'pitches': [0] * len(roster),
            'batters': [0] * len(roster),
        }

    def _current_pitcher(self, staff: Dict) -> tuple:
        index = staff['index']
        if index + 1 < len(staff['pitchers']) and (
            staff['pitches'][index] >= 85 or staff['batters'][index] >= 27
        ):
            staff['index'] += 1
            index = staff['index']

        pitcher = staff['pitchers'][index]
        stats = self._get_pitcher_stats(pitcher)
        fatigue = max(0, staff['pitches'][index] - 65)
        if fatigue:
            stats = dict(stats)
            stats['k_rate'] = max(0.05, stats.get('k_rate', 0.20) - fatigue * 0.0008)
            stats['bb_rate'] = min(0.25, stats.get('bb_rate', 0.08) + fatigue * 0.0006)
            stats['whiff_rate'] = max(0.05, stats.get('whiff_rate', 0.20) - fatigue * 0.0008)
            stats['fastball_avg_velo'] = max(
                80, stats.get('fastball_avg_velo', 92) - fatigue * 0.025
            )
        return pitcher, stats

    def _get_pitcher_stats(self, pitcher: Dict) -> Dict:
        """Load a pitcher's Statcast profile, falling back only when unavailable."""
        default_stats = {
            'fastball_pct': 0.60,
            'breaking_pct': 0.25,
            'changeup_pct': 0.15,
            'fastball_avg_velo': 92.0,
            'whiff_rate': 0.20,
            'k_rate': 0.20,
            'bb_rate': 0.08,
            'ba_against': 0.27,
        }

        if self.bvp_model is None:
            return default_stats

        stats = self.bvp_model.data_loader.get_pitcher_stats(
            pitcher.get('pitcher_id')
        )
        return {**default_stats, **(stats or {})}

    def _get_batter_stats(self, batter: Dict) -> Dict:
        """Load a batter's Statcast profile, falling back only when unavailable."""
        default_stats = {
            'contact_rate': 0.75,
            'chase_rate': 0.30,
            'gb_rate': 0.45,
            'ld_rate': 0.20,
            'fb_rate': 0.35,
            'ba': 0.27,
        }

        if self.bvp_model is None:
            return default_stats

        stats = self.bvp_model.data_loader.get_batter_stats(
            batter.get('batter_id')
        )
        return {**default_stats, **(stats or {})}

    def _get_matchup_prediction(self, pitcher: Dict, batter: Dict) -> Optional[Dict]:
        if self.bvp_model is None or not pitcher or not batter:
            return None
        pitcher_id = pitcher.get('pitcher_id')
        batter_id = batter.get('batter_id')
        if pitcher_id is None or batter_id is None:
            return None
        key = (pitcher_id, batter_id, pitcher.get('hand', 'R'), batter.get('hand', 'R'))
        if key not in self.matchup_cache:
            self.matchup_cache[key] = self.bvp_model.get_full_matchup_prediction(
                pitcher_id, batter_id, key[2], key[3]
            )
        return self.matchup_cache[key]

    def simulate_games_monte_carlo(self, away_team: Dict, home_team: Dict,
                                   away_pitchers: List[Dict], home_pitchers: List[Dict],
                                   num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulations.
        """

        away_wins = 0
        home_wins = 0
        ties = 0
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
            elif result.winner == 'home':
                home_wins += 1
            else:
                ties += 1

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
            'tie_count': ties,
            'tie_pct': ties / num_simulations,
            'avg_away_score': away_score_total / num_simulations,
            'avg_home_score': home_score_total / num_simulations,
            'avg_away_hits': away_hits_total / num_simulations,
            'avg_home_hits': home_hits_total / num_simulations,
            'avg_pitches_per_game': total_pitches_sim / num_simulations,
        }
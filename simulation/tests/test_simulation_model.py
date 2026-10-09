import unittest
from collections import Counter

import numpy as np
import pandas as pd

from src.bvp_model import HierarchicalBvPModel
from src.config import CONTACT_OUTCOMES
from src.data_loader import StatcastDataLoader
from src.game_simulator import GameSimulator, PitchSimulator
from src.real_data import RealDataProvider


def statcast_frame(rows):
    return pd.DataFrame(rows, columns=[
        'game_date', 'game_pk', 'at_bat_number', 'pitch_number', 'pitcher',
        'batter', 'stand', 'p_throws', 'pitch_type', 'release_speed', 'balls',
        'strikes', 'events', 'description', 'launch_angle', 'launch_speed', 'zone',
    ])


class StatcastProfileTests(unittest.TestCase):
    def test_preserves_pitch_rows_and_counts_terminal_pa_rows(self):
        frame = statcast_frame([
            ('2026-09-01', 1, 1, 1, 10, 20, 'R', 'R', 'FF', 95, 0, 0, None,
             'called_strike', None, None, 5),
            ('2026-09-01', 1, 1, 2, 10, 20, 'R', 'R', 'SL', 84, 0, 1, None,
             'swinging_strike', None, None, 12),
            ('2026-09-01', 1, 1, 3, 10, 20, 'R', 'R', 'FF', 96, 0, 2, 'single',
             'hit_into_play', 18, 95, 5),
        ])
        loader = StatcastDataLoader()
        loader.statcast_df = frame
        loader._preprocess_data()

        self.assertEqual(len(loader.statcast_df), 3)
        self.assertEqual(len(loader._pa_rows(loader.statcast_df)), 1)
        self.assertEqual(loader.get_pitcher_stats(10)['total_pa'], 1)
        self.assertEqual(loader.get_batter_stats(20)['total_pa'], 1)

    def test_sparse_player_stats_shrink_toward_priors(self):
        frame = statcast_frame([
            ('2026-09-01', 1, 1, 3, 10, 20, 'R', 'R', 'FF', 99, 0, 2,
             'home_run', 'hit_into_play', 35, 105, 5),
        ])
        loader = StatcastDataLoader()
        loader.statcast_df = frame
        loader._preprocess_data()
        loader._set_analysis_end_date()

        batter = loader.get_batter_stats(20)
        pitcher = loader.get_pitcher_stats(10)
        self.assertGreater(batter['ba'], 0.27)
        self.assertLess(batter['ba'], 1.0)
        self.assertGreater(pitcher['ba_against'], 0.27)
        self.assertLess(pitcher['ba_against'], 1.0)
        self.assertGreater(pitcher['fastball_avg_velo'], 92)
        self.assertLess(pitcher['fastball_avg_velo'], 99)

    def test_bvp_handedness_is_filtered_and_blended(self):
        rows = []
        for index, (stand, event) in enumerate([
            ('R', 'single'), ('R', 'single'), ('L', 'field_out'), ('L', 'field_out'),
        ]):
            rows.append((
                '2026-09-01', index, 1, 1, 10, 20, stand, 'R', 'FF', 94,
                0, 0, event, 'hit_into_play', 15, 90, 5,
            ))
        loader = StatcastDataLoader()
        loader.statcast_df = statcast_frame(rows)
        loader._preprocess_data()
        model = HierarchicalBvPModel(loader)

        right_split = model._get_handedness_ba('RHH_vs_RHP', 20)
        left_split = model._get_handedness_ba('LHH_vs_RHP', 20)
        prediction = model.get_full_matchup_prediction(10, 20, 'R', 'R')

        self.assertGreater(right_split, left_split)
        self.assertGreater(prediction['confidence'], 0)
        self.assertAlmostEqual(sum(prediction['outcomes'].values()), 1.0)


class PitchAndGameSimulationTests(unittest.TestCase):
    def test_pitcher_quality_changes_strike_probability(self):
        strong = {'k_rate': 0.35, 'bb_rate': 0.04, 'fastball_avg_velo': 98}
        weak = {'k_rate': 0.12, 'bb_rate': 0.12, 'fastball_avg_velo': 89}
        strong_sim = PitchSimulator(np.random.RandomState(41))
        weak_sim = PitchSimulator(np.random.RandomState(41))

        strong_strikes = sum(
            strong_sim.is_strike(strong, 'fastball') for _ in range(2000)
        )
        weak_strikes = sum(
            weak_sim.is_strike(weak, 'fastball') for _ in range(2000)
        )
        self.assertGreater(strong_strikes, weak_strikes)

        strong_contact = PitchSimulator(np.random.RandomState(7))
        weak_contact = PitchSimulator(np.random.RandomState(7))
        batter = {'contact_rate': 0.75}
        self.assertLess(
            sum(strong_contact.does_contact(batter, strong, 'fastball') for _ in range(2000)),
            sum(weak_contact.does_contact(batter, weak, 'fastball') for _ in range(2000)),
        )

    def test_contact_distributions_include_extra_base_hits_and_errors(self):
        for distribution in CONTACT_OUTCOMES.values():
            self.assertAlmostEqual(sum(distribution.values()), 1.0)
        simulator = PitchSimulator(np.random.RandomState(12))
        results = Counter(
            simulator.get_contact_outcome('line_drive') for _ in range(10000)
        )
        for event in ('single', 'double', 'triple', 'home_run', 'error'):
            self.assertGreater(results[event], 0)

    def test_walk_forces_only_occupied_runners(self):
        self.assertEqual(
            GameSimulator._advance_walk([False, True, True]),
            (0, [True, True, True]),
        )
        self.assertEqual(
            GameSimulator._advance_walk([True, False, True]),
            (0, [True, True, True]),
        )
        self.assertEqual(
            GameSimulator._advance_walk([True, True, True]),
            (1, [True, True, True]),
        )

    def test_hits_and_errors_score_and_advance_runners(self):
        class ScriptedAtBat:
            def __init__(self):
                self.results = iter([
                    'walk', 'single', 'double', 'triple', 'home_run', 'error',
                    'out', 'out', 'out',
                ])

            def simulate_at_bat(self, pitcher_stats, batter_stats, runners,
                                matchup_prediction=None):
                return next(self.results), 1, 0

        simulator = GameSimulator(rng=np.random.RandomState(2))
        simulator.ab_simulator = ScriptedAtBat()
        runs, hits, strikeouts, pitches, _ = simulator._simulate_half_inning(
            [{'batter_id': index} for index in range(9)],
            simulator._new_pitching_staff([{'pitcher_id': 1}]),
            inning=1,
        )
        self.assertEqual((runs, hits, strikeouts, pitches), (5, 4, 0, 9))

    def test_home_team_stops_after_walkoff_run(self):
        class WalkoffAtBat:
            calls = 0

            def simulate_at_bat(self, pitcher_stats, batter_stats, runners,
                                matchup_prediction=None):
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError('at-bat continued after walk-off')
                return 'home_run', 4, 1

        simulator = GameSimulator(rng=np.random.RandomState(4))
        scripted = WalkoffAtBat()
        simulator.ab_simulator = scripted
        runs, hits, strikeouts, pitches, _ = simulator._simulate_half_inning(
            [{'batter_id': 1}],
            simulator._new_pitching_staff([{'pitcher_id': 10}]),
            inning=9,
            walkoff_target=0,
        )
        self.assertEqual((runs, hits, strikeouts, pitches), (1, 1, 0, 4))

    def test_lineup_continues_and_tied_game_reaches_extra_innings(self):
        class AlwaysOut:
            @staticmethod
            def simulate_at_bat(pitcher_stats, batter_stats, runners,
                                matchup_prediction=None):
                return 'out', 1, 0

        simulator = GameSimulator(rng=np.random.RandomState(1))
        simulator.ab_simulator = AlwaysOut()
        order = []
        simulator._get_batter_stats = lambda batter: (
            order.append(batter['batter_id']) or {}
        )
        team = {'lineup': [{'batter_id': index} for index in range(9)]}
        staff = [{'pitcher_id': 100}, {'pitcher_id': 101}]

        result = simulator.simulate_game(team, team, staff, staff)

        self.assertEqual(result.winner, 'tie')
        self.assertEqual(result.total_pitches, 90)
        self.assertEqual(order[:12], [0, 1, 2, 0, 1, 2, 3, 4, 5, 3, 4, 5])

    def test_pitching_staff_switches_to_reliever(self):
        simulator = GameSimulator()
        staff = simulator._new_pitching_staff([
            {'pitcher_id': 100}, {'pitcher_id': 101},
        ])
        staff['pitches'][0] = 85

        pitcher, _ = simulator._current_pitcher(staff)

        self.assertEqual(pitcher['pitcher_id'], 101)

    def test_bvp_hit_evidence_changes_contact_outcome_distribution(self):
        batter = {'ba': 0.20}
        prediction = {
            'confidence': 0.9,
            'raw_predictions': {'ba': {'predicted_ba': 0.40}},
        }
        baseline = PitchSimulator(np.random.RandomState(3))
        adjusted = PitchSimulator(np.random.RandomState(3))
        baseline_hits = sum(
            baseline.get_contact_outcome('ground_ball') in {'single', 'double', 'triple', 'home_run'}
            for _ in range(5000)
        )
        adjusted_hits = sum(
            adjusted.get_contact_outcome('ground_ball', prediction, batter)
            in {'single', 'double', 'triple', 'home_run'}
            for _ in range(5000)
        )
        self.assertGreater(adjusted_hits, baseline_hits)

    def test_game_simulator_passes_cached_bvp_prediction_to_at_bats(self):
        class DataLoader:
            @staticmethod
            def get_pitcher_stats(pitcher_id):
                return {'k_rate': 0.22, 'bb_rate': 0.08}

            @staticmethod
            def get_batter_stats(batter_id):
                return {'ba': 0.27, 'contact_rate': 0.75}

        class BvPModel:
            data_loader = DataLoader()

            def __init__(self):
                self.calls = 0

            def get_full_matchup_prediction(self, *args):
                self.calls += 1
                return {'confidence': 0.5, 'raw_predictions': {}}

        class CapturePrediction:
            def __init__(self):
                self.predictions = []

            def simulate_at_bat(self, pitcher_stats, batter_stats, runners,
                                matchup_prediction=None):
                self.predictions.append(matchup_prediction)
                return 'out', 1, 0

        model = BvPModel()
        simulator = GameSimulator(model, np.random.RandomState(1))
        capture = CapturePrediction()
        simulator.ab_simulator = capture
        lineup = [{'batter_id': 20}]
        simulator._simulate_half_inning(
            lineup,
            simulator._new_pitching_staff([{'pitcher_id': 10}]),
            inning=1,
        )

        self.assertEqual(model.calls, 1)
        self.assertEqual(len(capture.predictions), 3)
        self.assertTrue(all(capture.predictions))


class RealLineupTests(unittest.TestCase):
    def test_recent_lineup_is_used_before_active_roster_estimate(self):
        provider = RealDataProvider(data_dir=__import__('pathlib').Path('/tmp/sim-test-data'))
        lineup = [
            {'batter_id': index, 'hand': 'R', 'name': f'Batter {index}'}
            for index in range(9)
        ]
        provider._recent_lineup = lambda team_id, game_date: lineup
        provider._roster_lineup = lambda team_id: self.fail('roster fallback should not be used')
        game = {
            'officialDate': '2026-09-30',
            'teams': {'away': {'team': {'id': 110, 'name': 'Orioles'}}},
        }
        boxscore = {'teams': {'away': {'players': {}, 'battingOrder': []}}}

        team = provider._mlb_team(game, boxscore, 'away')

        self.assertEqual(team['lineup_source'], 'most_recent_completed_game')
        self.assertFalse(team['lineup_confirmed'])
        self.assertEqual(len(team['lineup']), 9)

    def test_probable_starter_is_followed_by_active_bullpen(self):
        provider = RealDataProvider(data_dir=__import__('pathlib').Path('/tmp/sim-test-data'))
        reliever = {'pitcher_id': 200, 'hand': 'L', 'name': 'Reliever'}
        provider._mlb_roster_pitchers = lambda team_id: [reliever]
        game = {
            'teams': {
                'away': {
                    'team': {'id': 110},
                    'probablePitcher': {
                        'id': 100, 'fullName': 'Starter',
                        'pitchHand': {'code': 'R'},
                    },
                }
            }
        }

        pitchers = provider._mlb_pitchers(game, {'teams': {}}, 'away')

        self.assertEqual([pitcher['pitcher_id'] for pitcher in pitchers], [100, 200])


if __name__ == '__main__':
    unittest.main()

# simulation/src/data_loader.py

import pandas as pd
from pybaseball import statcast
from typing import Dict, Tuple, List
import src.config as config
import logging

logger = logging.getLogger(__name__)


class StatcastDataLoader:
    """Load and cache Statcast data for BvP analysis."""

    def __init__(self):
        self.statcast_df = None
        self.pitcher_stats = {}
        self.batter_stats = {}
        self.matchup_history = {}

    def load_season(self, year: int, use_cache: bool = True) -> pd.DataFrame:
        """Load full season Statcast data."""
        logger.info(f"Loading Statcast data for {year}...")

        try:
            # Try to load from pybaseball with caching
            self.statcast_df = statcast(f'{year}-01-01', f'{year}-12-31')

            if self.statcast_df is None or len(self.statcast_df) == 0:
                logger.warning(f"Empty data returned for {year}. Using mock data.")
                return self._get_mock_data()

            self._preprocess_data()
            logger.info(f"Successfully loaded {len(self.statcast_df)} records from Statcast")
            return self.statcast_df

        except Exception as e:
            logger.error(f"Error loading from pybaseball: {e}")
            logger.warning("Falling back to mock data for demonstration")
            return self._get_mock_data()

    def _get_mock_data(self) -> pd.DataFrame:
        """
        Return mock Statcast data for development/testing.
        This allows the model to run without live data.
        """
        logger.info("Generating mock Statcast data for testing...")

        import numpy as np

        # Create mock data with realistic structure
        n_records = 5000

        pitcher_ids = np.random.choice(range(500000, 600000), n_records)
        batter_ids = np.random.choice(range(400000, 650000), n_records)

        data = {
            'pitcher': pitcher_ids,
            'batter': batter_ids,
            'pitch_type': np.random.choice(['FF', 'SL', 'CU', 'CH'], n_records),
            'release_speed': np.random.normal(92, 4, n_records),
            'balls': np.random.randint(0, 4, n_records),
            'strikes': np.random.randint(0, 3, n_records),
            'events': np.random.choice([
                'single', 'double', 'triple', 'home_run', 'strikeout',
                'walk', 'field_out', 'grounded_into_double_play', 'sac_bunt'
            ], n_records),
            'description': np.random.choice([
                'hit_into_play', 'swinging_strike', 'called_strike', 'ball', 'foul'
            ], n_records),
            'launch_angle': np.random.normal(20, 25, n_records),
            'exit_velocity': np.random.normal(85, 15, n_records),
            'zone': np.random.choice([i for i in range(1, 15)] + [None], n_records),
        }

        self.statcast_df = pd.DataFrame(data)
        self._preprocess_data()

        logger.info(f"Mock data ready: {len(self.statcast_df)} records")
        return self.statcast_df

    def _preprocess_data(self):
        """Clean and standardize Statcast data."""
        logger.info("Preprocessing data...")

        # Remove nulls
        self.statcast_df = self.statcast_df.dropna(subset=['pitcher', 'batter', 'events'])

        # Create pitch type grouping
        self.statcast_df['pitch_category'] = self.statcast_df['pitch_type'].apply(
            self._categorize_pitch
        )

        # Create count string
        self.statcast_df['count'] = (
                self.statcast_df['balls'].astype(str) + '_' +
                self.statcast_df['strikes'].astype(str)
        )

        # Determine if at-bat result was hit
        self.statcast_df['is_hit'] = self.statcast_df['events'].apply(
            lambda x: 1 if any(h in str(x).lower() for h in ['single', 'double', 'triple', 'home_run']) else 0
        )

        # Contact type
        self.statcast_df['contact_type'] = self.statcast_df.apply(
            self._determine_contact_type, axis=1
        )

        logger.info("Data preprocessing complete")

    @staticmethod
    def _categorize_pitch(pitch_type: str) -> str:
        """Group pitch types into categories."""
        if pd.isna(pitch_type):
            return 'other'

        pitch_type = str(pitch_type).upper()

        fastballs = ['FF', 'FT', 'FA']
        breaking = ['CU', 'SL', 'KC', 'SLV']
        changeups = ['CH', 'FS']

        if pitch_type in fastballs:
            return 'fastball'
        elif pitch_type in breaking:
            return 'breaking'
        elif pitch_type in changeups:
            return 'changeup'
        else:
            return 'other'

    @staticmethod
    def _determine_contact_type(row) -> str:
        """Determine contact type from launch angle and exit velo."""
        try:
            if pd.isna(row['launch_angle']) or pd.isna(row['exit_velocity']):
                return 'unknown'

            angle = float(row['launch_angle'])

            if angle < 10:
                return 'ground_ball'
            elif 10 <= angle <= 25:
                return 'line_drive'
            elif angle > 25:
                return 'fly_ball'
            else:
                return 'unknown'
        except:
            return 'unknown'

    def get_pitcher_stats(self, pitcher_id: int, min_pa: int = 10) -> Dict:
        """Get aggregated stats for a pitcher."""
        try:
            pitcher_data = self.statcast_df[self.statcast_df['pitcher'] == pitcher_id]

            if len(pitcher_data) < min_pa:
                return None

            fastball_count = (pitcher_data['pitch_category'] == 'fastball').sum()
            breaking_count = (pitcher_data['pitch_category'] == 'breaking').sum()

            return {
                'pitcher_id': pitcher_id,
                'total_pa': len(pitcher_data),
                'fastball_pct': fastball_count / len(pitcher_data) if len(pitcher_data) > 0 else 0.60,
                'breaking_pct': breaking_count / len(pitcher_data) if len(pitcher_data) > 0 else 0.25,
                'changeup_pct': 1 - (fastball_count + breaking_count) / len(pitcher_data) if len(
                    pitcher_data) > 0 else 0.15,
                'fastball_avg_velo': pitcher_data[pitcher_data['pitch_category'] == 'fastball'][
                                         'release_speed'].mean() or 92,
                'whiff_rate': self._calculate_whiff_rate(pitcher_data),
                'k_rate': (pitcher_data['events'].astype(str).str.contains('strikeout', na=False)).sum() / len(
                    pitcher_data) if len(pitcher_data) > 0 else 0.20,
                'bb_rate': (pitcher_data['events'].astype(str).str.contains('walk', na=False)).sum() / len(
                    pitcher_data) if len(pitcher_data) > 0 else 0.08,
                'ba_against': pitcher_data['is_hit'].sum() / len(pitcher_data) if len(pitcher_data) > 0 else 0.270,
            }
        except Exception as e:
            logger.warning(f"Error getting pitcher stats for {pitcher_id}: {e}")
            return None

    def get_batter_stats(self, batter_id: int, min_pa: int = 10) -> Dict:
        """Get aggregated stats for a batter."""
        try:
            batter_data = self.statcast_df[self.statcast_df['batter'] == batter_id]

            if len(batter_data) < min_pa:
                return None

            return {
                'batter_id': batter_id,
                'total_pa': len(batter_data),
                'ba': batter_data['is_hit'].sum() / len(batter_data) if len(batter_data) > 0 else 0.270,
                'contact_rate': (batter_data['description'].astype(str).str.contains('hit_into_play',
                                                                                     na=False)).sum() / len(
                    batter_data) if len(batter_data) > 0 else 0.75,
                'whiff_rate': (batter_data['description'].astype(str).str.contains('swinging_strike',
                                                                                   na=False)).sum() / len(
                    batter_data) if len(batter_data) > 0 else 0.20,
                'chase_rate': self._calculate_chase_rate(batter_data),
                'gb_rate': (batter_data['contact_type'] == 'ground_ball').sum() / len(batter_data) if len(
                    batter_data) > 0 else 0.45,
                'ld_rate': (batter_data['contact_type'] == 'line_drive').sum() / len(batter_data) if len(
                    batter_data) > 0 else 0.20,
                'fb_rate': (batter_data['contact_type'] == 'fly_ball').sum() / len(batter_data) if len(
                    batter_data) > 0 else 0.35,
            }
        except Exception as e:
            logger.warning(f"Error getting batter stats for {batter_id}: {e}")
            return None

    def get_matchup_history(self, pitcher_id: int, batter_id: int) -> Dict:
        """Get direct history between pitcher and batter."""
        try:
            matchup_data = self.statcast_df[
                (self.statcast_df['pitcher'] == pitcher_id) &
                (self.statcast_df['batter'] == batter_id)
                ]

            if len(matchup_data) == 0:
                return {'pa_count': 0}

            return {
                'pa_count': len(matchup_data),
                'ba': matchup_data['is_hit'].sum() / len(matchup_data),
                'k_rate': (matchup_data['events'].astype(str).str.contains('strikeout', na=False)).sum() / len(
                    matchup_data),
                'bb_rate': (matchup_data['events'].astype(str).str.contains('walk', na=False)).sum() / len(
                    matchup_data),
            }
        except Exception as e:
            logger.warning(f"Error getting matchup history: {e}")
            return {'pa_count': 0}

    @staticmethod
    def _calculate_whiff_rate(data: pd.DataFrame) -> float:
        """Calculate swinging strike rate."""
        try:
            swings = data['description'].astype(str).str.contains('swinging_strike', na=False, regex=True).sum()
            total_pitches = len(data)
            return swings / total_pitches if total_pitches > 0 else 0.20
        except:
            return 0.20

    @staticmethod
    def _calculate_chase_rate(data: pd.DataFrame) -> float:
        """Calculate rate of swinging at pitches outside zone."""
        try:
            pitches_outside_zone = data['zone'].isna().sum()
            swings_outside = data[data['zone'].isna()]['description'].astype(str).str.contains(
                'swinging_strike|hit_into_play', na=False).sum()
            return swings_outside / pitches_outside_zone if pitches_outside_zone > 0 else 0.30
        except:
            return 0.30
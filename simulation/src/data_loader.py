# simulation/src/data_loader.py

import os
import calendar
from pathlib import Path

import pandas as pd

# pybaseball reads this setting while it is imported.
os.environ.setdefault(
    'PYBASEBALL_CACHE',
    str(Path(__file__).resolve().parents[1] / 'data')
)

from pybaseball import cache, statcast
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

    def load_season(self, year: int, use_cache: bool = True,
                    allow_mock_data: bool = False) -> pd.DataFrame:
        """Load full season Statcast data, optionally allowing development data."""
        logger.info(f"Loading Statcast data for {year}...")
        season_cache = Path(__file__).resolve().parents[1] / 'data' / f'statcast_{year}.pkl'
        season_cache.parent.mkdir(parents=True, exist_ok=True)

        try:
            if use_cache and season_cache.exists():
                self.statcast_df = pd.read_pickle(season_cache)
                self._preprocess_data()
                logger.info("Loaded %s Statcast records from %s", len(self.statcast_df), season_cache)
                return self.statcast_df

            if use_cache:
                cache.enable()
                logger.info("pybaseball cache enabled")
            else:
                cache.disable()

            monthly_frames = []
            for month in range(1, 13):
                month_cache = season_cache.with_name(
                    f'statcast_{year}_{month:02d}.pkl'
                )

                if use_cache and month_cache.exists():
                    month_df = pd.read_pickle(month_cache)
                    logger.info(
                        "Loaded cached Statcast month %s/%s (%s records)",
                        year, month, len(month_df)
                    )
                else:
                    last_day = calendar.monthrange(year, month)[1]
                    logger.info("Downloading Statcast month %s/%s", year, month)
                    month_df = statcast(
                        f'{year}-{month:02d}-01',
                        f'{year}-{month:02d}-{last_day:02d}',
                        verbose=True,
                        parallel=False,
                    )
                    if use_cache:
                        month_df.to_pickle(month_cache)

                if month_df is not None and len(month_df) > 0:
                    monthly_frames.append(month_df)

            self.statcast_df = (
                pd.concat(monthly_frames, ignore_index=True)
                if monthly_frames else pd.DataFrame()
            )

            if self.statcast_df is None or len(self.statcast_df) == 0:
                raise RuntimeError(f"No Statcast data returned for {year}")

            self._preprocess_data()
            if use_cache:
                self.statcast_df.to_pickle(season_cache)
            logger.info(f"Successfully loaded {len(self.statcast_df)} records from Statcast")
            return self.statcast_df

        except Exception as e:
            logger.error(f"Error loading from pybaseball: {e}")
            if allow_mock_data:
                logger.warning("Using mock data because allow_mock_data=True")
                return self._get_mock_data()
            raise RuntimeError(
                f"Could not load real Statcast data for {year}. "
                "Check connectivity or run again after the cache is populated."
            ) from e

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
            if pitcher_id in self.pitcher_stats:
                return self.pitcher_stats[pitcher_id]

            pitcher_data = self.statcast_df[self.statcast_df['pitcher'] == pitcher_id]

            if len(pitcher_data) < min_pa:
                return None

            fastball_count = (pitcher_data['pitch_category'] == 'fastball').sum()
            breaking_count = (pitcher_data['pitch_category'] == 'breaking').sum()
            fastball_velo = pitcher_data.loc[
                pitcher_data['pitch_category'] == 'fastball',
                'release_speed'
            ].mean()
            if pd.isna(fastball_velo):
                fastball_velo = 92.0

            stats = {
                'pitcher_id': pitcher_id,
                'total_pa': len(pitcher_data),
                'fastball_pct': fastball_count / len(pitcher_data) if len(pitcher_data) > 0 else 0.60,
                'breaking_pct': breaking_count / len(pitcher_data) if len(pitcher_data) > 0 else 0.25,
                'changeup_pct': 1 - (fastball_count + breaking_count) / len(pitcher_data) if len(
                    pitcher_data) > 0 else 0.15,
                'fastball_avg_velo': fastball_velo,
                'whiff_rate': self._calculate_whiff_rate(pitcher_data),
                'k_rate': (pitcher_data['events'].astype(str).str.contains('strikeout', na=False)).sum() / len(
                    pitcher_data) if len(pitcher_data) > 0 else 0.20,
                'bb_rate': (pitcher_data['events'].astype(str).str.contains('walk', na=False)).sum() / len(
                    pitcher_data) if len(pitcher_data) > 0 else 0.08,
                'ba_against': pitcher_data['is_hit'].sum() / len(pitcher_data) if len(pitcher_data) > 0 else 0.270,
            }
            self.pitcher_stats[pitcher_id] = stats
            return stats
        except Exception as e:
            logger.warning(f"Error getting pitcher stats for {pitcher_id}: {e}")
            return None

    def get_batter_stats(self, batter_id: int, min_pa: int = 10) -> Dict:
        """Get aggregated stats for a batter."""
        try:
            if batter_id in self.batter_stats:
                return self.batter_stats[batter_id]

            batter_data = self.statcast_df[self.statcast_df['batter'] == batter_id]

            if len(batter_data) < min_pa:
                return None

            stats = {
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
            self.batter_stats[batter_id] = stats
            return stats
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
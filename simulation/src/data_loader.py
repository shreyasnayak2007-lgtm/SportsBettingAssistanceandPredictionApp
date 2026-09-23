# simulation/src/data_loader.py

import pandas as pd
from pybaseball import statcast
from typing import Dict, Tuple, List
import config


class StatcastDataLoader:
    """Load and cache Statcast data for BvP analysis."""

    def __init__(self):
        self.statcast_df = None
        self.pitcher_stats = {}
        self.batter_stats = {}
        self.matchup_history = {}

    def load_season(self, year: int) -> pd.DataFrame:
        """Load full season Statcast data."""
        print(f"Loading Statcast data for {year}...")
        self.statcast_df = statcast(f'{year}-01-01', f'{year}-12-31')
        self._preprocess_data()
        return self.statcast_df

    def _preprocess_data(self):
        """Clean and standardize Statcast data."""
        # Remove nulls
        self.statcast_df = self.statcast_df.dropna(subset=['pitcher', 'batter', 'events'])

        # Create pitch type grouping (fastball, breaking, changeup)
        self.statcast_df['pitch_category'] = self.statcast_df['pitch_type'].apply(
            self._categorize_pitch
        )

        # Create count string (balls-strikes)
        self.statcast_df['count'] = (
                self.statcast_df['balls'].astype(str) + '_' +
                self.statcast_df['strikes'].astype(str)
        )

        # Determine if at-bat result was hit (1) or out (0)
        self.statcast_df['is_hit'] = self.statcast_df['events'].apply(
            lambda x: 1 if 'single' in x or 'double' in x or 'triple' in x or 'home_run' in x else 0
        )

        # Contact type
        self.statcast_df['contact_type'] = self.statcast_df.apply(
            self._determine_contact_type, axis=1
        )

    @staticmethod
    def _categorize_pitch(pitch_type: str) -> str:
        """Group pitch types into categories."""
        fastballs = ['FF', 'FT', 'FA']  # Four-seam, Two-seam, Fastball
        breaking = ['CU', 'SL', 'KC']  # Curveball, Slider, Knuckle curve
        changeups = ['CH', 'FS']  # Changeup, Forkball

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
        if pd.isna(row['launch_angle']) or pd.isna(row['exit_velocity']):
            return 'unknown'

        angle = row['launch_angle']
        velo = row['exit_velocity']

        if angle < 10:
            return 'ground_ball'
        elif 10 <= angle <= 25:
            return 'line_drive'
        elif angle > 25:
            return 'fly_ball'
        else:
            return 'unknown'

    def get_pitcher_stats(self, pitcher_id: int, min_pa: int = 10) -> Dict:
        """Get aggregated stats for a pitcher."""
        pitcher_data = self.statcast_df[self.statcast_df['pitcher'] == pitcher_id]

        if len(pitcher_data) < min_pa:
            return None

        return {
            'pitcher_id': pitcher_id,
            'total_pa': len(pitcher_data),
            'fastball_pct': (pitcher_data['pitch_category'] == 'fastball').sum() / len(pitcher_data),
            'breaking_pct': (pitcher_data['pitch_category'] == 'breaking').sum() / len(pitcher_data),
            'changeup_pct': (pitcher_data['pitch_category'] == 'changeup').sum() / len(pitcher_data),
            'fastball_avg_velo': pitcher_data[pitcher_data['pitch_category'] == 'fastball']['release_speed'].mean(),
            'whiff_rate': self._calculate_whiff_rate(pitcher_data),
            'k_rate': (pitcher_data['events'].str.contains('strikeout', na=False)).sum() / len(pitcher_data),
            'bb_rate': (pitcher_data['events'].str.contains('walk', na=False)).sum() / len(pitcher_data),
            'ba_against': pitcher_data['is_hit'].sum() / len(pitcher_data),
        }

    def get_batter_stats(self, batter_id: int, min_pa: int = 10) -> Dict:
        """Get aggregated stats for a batter."""
        batter_data = self.statcast_df[self.statcast_df['batter'] == batter_id]

        if len(batter_data) < min_pa:
            return None

        return {
            'batter_id': batter_id,
            'total_pa': len(batter_data),
            'ba': batter_data['is_hit'].sum() / len(batter_data),
            'contact_rate': (batter_data['description'].str.contains('hit_into_play', na=False)).sum() / len(
                batter_data),
            'whiff_rate': (batter_data['description'].str.contains('swinging_strike', na=False)).sum() / len(
                batter_data),
            'chase_rate': self._calculate_chase_rate(batter_data),
            'gb_rate': (batter_data['contact_type'] == 'ground_ball').sum() / len(batter_data),
            'ld_rate': (batter_data['contact_type'] == 'line_drive').sum() / len(batter_data),
            'fb_rate': (batter_data['contact_type'] == 'fly_ball').sum() / len(batter_data),
        }

    def get_matchup_history(self, pitcher_id: int, batter_id: int) -> Dict:
        """Get direct history between pitcher and batter."""
        matchup_data = self.statcast_df[
            (self.statcast_df['pitcher'] == pitcher_id) &
            (self.statcast_df['batter'] == batter_id)
            ]

        if len(matchup_data) == 0:
            return {'pa_count': 0}

        return {
            'pa_count': len(matchup_data),
            'ba': matchup_data['is_hit'].sum() / len(matchup_data),
            'k_rate': (matchup_data['events'].str.contains('strikeout', na=False)).sum() / len(matchup_data),
            'bb_rate': (matchup_data['events'].str.contains('walk', na=False)).sum() / len(matchup_data),
        }

    @staticmethod
    def _calculate_whiff_rate(data: pd.DataFrame) -> float:
        """Calculate swinging strike rate."""
        swings = data['description'].str.contains('swinging_strike|swinging_strike_blocked', na=False, regex=True).sum()
        total_pitches = len(data)
        return swings / total_pitches if total_pitches > 0 else 0

    @staticmethod
    def _calculate_chase_rate(data: pd.DataFrame) -> float:
        """Calculate rate of swinging at pitches outside zone."""
        pitches_outside_zone = data['zone'].isna().sum()  # zone column is NA when outside zone
        swings_outside = data[data['zone'].isna()]['description'].str.contains('swinging_strike|hit_into_play',
                                                                               na=False).sum()
        return swings_outside / pitches_outside_zone if pitches_outside_zone > 0 else 0
# simulation/src/data_loader.py

import os
import calendar
from pathlib import Path
from datetime import date

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

    WINDOW_WEIGHTS = {
        'five_years': 0.10,
        'season': 0.35,
        'month': 0.30,
        'week': 0.25,
    }

    def __init__(self):
        self.statcast_df = None
        self.pitcher_stats = {}
        self.batter_stats = {}
        self.matchup_history = {}
        self.analysis_end_date = pd.Timestamp(date.today())

    def load_season(self, year: int, use_cache: bool = True,
                    allow_mock_data: bool = False) -> pd.DataFrame:
        """Load full season Statcast data, optionally allowing development data."""
        logger.info(f"Loading Statcast data for {year}...")
        season_cache = Path(__file__).resolve().parents[1] / 'data' / f'statcast_{year}_pitches_v2.pkl'
        season_cache.parent.mkdir(parents=True, exist_ok=True)

        try:
            if use_cache and season_cache.exists() and year != date.today().year:
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
                today = date.today()
                is_future_month = (year, month) > (today.year, today.month)
                if is_future_month:
                    continue

                is_current_month = year == today.year and month == today.month
                cache_name = (
                    f'statcast_{year}_{month:02d}_through_{today.day}_pitches_v2.pkl'
                    if is_current_month
                    else f'statcast_{year}_{month:02d}_pitches_v2.pkl'
                )
                month_cache = season_cache.with_name(cache_name)

                if use_cache and month_cache.exists() and not is_current_month:
                    month_df = pd.read_pickle(month_cache)
                    logger.info(
                        "Loaded cached Statcast month %s/%s (%s records)",
                        year, month, len(month_df)
                    )
                else:
                    last_day = calendar.monthrange(year, month)[1]
                    if year == today.year and month == today.month:
                        last_day = today.day
                    logger.info("Downloading Statcast month %s/%s", year, month)
                    if use_cache and is_current_month:
                        cache.disable()
                    try:
                        month_df = statcast(
                            f'{year}-{month:02d}-01',
                            f'{year}-{month:02d}-{last_day:02d}',
                            verbose=True,
                            parallel=False,
                        )
                    finally:
                        if use_cache and is_current_month:
                            cache.enable()
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

        if 'game_date' in self.statcast_df.columns:
            self.statcast_df['game_date'] = pd.to_datetime(
                self.statcast_df['game_date'], errors='coerce'
            )

        # Keep non-terminal pitches for pitch mix and whiff metrics.
        self.statcast_df = self.statcast_df.dropna(subset=['pitcher', 'batter']).copy()

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
        self.statcast_df['events'] = self.statcast_df['events'].fillna('').astype(str).str.lower()
        self.statcast_df['is_pa_result'] = self.statcast_df['events'].ne('')
        self.statcast_df['is_hit'] = self.statcast_df['events'].isin(
            {'single', 'double', 'triple', 'home_run'}
        ).astype(int)

        # Contact type
        self.statcast_df['contact_type'] = self.statcast_df.apply(
            self._determine_contact_type, axis=1
        )

        logger.info("Data preprocessing complete")

    @staticmethod
    def _pa_rows(data: pd.DataFrame) -> pd.DataFrame:
        """Return terminal Statcast rows, one outcome row per plate appearance."""
        return data[data['is_pa_result']]

    def _set_analysis_end_date(self):
        """Use the latest available pitch as the end of recency windows."""
        if 'game_date' not in self.statcast_df.columns:
            return

        available_dates = self.statcast_df['game_date'].dropna()
        if not available_dates.empty:
            self.analysis_end_date = available_dates.max().normalize()

    def _player_windows(self, player_column: str, player_id: int) -> Dict[str, pd.DataFrame]:
        """Return a player's Statcast rows for each weighted time window."""
        player_data = self.statcast_df[
            self.statcast_df[player_column] == player_id
        ]
        if player_data.empty:
            return {}
        if 'game_date' not in player_data.columns:
            return {'five_years': player_data}

        end_date = self.analysis_end_date
        season_start = pd.Timestamp(year=end_date.year, month=1, day=1)
        return {
            'five_years': player_data[
                player_data['game_date'] >= end_date - pd.DateOffset(years=5)
            ],
            'season': player_data[player_data['game_date'] >= season_start],
            'month': player_data[
                player_data['game_date'] >= end_date - pd.Timedelta(days=30)
            ],
            'week': player_data[
                player_data['game_date'] >= end_date - pd.Timedelta(days=7)
            ],
        }

    @classmethod
    def _weighted_stat(cls, windows: Dict[str, pd.DataFrame], calculator) -> float:
        """Blend available windows and renormalize weights when needed."""
        total = 0.0
        available_weight = 0.0
        for window_name, window_data in windows.items():
            if window_data.empty:
                continue
            value = calculator(window_data)
            if value is None or pd.isna(value):
                continue
            weight = cls.WINDOW_WEIGHTS[window_name]
            total += weight * float(value)
            available_weight += weight
        return total / available_weight if available_weight else 0.0

    @staticmethod
    def _rate(data: pd.DataFrame, condition) -> float:
        return condition(data).sum() / len(data) if len(data) else 0.0

    @staticmethod
    def _batting_average(data: pd.DataFrame) -> float:
        at_bats = StatcastDataLoader._at_bats(data)
        return (
            at_bats['is_hit'].sum() / len(at_bats)
            if len(at_bats) else 0.0
        )

    @staticmethod
    def _at_bats(data: pd.DataFrame) -> pd.DataFrame:
        plate_appearances = StatcastDataLoader._pa_rows(data)
        non_at_bat_events = {
            'walk', 'intent_walk', 'hit_by_pitch', 'sac_fly', 'sac_bunt',
            'catcher_interf', 'intentional_walk',
        }
        return plate_appearances[
            ~plate_appearances['events'].isin(non_at_bat_events)
        ]

    @staticmethod
    def _shrink(value: float, prior: float, sample_size: int,
                prior_strength: int) -> float:
        weight = sample_size / (sample_size + prior_strength)
        return weight * value + (1 - weight) * prior

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
            exit_velocity = row.get('launch_speed', row.get('exit_velocity'))
            if pd.isna(row['launch_angle']) or pd.isna(exit_velocity):
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

            if pitcher_data.empty:
                return None

            windows = self._player_windows('pitcher', pitcher_id)
            pa_windows = {
                name: self._pa_rows(data) for name, data in windows.items()
            }
            pa_count = len(self._pa_rows(pitcher_data))
            pitch_count = len(pitcher_data)
            fastball_count = (pitcher_data['pitch_category'] == 'fastball').sum()
            fastball_pct = self._weighted_stat(
                windows,
                lambda data: self._rate(
                    data, lambda frame: frame['pitch_category'] == 'fastball'
                )
            )
            breaking_pct = self._weighted_stat(
                windows,
                lambda data: self._rate(
                    data, lambda frame: frame['pitch_category'] == 'breaking'
                )
            )
            fastball_velo = self._weighted_stat(
                windows,
                lambda data: data.loc[
                    data['pitch_category'] == 'fastball', 'release_speed'
                ].mean()
            )

            stats = {
                'pitcher_id': pitcher_id,
                'total_pa': pa_count,
                'fastball_pct': fastball_pct,
                'breaking_pct': breaking_pct,
                'changeup_pct': max(0.0, 1 - fastball_pct - breaking_pct),
                'fastball_avg_velo': fastball_velo,
                'whiff_rate': self._weighted_stat(windows, self._calculate_whiff_rate),
                'k_rate': self._weighted_stat(
                    pa_windows,
                    lambda data: self._rate(
                        data,
                        lambda frame: frame['events'].eq('strikeout')
                    )
                ),
                'bb_rate': self._weighted_stat(
                    pa_windows,
                    lambda data: self._rate(
                        data,
                        lambda frame: frame['events'].isin(
                            {'walk', 'intent_walk', 'intentional_walk'}
                        )
                    )
                ),
                'ba_against': self._weighted_stat(
                    pa_windows, self._batting_average
                ),
            }
            stats['fastball_pct'] = self._shrink(
                fastball_pct, 0.56, pitch_count, 100
            )
            stats['breaking_pct'] = self._shrink(
                breaking_pct, 0.25, pitch_count, 100
            )
            stats['changeup_pct'] = max(
                0.0, 1 - stats['fastball_pct'] - stats['breaking_pct']
            )
            stats['fastball_avg_velo'] = self._shrink(
                fastball_velo or 92.0, 92.0, int(fastball_count), 50
            )
            stats['whiff_rate'] = self._shrink(
                stats['whiff_rate'], 0.20, pitch_count, 100
            )
            stats['k_rate'] = self._shrink(stats['k_rate'], 0.22, pa_count, 50)
            stats['bb_rate'] = self._shrink(stats['bb_rate'], 0.08, pa_count, 50)
            stats['ba_against'] = self._shrink(
                stats['ba_against'], 0.27, len(self._at_bats(pitcher_data)), 50
            )
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

            if batter_data.empty:
                return None

            windows = self._player_windows('batter', batter_id)
            pa_windows = {
                name: self._pa_rows(data) for name, data in windows.items()
            }
            stats = {
                'batter_id': batter_id,
                'total_pa': len(self._pa_rows(batter_data)),
                'ba': self._weighted_stat(pa_windows, self._batting_average),
                'k_rate': self._weighted_stat(
                    pa_windows,
                    lambda data: self._rate(
                        data, lambda frame: frame['events'].eq('strikeout')
                    )
                ),
                'bb_rate': self._weighted_stat(
                    pa_windows,
                    lambda data: self._rate(
                        data,
                        lambda frame: frame['events'].isin(
                            {'walk', 'intent_walk', 'intentional_walk'}
                        )
                    )
                ),
                'contact_rate': self._weighted_stat(windows, self._calculate_contact_rate),
                'whiff_rate': self._weighted_stat(windows, self._calculate_whiff_rate),
                'chase_rate': self._weighted_stat(windows, self._calculate_chase_rate),
                'gb_rate': self._weighted_stat(
                    windows,
                    lambda data: self._contact_type_rate(data, 'ground_ball')
                ),
                'ld_rate': self._weighted_stat(
                    windows,
                    lambda data: self._contact_type_rate(data, 'line_drive')
                ),
                'fb_rate': self._weighted_stat(
                    windows,
                    lambda data: self._contact_type_rate(data, 'fly_ball')
                ),
            }
            pa_count = len(self._pa_rows(batter_data))
            at_bat_count = len(self._at_bats(batter_data))
            descriptions = batter_data['description'].fillna('').astype(str)
            swing_count = int(descriptions.str.contains(
                'swinging_strike|missed_bunt|foul|hit_into_play|in_play|foul_tip',
                na=False,
            ).sum())
            batted_ball_count = int(batter_data['contact_type'].isin(
                {'ground_ball', 'line_drive', 'fly_ball'}
            ).sum())
            stats['ba'] = self._shrink(stats['ba'], 0.27, at_bat_count, 50)
            stats['k_rate'] = self._shrink(stats['k_rate'], 0.22, pa_count, 50)
            stats['bb_rate'] = self._shrink(stats['bb_rate'], 0.08, pa_count, 50)
            stats['contact_rate'] = self._shrink(
                stats['contact_rate'], 0.75, swing_count, 75
            )
            stats['whiff_rate'] = self._shrink(
                stats['whiff_rate'], 0.20, swing_count, 75
            )
            stats['chase_rate'] = self._shrink(
                stats['chase_rate'], 0.30, len(batter_data), 75
            )
            stats['gb_rate'] = self._shrink(
                stats['gb_rate'], 0.45, batted_ball_count, 50
            )
            stats['ld_rate'] = self._shrink(
                stats['ld_rate'], 0.20, batted_ball_count, 50
            )
            stats['fb_rate'] = self._shrink(
                stats['fb_rate'], 0.35, batted_ball_count, 50
            )
            self.batter_stats[batter_id] = stats
            return stats
        except Exception as e:
            logger.warning(f"Error getting batter stats for {batter_id}: {e}")
            return None

    def get_matchup_history(self, pitcher_id: int, batter_id: int) -> Dict:
        """Get direct history between pitcher and batter."""
        try:
            matchup_pitches = self.statcast_df[
                (self.statcast_df['pitcher'] == pitcher_id) &
                (self.statcast_df['batter'] == batter_id)
                ]
            matchup_data = self._pa_rows(matchup_pitches)

            if len(matchup_data) == 0:
                return {'pa_count': 0}

            return {
                'pa_count': len(matchup_data),
                'ba': self._batting_average(matchup_data),
                'k_rate': matchup_data['events'].eq('strikeout').mean(),
                'bb_rate': matchup_data['events'].isin(
                    {'walk', 'intent_walk', 'intentional_walk'}
                ).mean(),
            }
        except Exception as e:
            logger.warning(f"Error getting matchup history: {e}")
            return {'pa_count': 0}

    @staticmethod
    def _calculate_whiff_rate(data: pd.DataFrame) -> float:
        """Calculate misses per swing, rather than misses per pitch."""
        try:
            descriptions = data['description'].fillna('').astype(str)
            misses = descriptions.str.contains('swinging_strike|missed_bunt', na=False).sum()
            swings = descriptions.str.contains(
                'swinging_strike|missed_bunt|foul|hit_into_play|in_play', na=False
            ).sum()
            return misses / swings if swings else 0.20
        except:
            return 0.20

    @staticmethod
    def _calculate_contact_rate(data: pd.DataFrame) -> float:
        """Calculate non-miss contact per swing."""
        try:
            descriptions = data['description'].fillna('').astype(str)
            contact = descriptions.str.contains(
                'foul|hit_into_play|in_play|foul_tip', na=False
            ).sum()
            swings = descriptions.str.contains(
                'swinging_strike|missed_bunt|foul|hit_into_play|in_play|foul_tip',
                na=False,
            ).sum()
            return contact / swings if swings else 0.75
        except:
            return 0.75

    @staticmethod
    def _contact_type_rate(data: pd.DataFrame, contact_type: str) -> float:
        batted_balls = data[data['contact_type'].isin(
            {'ground_ball', 'line_drive', 'fly_ball'}
        )]
        return (
            (batted_balls['contact_type'] == contact_type).sum() / len(batted_balls)
            if len(batted_balls) else 0.0
        )

    @staticmethod
    def _calculate_chase_rate(data: pd.DataFrame) -> float:
        """Calculate swings at Statcast out-of-zone pitches."""
        try:
            zone = pd.to_numeric(data['zone'], errors='coerce')
            outside_zone = zone > 9
            pitches_outside_zone = outside_zone.sum()
            swings_outside = data.loc[outside_zone, 'description'].astype(str).str.contains(
                'swinging_strike|hit_into_play|foul|foul_tip|missed_bunt',
                na=False,
            ).sum()
            return swings_outside / pitches_outside_zone if pitches_outside_zone > 0 else 0.30
        except:
            return 0.30
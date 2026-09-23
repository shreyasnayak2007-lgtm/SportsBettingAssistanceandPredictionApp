# simulation/src/bvp_model.py

import pandas as pd
from typing import Dict, Tuple, Optional
import numpy as np
from data_loader import StatcastDataLoader
import config


class HierarchicalBvPModel:
    """
    Hierarchical Bayesian BvP (Batter vs Pitcher) model.

    Uses 4 tiers of data, weighted by sample size:
    1. Direct history (pitcher vs batter)
    2. Pitcher archetype vs batter
    3. Batter handedness vs pitcher handedness
    4. League average

    This avoids the small-sample problem in traditional BvP.
    """

    def __init__(self, data_loader: StatcastDataLoader):
        self.data_loader = data_loader
        self.pitcher_cache = {}
        self.batter_cache = {}
        self.archetype_cache = {}

    def predict_ba(self, pitcher_id: int, batter_id: int,
                   pitcher_hand: str = 'R', batter_hand: str = 'R') -> Dict:
        """
        Predict batting average for pitcher vs batter matchup.

        Returns dict with:
        - predicted_ba: The blended BA estimate
        - confidence: Weight given to direct history (0-1)
        - breakdown: How much each tier contributed
        """

        # Tier 1: Direct history (pitcher vs batter all-time)
        direct = self.data_loader.get_matchup_history(pitcher_id, batter_id)
        direct_pa = direct.get('pa_count', 0)
        direct_ba = direct.get('ba', config.LEAGUE_AVG_BA)

        # Tier 2: Pitcher archetype vs batter
        pitcher_stats = self.data_loader.get_pitcher_stats(pitcher_id)
        batter_stats = self.data_loader.get_batter_stats(batter_id)

        if pitcher_stats is None or batter_stats is None:
            # Fallback to league average if not enough data
            return {
                'predicted_ba': config.LEAGUE_AVG_BA,
                'confidence': 0.0,
                'breakdown': {
                    'direct': 0,
                    'archetype': 0,
                    'handedness': 0,
                    'league_avg': 1.0
                }
            }

        pitcher_archetype = self._classify_pitcher_archetype(pitcher_stats)
        archetype_ba = self._get_archetype_ba(pitcher_archetype, batter_id, batter_hand)
        archetype_pa = self._get_archetype_sample_size(pitcher_archetype, batter_id)

        # Tier 3: Handedness (RHH vs RHP, LHH vs LHP, etc.)
        handedness_key = f"{batter_hand}HH_vs_{pitcher_hand}HP"
        handedness_ba = self._get_handedness_ba(handedness_key, batter_id)
        handedness_pa = self._get_handedness_sample_size(handedness_key, batter_id)

        # Tier 4: League average
        league_ba = config.LEAGUE_AVG_BA

        # Calculate weights (Bayesian shrinkage)
        # More sample size = higher weight
        w1 = min(direct_pa / config.DIRECT_PA_THRESHOLD, 1.0)
        w2 = min(archetype_pa / config.ARCHETYPE_PA_THRESHOLD, 1.0)
        w3 = min(handedness_pa / config.HANDEDNESS_PA_THRESHOLD, 1.0)
        w_league = 0.3  # League average always has some baseline weight

        # Normalize weights
        total_weight = w1 + w2 + w3 + w_league
        w1_norm = w1 / total_weight
        w2_norm = w2 / total_weight
        w3_norm = w3 / total_weight
        w_league_norm = w_league / total_weight

        # Weighted blend
        predicted_ba = (
                w1_norm * direct_ba +
                w2_norm * archetype_ba +
                w3_norm * handedness_ba +
                w_league_norm * league_ba
        )

        # Confidence is how much weight direct history got
        confidence = w1_norm

        return {
            'predicted_ba': predicted_ba,
            'confidence': confidence,
            'breakdown': {
                'direct': w1_norm,
                'archetype': w2_norm,
                'handedness': w3_norm,
                'league_avg': w_league_norm
            },
            'details': {
                'direct_ba': direct_ba,
                'direct_pa': direct_pa,
                'archetype_ba': archetype_ba,
                'archetype_pa': archetype_pa,
                'handedness_ba': handedness_ba,
                'handedness_pa': handedness_pa,
                'pitcher_archetype': pitcher_archetype
            }
        }

    def predict_k_rate(self, pitcher_id: int, batter_id: int,
                       pitcher_hand: str = 'R', batter_hand: str = 'R') -> Dict:
        """
        Predict strikeout rate for pitcher vs batter matchup.
        Same hierarchical approach as predict_ba, but for K%.
        """

        # Tier 1: Direct history
        direct = self.data_loader.get_matchup_history(pitcher_id, batter_id)
        direct_pa = direct.get('pa_count', 0)
        direct_k_rate = direct.get('k_rate', 0.20)  # League avg K rate ~20%

        # Tier 2: Pitcher archetype vs batter
        pitcher_stats = self.data_loader.get_pitcher_stats(pitcher_id)
        batter_stats = self.data_loader.get_batter_stats(batter_id)

        if pitcher_stats is None or batter_stats is None:
            return {
                'predicted_k_rate': 0.20,
                'confidence': 0.0
            }

        pitcher_archetype = self._classify_pitcher_archetype(pitcher_stats)
        archetype_k_rate = self._get_archetype_k_rate(pitcher_archetype, batter_id, batter_hand)
        archetype_pa = self._get_archetype_sample_size(pitcher_archetype, batter_id)

        # Tier 3: Handedness
        handedness_key = f"{batter_hand}HH_vs_{pitcher_hand}HP"
        handedness_k_rate = self._get_handedness_k_rate(handedness_key, batter_id)
        handedness_pa = self._get_handedness_sample_size(handedness_key, batter_id)

        # Tier 4: League average (from pitcher stats)
        league_k_rate = pitcher_stats.get('k_rate', 0.20)

        # Calculate weights
        w1 = min(direct_pa / config.DIRECT_PA_THRESHOLD, 1.0)
        w2 = min(archetype_pa / config.ARCHETYPE_PA_THRESHOLD, 1.0)
        w3 = min(handedness_pa / config.HANDEDNESS_PA_THRESHOLD, 1.0)
        w_league = 0.3

        total_weight = w1 + w2 + w3 + w_league
        w1_norm = w1 / total_weight
        w2_norm = w2 / total_weight
        w3_norm = w3 / total_weight
        w_league_norm = w_league / total_weight

        predicted_k_rate = (
                w1_norm * direct_k_rate +
                w2_norm * archetype_k_rate +
                w3_norm * handedness_k_rate +
                w_league_norm * league_k_rate
        )

        confidence = w1_norm

        return {
            'predicted_k_rate': predicted_k_rate,
            'confidence': confidence,
            'breakdown': {
                'direct': w1_norm,
                'archetype': w2_norm,
                'handedness': w3_norm,
                'league_avg': w_league_norm
            }
        }

    def predict_bb_rate(self, pitcher_id: int, batter_id: int,
                        pitcher_hand: str = 'R', batter_hand: str = 'R') -> Dict:
        """
        Predict walk rate for pitcher vs batter matchup.
        """

        direct = self.data_loader.get_matchup_history(pitcher_id, batter_id)
        direct_pa = direct.get('pa_count', 0)
        direct_bb_rate = direct.get('bb_rate', 0.08)  # League avg ~8%

        pitcher_stats = self.data_loader.get_pitcher_stats(pitcher_id)
        batter_stats = self.data_loader.get_batter_stats(batter_id)

        if pitcher_stats is None or batter_stats is None:
            return {
                'predicted_bb_rate': 0.08,
                'confidence': 0.0
            }

        pitcher_archetype = self._classify_pitcher_archetype(pitcher_stats)
        archetype_bb_rate = self._get_archetype_bb_rate(pitcher_archetype, batter_id, batter_hand)
        archetype_pa = self._get_archetype_sample_size(pitcher_archetype, batter_id)

        handedness_key = f"{batter_hand}HH_vs_{pitcher_hand}HP"
        handedness_bb_rate = self._get_handedness_bb_rate(handedness_key, batter_id)
        handedness_pa = self._get_handedness_sample_size(handedness_key, batter_id)

        league_bb_rate = pitcher_stats.get('bb_rate', 0.08)

        w1 = min(direct_pa / config.DIRECT_PA_THRESHOLD, 1.0)
        w2 = min(archetype_pa / config.ARCHETYPE_PA_THRESHOLD, 1.0)
        w3 = min(handedness_pa / config.HANDEDNESS_PA_THRESHOLD, 1.0)
        w_league = 0.3

        total_weight = w1 + w2 + w3 + w_league
        w1_norm = w1 / total_weight
        w2_norm = w2 / total_weight
        w3_norm = w3 / total_weight
        w_league_norm = w_league / total_weight

        predicted_bb_rate = (
                w1_norm * direct_bb_rate +
                w2_norm * archetype_bb_rate +
                w3_norm * handedness_bb_rate +
                w_league_norm * league_bb_rate
        )

        confidence = w1_norm

        return {
            'predicted_bb_rate': predicted_bb_rate,
            'confidence': confidence,
            'breakdown': {
                'direct': w1_norm,
                'archetype': w2_norm,
                'handedness': w3_norm,
                'league_avg': w_league_norm
            }
        }

    def get_full_matchup_prediction(self, pitcher_id: int, batter_id: int,
                                    pitcher_hand: str = 'R', batter_hand: str = 'R') -> Dict:
        """
        Get all predictions (BA, K%, BB%) for a matchup in one call.
        Returns a comprehensive dict with all three outcomes.
        """

        ba_pred = self.predict_ba(pitcher_id, batter_id, pitcher_hand, batter_hand)
        k_pred = self.predict_k_rate(pitcher_id, batter_id, pitcher_hand, batter_hand)
        bb_pred = self.predict_bb_rate(pitcher_id, batter_id, pitcher_hand, batter_hand)

        # Calculate out rate (1 - BA - BB - K + some overlap)
        # Simplified: out_rate = 1 - (ba + k + bb) / 3 (rough approximation)
        predicted_ba = ba_pred['predicted_ba']
        predicted_k = k_pred['predicted_k_rate']
        predicted_bb = bb_pred['predicted_bb_rate']

        # Normalize so outcomes sum to 1
        predicted_out = max(0, 1 - predicted_ba - predicted_k - predicted_bb)

        # Re-normalize
        total = predicted_ba + predicted_k + predicted_bb + predicted_out
        predicted_ba_norm = predicted_ba / total if total > 0 else 0.25
        predicted_k_norm = predicted_k / total if total > 0 else 0.25
        predicted_bb_norm = predicted_bb / total if total > 0 else 0.25
        predicted_out_norm = predicted_out / total if total > 0 else 0.25

        return {
            'pitcher_id': pitcher_id,
            'batter_id': batter_id,
            'outcomes': {
                'hit': predicted_ba_norm,
                'strikeout': predicted_k_norm,
                'walk': predicted_bb_norm,
                'out': predicted_out_norm
            },
            'confidence': (ba_pred['confidence'] + k_pred['confidence'] + bb_pred['confidence']) / 3,
            'raw_predictions': {
                'ba': ba_pred,
                'k_rate': k_pred,
                'bb_rate': bb_pred
            }
        }

    # ==================== HELPER METHODS ====================

    def _classify_pitcher_archetype(self, pitcher_stats: Dict) -> str:
        """
        Classify pitcher into an archetype for better sample size pooling.

        Archetypes:
        - elite_heat: 96+ mph fastball, 60%+ fastball usage (Kershaw, deGrom)
        - high_velo_strikeout: 95+ mph fastball, 25%+ whiff rate
        - junk_ball: <78 mph breaking ball, <50% fastball
        - crafty_lh: <92 mph fastball (lefty soft toss)
        - balanced: everything else
        """

        fb_velo = pitcher_stats.get('fastball_avg_velo', 92)
        fb_pct = pitcher_stats.get('fastball_pct', 0.5)
        whiff = pitcher_stats.get('whiff_rate', 0.20)

        if fb_velo >= config.ELITE_HEAT_FASTBALL_VELO and fb_pct >= config.ELITE_HEAT_FASTBALL_PCT:
            return 'elite_heat'
        elif fb_velo >= config.HIGH_VELO_STRIKEOUT_VELO and whiff >= config.HIGH_VELO_STRIKEOUT_WHIFF:
            return 'high_velo_strikeout'
        elif fb_velo < config.CRAFTY_LH_FASTBALL_VELO:
            return 'crafty_lh'
        elif fb_pct <= config.JUNK_BALL_FASTBALL_PCT:
            return 'junk_ball'
        else:
            return 'balanced'

    def _get_archetype_ba(self, archetype: str, batter_id: int, batter_hand: str) -> float:
        """
        Get BA for a batter against a specific pitcher archetype.
        This pools all pitchers of that archetype vs this batter.
        """
        # Filter Statcast data for pitchers of this archetype
        archetype_pitchers = self._get_pitchers_by_archetype(archetype)

        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['pitcher'].isin(archetype_pitchers)) &
            (self.data_loader.statcast_df['batter'] == batter_id)
            ]

        if len(batter_data) == 0:
            # Fallback to handedness-based average
            return config.LEAGUE_AVG_BA

        return batter_data['is_hit'].sum() / len(batter_data)

    def _get_archetype_k_rate(self, archetype: str, batter_id: int, batter_hand: str) -> float:
        """Get K rate for batter vs pitcher archetype."""
        archetype_pitchers = self._get_pitchers_by_archetype(archetype)

        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['pitcher'].isin(archetype_pitchers)) &
            (self.data_loader.statcast_df['batter'] == batter_id)
            ]

        if len(batter_data) == 0:
            return 0.20  # Default K rate

        return (batter_data['events'].str.contains('strikeout', na=False)).sum() / len(batter_data)

    def _get_archetype_bb_rate(self, archetype: str, batter_id: int, batter_hand: str) -> float:
        """Get BB rate for batter vs pitcher archetype."""
        archetype_pitchers = self._get_pitchers_by_archetype(archetype)

        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['pitcher'].isin(archetype_pitchers)) &
            (self.data_loader.statcast_df['batter'] == batter_id)
            ]

        if len(batter_data) == 0:
            return 0.08  # Default BB rate

        return (batter_data['events'].str.contains('walk', na=False)).sum() / len(batter_data)

    def _get_archetype_sample_size(self, archetype: str, batter_id: int) -> int:
        """Get number of PA for a batter vs pitcher archetype."""
        archetype_pitchers = self._get_pitchers_by_archetype(archetype)

        return len(self.data_loader.statcast_df[
                       (self.data_loader.statcast_df['pitcher'].isin(archetype_pitchers)) &
                       (self.data_loader.statcast_df['batter'] == batter_id)
                       ])

    def _get_handedness_ba(self, handedness_key: str, batter_id: int) -> float:
        """Get BA for batter vs handedness matchup."""
        # E.g., 'RHH_vs_RHP' = right-handed batter vs right-handed pitcher
        batter_hand, pitcher_hand = handedness_key.split('_vs_')

        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['batter'] == batter_id)
        ]

        if len(batter_data) == 0:
            return config.LEAGUE_AVG_BA

        return batter_data['is_hit'].sum() / len(batter_data)

    def _get_handedness_k_rate(self, handedness_key: str, batter_id: int) -> float:
        """Get K rate for batter vs handedness."""
        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['batter'] == batter_id)
        ]

        if len(batter_data) == 0:
            return 0.20

        return (batter_data['events'].str.contains('strikeout', na=False)).sum() / len(batter_data)

    def _get_handedness_bb_rate(self, handedness_key: str, batter_id: int) -> float:
        """Get BB rate for batter vs handedness."""
        batter_data = self.data_loader.statcast_df[
            (self.data_loader.statcast_df['batter'] == batter_id)
        ]

        if len(batter_data) == 0:
            return 0.08

        return (batter_data['events'].str.contains('walk', na=False)).sum() / len(batter_data)

    def _get_handedness_sample_size(self, handedness_key: str, batter_id: int) -> int:
        """Get number of PA for batter vs handedness."""
        return len(self.data_loader.statcast_df[
                       (self.data_loader.statcast_df['batter'] == batter_id)
                   ])

    def _get_pitchers_by_archetype(self, archetype: str) -> list:
        """Get list of pitcher IDs that match this archetype."""
        if archetype not in self.archetype_cache:
            # Classify all pitchers
            pitcher_ids = self.data_loader.statcast_df['pitcher'].unique()
            matching_pitchers = []

            for pitcher_id in pitcher_ids:
                stats = self.data_loader.get_pitcher_stats(pitcher_id)
                if stats and self._classify_pitcher_archetype(stats) == archetype:
                    matching_pitchers.append(pitcher_id)

            self.archetype_cache[archetype] = matching_pitchers

        return self.archetype_cache[archetype]
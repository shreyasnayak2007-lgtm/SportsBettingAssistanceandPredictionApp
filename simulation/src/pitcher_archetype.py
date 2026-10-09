# simulation/src/pitcher_archetype.py

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import src.config as config


class PitcherArchetype:
    """
    Classify pitchers into archetypes based on pitch mix, velocity, and movement.

    This allows us to pool similar pitchers together for better sample sizes in BvP predictions.

    Archetypes:
    - elite_heat: 96+ mph fastball, 60%+ usage (Kershaw, deGrom, Scherzer)
    - high_velo_strikeout: 95+ mph fastball, 25%+ whiff rate (Young heat-throwing arms)
    - junk_ball: <78 mph breaking, <50% fastball usage (Maddux-type crafty pitchers)
    - crafty_lh: <92 mph fastball (Lefty soft-toss specialists)
    - balanced: Everything else (standard pitcher)
    """

    def __init__(self):
        self.archetypes = {
            'elite_heat': {
                'description': 'Elite fastball pitcher',
                'fastball_velo_min': config.ELITE_HEAT_FASTBALL_VELO,
                'fastball_pct_min': config.ELITE_HEAT_FASTBALL_PCT,
                'whiff_rate_min': 0.20,
                'examples': ['Clayton Kershaw', 'Jacob deGrom', 'Max Scherzer']
            },
            'high_velo_strikeout': {
                'description': 'High velocity strikeout pitcher',
                'fastball_velo_min': config.HIGH_VELO_STRIKEOUT_VELO,
                'whiff_rate_min': config.HIGH_VELO_STRIKEOUT_WHIFF,
                'examples': ['Noah Syndergaard', 'Gerrit Cole', 'Lucas Giolito']
            },
            'junk_ball': {
                'description': 'Junk ball / crafty pitcher',
                'fastball_pct_max': config.JUNK_BALL_FASTBALL_PCT,
                'breaking_velo_max': 78,  # Low velo breaking balls
                'examples': ['Greg Maddux', 'Jamie Moyer', 'Tom Glavine']
            },
            'crafty_lh': {
                'description': 'Crafty lefty soft-tosser',
                'fastball_velo_max': config.CRAFTY_LH_FASTBALL_VELO,
                'pitcher_hand': 'L',
                'examples': ['Clayton Kershaw (young)', 'David Price', 'CC Sabathia']
            },
            'balanced': {
                'description': 'Balanced / standard pitcher',
                'examples': ['Most pitchers']
            }
        }

    def classify(self, pitcher_stats: Dict) -> str:
        """
        Classify a pitcher into an archetype.

        Args:
            pitcher_stats: Dict with keys like 'fastball_avg_velo', 'fastball_pct', 'whiff_rate'

        Returns:
            archetype_name: One of ['elite_heat', 'high_velo_strikeout', 'junk_ball', 'crafty_lh', 'balanced']
        """

        fb_velo = pitcher_stats.get('fastball_avg_velo', 92)
        fb_pct = pitcher_stats.get('fastball_pct', 0.5)
        breaking_velo = pitcher_stats.get('breaking_avg_velo', 80)
        whiff = pitcher_stats.get('whiff_rate', 0.20)
        pitcher_hand = pitcher_stats.get('pitcher_hand', 'R')

        # Order matters: Check most specific archetypes first

        # 1. Elite heat: High velo + high fastball usage
        if (fb_velo >= config.ELITE_HEAT_FASTBALL_VELO and
                fb_pct >= config.ELITE_HEAT_FASTBALL_PCT and
                whiff >= 0.20):
            return 'elite_heat'

        # 2. High velo strikeout: High velo + high whiff
        elif (fb_velo >= config.HIGH_VELO_STRIKEOUT_VELO and
              whiff >= config.HIGH_VELO_STRIKEOUT_WHIFF):
            return 'high_velo_strikeout'

        # 3. Junk ball: Low fastball usage + low breaking velo
        elif (fb_pct <= config.JUNK_BALL_FASTBALL_PCT and
              breaking_velo <= 78):
            return 'junk_ball'

        # 4. Crafty LH: Low fastball velo (and probably lefty)
        elif fb_velo < config.CRAFTY_LH_FASTBALL_VELO:
            return 'crafty_lh'

        # 5. Default: Balanced
        else:
            return 'balanced'

    def get_archetype_description(self, archetype: str) -> Dict:
        """Get metadata about an archetype."""
        return self.archetypes.get(archetype, {})

    def explain_classification(self, pitcher_stats: Dict) -> Dict:
        """
        Explain why a pitcher was classified into an archetype.
        Useful for debugging and understanding the model.
        """

        fb_velo = pitcher_stats.get('fastball_avg_velo', 92)
        fb_pct = pitcher_stats.get('fastball_pct', 0.5)
        breaking_velo = pitcher_stats.get('breaking_avg_velo', 80)
        whiff = pitcher_stats.get('whiff_rate', 0.20)

        archetype = self.classify(pitcher_stats)

        explanation = {
            'archetype': archetype,
            'pitcher_name': pitcher_stats.get('pitcher_name', 'Unknown'),
            'stats': {
                'fastball_avg_velo': fb_velo,
                'fastball_pct': f"{fb_pct:.1%}",
                'breaking_avg_velo': breaking_velo,
                'whiff_rate': f"{whiff:.1%}",
            },
            'thresholds_checked': {}
        }

        # Explain which thresholds were checked
        explanation['thresholds_checked']['elite_heat'] = {
            'fastball_velo_96+': fb_velo >= config.ELITE_HEAT_FASTBALL_VELO,
            'fastball_60%+': fb_pct >= config.ELITE_HEAT_FASTBALL_PCT,
            'whiff_20%+': whiff >= 0.20,
            'result': 'MATCH' if archetype == 'elite_heat' else 'no'
        }

        explanation['thresholds_checked']['high_velo_strikeout'] = {
            'fastball_velo_95+': fb_velo >= config.HIGH_VELO_STRIKEOUT_VELO,
            'whiff_25%+': whiff >= config.HIGH_VELO_STRIKEOUT_WHIFF,
            'result': 'MATCH' if archetype == 'high_velo_strikeout' else 'no'
        }

        explanation['thresholds_checked']['junk_ball'] = {
            'fastball_50%-or-less': fb_pct <= config.JUNK_BALL_FASTBALL_PCT,
            'breaking_velo_78-or-less': breaking_velo <= 78,
            'result': 'MATCH' if archetype == 'junk_ball' else 'no'
        }

        explanation['thresholds_checked']['crafty_lh'] = {
            'fastball_velo_under_92': fb_velo < config.CRAFTY_LH_FASTBALL_VELO,
            'result': 'MATCH' if archetype == 'crafty_lh' else 'no'
        }

        return explanation


class ArchetypePool:
    """
    Manage pooling of pitchers by archetype for sample size aggregation.

    Used by HierarchicalBvPModel to get all pitchers of a specific archetype.
    """

    def __init__(self, statcast_df: pd.DataFrame):
        """
        Args:
            statcast_df: Full Statcast dataframe with all pitches
        """
        self.statcast_df = statcast_df
        self.archetype_classifier = PitcherArchetype()
        self.pitcher_archetype_cache = {}  # pitcher_id -> archetype
        self.archetype_pitcher_cache = {}  # archetype -> [pitcher_ids]

    def get_pitcher_archetype(self, pitcher_id: int, pitcher_stats: Dict) -> str:
        """Get cached archetype for a pitcher, or classify if not in cache."""

        if pitcher_id not in self.pitcher_archetype_cache:
            archetype = self.archetype_classifier.classify(pitcher_stats)
            self.pitcher_archetype_cache[pitcher_id] = archetype

        return self.pitcher_archetype_cache[pitcher_id]

    def get_pitchers_by_archetype(self, archetype: str,
                                  pitcher_stats_dict: Dict[int, Dict]) -> List[int]:
        """
        Get all pitcher IDs that belong to a specific archetype.

        Args:
            archetype: Name of archetype (e.g., 'elite_heat')
            pitcher_stats_dict: Dict mapping pitcher_id -> pitcher_stats

        Returns:
            List of pitcher IDs in this archetype
        """

        if archetype not in self.archetype_pitcher_cache:
            matching_pitchers = []

            for pitcher_id, stats in pitcher_stats_dict.items():
                classified_archetype = self.archetype_classifier.classify(stats)
                if classified_archetype == archetype:
                    matching_pitchers.append(pitcher_id)

            self.archetype_pitcher_cache[archetype] = matching_pitchers

        return self.archetype_pitcher_cache[archetype]

    def get_archetype_stats(self, archetype: str, pitcher_ids: List[int]) -> Dict:
        """
        Get aggregated stats for all pitchers in an archetype.

        Returns:
            Dict with average velocity, whiff rate, K rate, etc. for the archetype
        """

        archetype_data = self.statcast_df[
            self.statcast_df['pitcher'].isin(pitcher_ids)
        ]

        if len(archetype_data) == 0:
            return {}

        # Calculate aggregated stats
        fastballs = archetype_data[archetype_data['pitch_category'] == 'fastball']
        breaking = archetype_data[archetype_data['pitch_category'] == 'breaking']

        return {
            'archetype': archetype,
            'pitcher_count': len(pitcher_ids),
            'total_pitches': len(archetype_data),
            'avg_fastball_velo': fastballs['release_speed'].mean() if len(fastballs) > 0 else 0,
            'avg_breaking_velo': breaking['release_speed'].mean() if len(breaking) > 0 else 0,
            'fastball_pct': len(fastballs) / len(archetype_data) if len(archetype_data) > 0 else 0,
            'breaking_pct': len(breaking) / len(archetype_data) if len(archetype_data) > 0 else 0,
            'avg_whiff_rate': (archetype_data['description'].str.contains('swinging_strike', na=False).sum() /
                               len(archetype_data) if len(archetype_data) > 0 else 0),
            'k_rate': (archetype_data['events'].str.contains('strikeout', na=False).sum() /
                       len(archetype_data) if len(archetype_data) > 0 else 0),
            'bb_rate': (archetype_data['events'].str.contains('walk', na=False).sum() /
                        len(archetype_data) if len(archetype_data) > 0 else 0),
        }

    def get_batter_vs_archetype_stats(self, batter_id: int, archetype: str,
                                      pitcher_ids: List[int]) -> Dict:
        """
        Get performance stats for a specific batter vs all pitchers in an archetype.

        Returns:
            Dict with BA, K%, BB%, sample size for batter vs this archetype
        """

        batter_data = self.statcast_df[
            (self.statcast_df['batter'] == batter_id) &
            (self.statcast_df['pitcher'].isin(pitcher_ids))
            ]

        if len(batter_data) == 0:
            return {
                'archetype': archetype,
                'batter_id': batter_id,
                'pa_count': 0,
                'ba': config.LEAGUE_AVG_BA,
                'k_rate': 0.20,
                'bb_rate': 0.08,
            }

        return {
            'archetype': archetype,
            'batter_id': batter_id,
            'pa_count': len(batter_data),
            'ba': batter_data['is_hit'].sum() / len(batter_data),
            'k_rate': (batter_data['events'].str.contains('strikeout', na=False).sum() /
                       len(batter_data)),
            'bb_rate': (batter_data['events'].str.contains('walk', na=False).sum() /
                        len(batter_data)),
            'contact_type_dist': {
                'ground_ball': (batter_data['contact_type'] == 'ground_ball').sum() / len(batter_data),
                'line_drive': (batter_data['contact_type'] == 'line_drive').sum() / len(batter_data),
                'fly_ball': (batter_data['contact_type'] == 'fly_ball').sum() / len(batter_data),
            }
        }


class ArchetypeComparison:
    """
    Compare archetypes to understand strengths/weaknesses.
    Useful for analysis and validation.
    """

    def __init__(self, archetype_pool: ArchetypePool):
        self.archetype_pool = archetype_pool

    def compare_all_archetypes(self) -> Dict:
        """
        Get stats for all archetypes in the dataset.

        Returns:
            Dict mapping archetype -> stats
        """

        archetypes = ['elite_heat', 'high_velo_strikeout', 'junk_ball', 'crafty_lh', 'balanced']
        comparison = {}

        for archetype in archetypes:
            pitcher_ids = list(self.archetype_pool.pitcher_archetype_cache.keys())
            pitchers_in_archetype = [
                pid for pid in pitcher_ids
                if self.archetype_pool.pitcher_archetype_cache[pid] == archetype
            ]

            if len(pitchers_in_archetype) > 0:
                comparison[archetype] = self.archetype_pool.get_archetype_stats(
                    archetype, pitchers_in_archetype
                )

        return comparison

    def explain_batter_vs_archetypes(self, batter_id: int) -> Dict:
        """
        Show how a specific batter performs against each archetype.

        Returns:
            Dict mapping archetype -> batter's performance stats
        """

        archetypes = ['elite_heat', 'high_velo_strikeout', 'junk_ball', 'crafty_lh', 'balanced']
        performance = {}

        for archetype in archetypes:
            pitcher_ids = list(self.archetype_pool.pitcher_archetype_cache.keys())
            pitchers_in_archetype = [
                pid for pid in pitcher_ids
                if self.archetype_pool.pitcher_archetype_cache[pid] == archetype
            ]

            if len(pitchers_in_archetype) > 0:
                performance[archetype] = self.archetype_pool.get_batter_vs_archetype_stats(
                    batter_id, archetype, pitchers_in_archetype
                )

        return performance
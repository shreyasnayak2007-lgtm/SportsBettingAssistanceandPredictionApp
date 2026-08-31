// Shared typescript interfaces
export type PitcherHand = 'RHP' | 'LHP';

export interface GameSummary {
  game_id: string;
  game_time_utc: string;
  venue_name: string;
  away_team: { name: string; abbreviation: string; logo_url: string };
  home_team: { name: string; abbreviation: string; logo_url: string };
  probable_starters: {
    away: { id: number; name: string; hand: PitcherHand };
    home: { id: number; name: string; hand: PitcherHand };
  };
}

export interface StatBadge {
  id: 'vs_handedness' | 'l20_streak' | 'ballpark' | 'bv_advantage';
  label: string;
  type: 'fire' | 'streak' | 'park' | 'target';
  description: string;
}

export interface BatterMatchup {
  player_id: number;
  name: string;
  position: string;
  bat_side: 'L' | 'R' | 'S';
  bvp_stats: {
    plate_appearances: number;
    at_bats: number;
    avg: number;
    ops: number;
    home_runs: number;
    strikeouts: number;
    walk_pct: number;
  };
  current_season_splits: {
    vs_rhp_ops: number;
    vs_lhp_ops: number;
  };
  rolling_20: {
    avg: number;
    slugging: number;
    hard_hit_pct: number;
    home_runs: number;
    hits_last_20: number; // For L20 Hot Streak evaluation
  };
  badges: StatBadge[];
}

export interface MatchupDetailResponse {
  game_id: string;
  park_factors: {
    venue: string;
    hr_factor_lhh: number;
    hr_factor_rhh: number;
  };
  matchups: {
    away_lineup: BatterMatchup[];
    home_lineup: BatterMatchup[];
  };
}
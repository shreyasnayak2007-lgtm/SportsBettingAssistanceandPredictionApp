export interface DetailGame {
  id: number
  gamePk: number
  gameDate: string
  season: number
  gameDatetime: string | null
  time: string
  status: 'live' | 'upcoming' | 'final'
  statusLabel: string
  inning?: number
  inningState?: string | null
  outs?: number | null
  runners: {
    first: boolean
    second: boolean
    third: boolean
  }
  awayTeam: string
  awayTeamName: string
  awayTeamId: number
  awayMlbTeamId: number
  awayLeague: string | null
  awayDivision: string | null
  awayScore: number
  homeTeam: string
  homeTeamName: string
  homeTeamId: number
  homeMlbTeamId: number
  homeLeague: string | null
  homeDivision: string | null
  homeScore: number
  odds?: {
    spread?: string
  }
  source: 'real'
  stats: {
    pitches: number
    strikeouts: number
    walks: number
    ballsInPlay: number
    source: 'real' | 'mock' | 'unavailable'
    sample: Record<string, unknown>[]
  }
}

export function mapBackendGamesList(data: any[]): DetailGame[] {
  if (!Array.isArray(data)) return []

  return data.map((game) => {
    const rawStatus = (game.status || '').toLowerCase()
    const statusLabel = String(game.status || 'Unknown')
    let status: 'live' | 'upcoming' | 'final' = 'upcoming'

    if (rawStatus.includes('in progress') || rawStatus === 'live') {
      status = 'live'
    } else if (rawStatus.includes('final') || rawStatus.includes('completed')) {
      status = 'final'
    }

    return {
      id: Number(game.id ?? 0),
      gamePk: Number(game.game_pk ?? 0),
      gameDate: String(game.game_date ?? ''),
      season: Number(game.season ?? 0),
      gameDatetime: game.game_datetime ?? null,
      time: game.game_datetime || game.game_date || new Date().toISOString(),
      status,
      statusLabel,
      inning: game.current_inning ?? undefined,
      inningState: game.inning_state ?? null,
      outs: game.outs ?? null,
      runners: {
        first: Boolean(game.runner_on_first),
        second: Boolean(game.runner_on_second),
        third: Boolean(game.runner_on_third),
      },
      awayTeam: game.away_team?.abbreviation || game.away_team?.name || 'AWAY',
      awayTeamName: game.away_team?.name || game.away_team?.abbreviation || 'Away team',
      awayTeamId: Number(game.away_team?.id ?? 0),
      awayMlbTeamId: Number(game.away_team?.mlb_team_id ?? 0),
      awayLeague: game.away_team?.league ?? null,
      awayDivision: game.away_team?.division ?? null,
      awayScore: Number(game.away_team?.score ?? 0),
      homeTeam: game.home_team?.abbreviation || game.home_team?.name || 'HOME',
      homeTeamName: game.home_team?.name || game.home_team?.abbreviation || 'Home team',
      homeTeamId: Number(game.home_team?.id ?? 0),
      homeMlbTeamId: Number(game.home_team?.mlb_team_id ?? 0),
      homeLeague: game.home_team?.league ?? null,
      homeDivision: game.home_team?.division ?? null,
      homeScore: Number(game.home_team?.score ?? 0),
      odds: {
        spread: 'N/A',
      },
      source: 'real' as const,
      stats: {
        pitches: 0,
        strikeouts: 0,
        walks: 0,
        ballsInPlay: 0,
        source: 'real' as const,
        sample: [],
      },
    }
  })
}
export interface DetailGame {
  id: number
  gamePk: number
  time: string
  status: 'live' | 'upcoming' | 'final'
  inning?: number
  awayTeam: string
  awayScore: number
  homeTeam: string
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
    let status: 'live' | 'upcoming' | 'final' = 'upcoming'

    if (rawStatus.includes('in progress') || rawStatus === 'live') {
      status = 'live'
    } else if (rawStatus.includes('final') || rawStatus.includes('completed')) {
      status = 'final'
    }

    return {
      id: Number(game.id ?? 0),
      gamePk: Number(game.game_pk ?? 0),
      time: game.game_datetime || game.game_date || new Date().toISOString(),
      status,
      inning: game.current_inning ?? undefined,
      awayTeam: game.away_team?.abbreviation || game.away_team?.name || 'AWAY',
      awayScore: Number(game.away_team?.score ?? 0),
      homeTeam: game.home_team?.abbreviation || game.home_team?.name || 'HOME',
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
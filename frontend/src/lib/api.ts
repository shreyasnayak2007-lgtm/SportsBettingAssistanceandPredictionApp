import type { Game } from './mock-data'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? ''

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message)
    this.name = 'ApiError'
  }
}

function toGame(payload: Record<string, unknown>): Game | null {
  const home = (payload.homeTeam ?? payload.home_team) as Record<string, unknown> | string | undefined
  const away = (payload.awayTeam ?? payload.away_team) as Record<string, unknown> | string | undefined
  const homeTeam = typeof home === 'object' ? String(home.abbreviation ?? home.name ?? '') : String(home ?? '')
  const awayTeam = typeof away === 'object' ? String(away.abbreviation ?? away.name ?? '') : String(away ?? '')
  if (!homeTeam || !awayTeam) return null

  const odds = (payload.odds ?? {}) as Record<string, unknown>
  return {
    id: String(payload.id ?? `${awayTeam}-${homeTeam}`),
    homeTeam,
    awayTeam,
    homeTeamLogo: String(payload.homeTeamLogo ?? payload.home_team_logo ?? (typeof home === 'object' ? home.id ?? homeTeam : homeTeam)),
    awayTeamLogo: String(payload.awayTeamLogo ?? payload.away_team_logo ?? (typeof away === 'object' ? away.id ?? awayTeam : awayTeam)),
    status: String(payload.status ?? 'upcoming').toLowerCase().includes('live') ? 'live' : String(payload.status ?? '').toLowerCase().includes('final') ? 'final' : 'upcoming',
    inning: typeof payload.inning === 'number' ? payload.inning : undefined,
    homeScore: Number(payload.homeScore ?? payload.home_score ?? 0),
    awayScore: Number(payload.awayScore ?? payload.away_score ?? 0),
    time: String(payload.time ?? payload.game_time ?? payload.start_time ?? 'Today'),
    odds: {
      spread: String(payload.spread ?? odds.spread ?? 'Unavailable'),
      overUnder: String(payload.overUnder ?? payload.over_under ?? odds.overUnder ?? 'Unavailable'),
      moneyline: String(payload.moneyline ?? odds.moneyline ?? 'Unavailable'),
    },
  }
}

export async function fetchTodayGames(): Promise<Game[]> {
  const endpoint = `${API_BASE_URL}/api/v1/games/today`
  const response = await fetch(endpoint, { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new ApiError(`Games API returned ${response.status}`, response.status)

  const payload = await response.json()
  const records = Array.isArray(payload) ? payload : payload.data ?? payload.games
  if (!Array.isArray(records)) throw new ApiError('Games API returned an unexpected response')
  return records.map(toGame).filter((game): game is Game => game !== null)
}

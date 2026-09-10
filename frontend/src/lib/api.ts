const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? (typeof window === 'undefined' ? 'http://localhost:8000' : '')

export type LiveGame = {
  gamePk: number
  awayTeam: string
  homeTeam: string
  awayTeamLogo?: string
  homeTeamLogo?: string
  status: 'upcoming' | 'live' | 'final'
  inning?: number
  awayScore: number
  homeScore: number
  time: string
  source: 'real'
  stats: {
    pitches: number
    strikeouts: number
    walks: number
    ballsInPlay: number
    source: 'real' | 'mock' | 'unavailable'
    sample: Array<Record<string, unknown>>
  }
}

export class ApiError extends Error {}

function formatGameTime(value: unknown): string {
  const parsed = new Date(String(value ?? ''))
  if (Number.isNaN(parsed.getTime())) return 'Time unavailable'
  return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }).format(parsed)
}

export async function fetchTodayGames(): Promise<LiveGame[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/games/today`, { cache: 'no-store' })
  if (!response.ok) throw new ApiError(`Games API returned ${response.status}`)
  const payload = await response.json()
  const records = Array.isArray(payload) ? payload : payload.data ?? payload.games
  if (!Array.isArray(records)) throw new ApiError('Games API returned an unexpected response')
  return records.map((record) => ({ ...record, time: formatGameTime(record.time), source: 'real' as const, stats: { pitches: 0, strikeouts: 0, walks: 0, ballsInPlay: 0, source: 'unavailable' as const, sample: [], ...record.stats } }))
}

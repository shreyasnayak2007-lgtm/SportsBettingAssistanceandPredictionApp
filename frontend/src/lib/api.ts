// frontend/src/lib/api.ts
/**
 * API client for MLB Stats Platform backend
 * Handles all HTTP requests to the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

// ============================================================
// GAME DATA TYPES
// ============================================================

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

// ============================================================
// MATCHUP DATA TYPES
// ============================================================

export type Badge = {
  type: 'hot_streak' | 'handedness' | 'ballpark' | 'bvp_advantage'
  strength: 'strong' | 'moderate' | 'weak'
  value: string
  tooltip: string
}

export type BvPStats = {
  careerAB: number
  careerH: number
  careerAVG: number
  careerSLG: number
  careerOBP: number
  vsRHP: Record<string, number>
  vsLHP: Record<string, number>
}

export type RollingMetric = {
  gameDate: string
  result: 'W' | 'L'
  hits: number
  runs: number
  rbi: number
  avg: number
  hardHitRate: number
}

export type BatterDetail = {
  mlbamId: number
  name: string
  position: string
  handedness: 'L' | 'R' | 'S'
  jerseyNumber: number
  bvpStats: BvPStats
  rollingTrends: RollingMetric[]
  badges: Badge[]
}

export type PitcherInfo = {
  mlbamId: number
  name: string
  position: string
  handedness: 'L' | 'R'
  jerseyNumber: number
  season_era: number
  last_7_days_performance: Record<string, unknown>
}

export type Matchup = {
  gamePk: number
  gameDate: string
  awayTeam: string
  homeTeam: string
  ballparkName: string
  ballparkFactor: number
  homePitcher: PitcherInfo | null
  awayPitcher: PitcherInfo | null
  awayLineup: BatterDetail[]
  homeLineup: BatterDetail[]
}

// ============================================================
// ERROR HANDLING
// ============================================================

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message)
    this.name = 'ApiError'
  }
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

function formatGameTime(value: unknown): string {
  const parsed = new Date(String(value ?? ''))
  if (Number.isNaN(parsed.getTime())) return 'Time unavailable'
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(parsed)
}

// ============================================================
// API FUNCTIONS
// ============================================================

/**
 * Fetch today's MLB games with real Statcast data
 *
 * @returns List of games playing today
 * @throws ApiError if backend is unavailable
 *
 * @example
 * const games = await fetchTodayGames()
 * games.forEach(game => {
 *   console.log(`${game.awayTeam} @ ${game.homeTeam}`)
 * })
 */
export async function fetchTodayGames(): Promise<LiveGame[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/games/today`,
    { cache: 'no-store' }
  )

  if (!response.ok) {
    throw new ApiError(
      `Games API returned ${response.status}`,
      response.status
    )
  }

  const payload = await response.json()

  // Handle different response formats
  const records = Array.isArray(payload)
    ? payload
    : payload.data ?? payload.games

  if (!Array.isArray(records)) {
    throw new ApiError('Games API returned an unexpected response')
  }

  // Transform and normalize response
  return records.map((record) => ({
    ...record,
    time: formatGameTime(record.time),
    source: 'real' as const,
    stats: {
      pitches: 0,
      strikeouts: 0,
      walks: 0,
      ballsInPlay: 0,
      source: 'unavailable' as const,
      sample: [],
      ...record.stats,
    },
  }))
}

/**
 * Fetch detailed matchup information for a specific game
 *
 * Includes:
 * - Complete home and away lineups
 * - BvP (batter vs pitcher) career statistics
 * - Rolling 20-game performance trends
 * - Performance badges (hot streak, handedness advantage, etc.)
 * - Ballpark factor
 *
 * @param gamePk - MLB game ID
 * @returns Matchup object with all detail data
 * @throws ApiError if game not found or backend error
 *
 * @example
 * const matchup = await fetchMatchupDetail(777278)
 * console.log(`${matchup.awayTeam} @ ${matchup.homeTeam}`)
 * console.log(`Ballpark: ${matchup.ballparkName}`)
 * matchup.homeLineup.forEach(batter => {
 *   console.log(`${batter.name}: .${batter.bvpStats.careerAVG}`)
 * })
 */
export async function fetchMatchupDetail(gamePk: number): Promise<Matchup> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/matchups/${gamePk}`,
    { cache: 'no-store' }
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiError(`Game ${gamePk} not found`, 404)
    }
    throw new ApiError(
      `Matchup API returned ${response.status}`,
      response.status
    )
  }

  const matchup = await response.json()

  // Validate response has required fields
  if (!matchup.gamePk || !matchup.awayLineup || !matchup.homeLineup) {
    throw new ApiError('Matchup API returned incomplete data')
  }

  return matchup
}

/**
 * Fetch Statcast pitch-by-pitch data for a specific game
 *
 * @param gamePk - MLB game ID
 * @returns List of individual pitches with detailed metrics
 * @throws ApiError if game not found or no Statcast data
 *
 * @example
 * const pitches = await fetchGameStatcast(777278)
 * console.log(`${pitches.length} pitches in game`)
 */
export async function fetchGameStatcast(
  gamePk: number
): Promise<Array<Record<string, unknown>>> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/statcast/games/${gamePk}`,
    { cache: 'no-store' }
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new ApiError(
        `No Statcast data found for game ${gamePk}`,
        404
      )
    }
    throw new ApiError(
      `Statcast API returned ${response.status}`,
      response.status
    )
  }

  return response.json()
}

// ============================================================
// PORTFOLIO/FAVORITES (Optional - for later)
// ============================================================

type PortfolioItem = {
  id: string
  gamePk: number
  batter: string
  prop: string
  odds: string
  addedAt: string
}

const PORTFOLIO_STORAGE_KEY = 'mlb-portfolio'

/**
 * Get user's saved prop selections from localStorage
 *
 * @returns Array of saved props
 */
export function getPortfolio(): PortfolioItem[] {
  if (typeof window === 'undefined') return []

  try {
    const stored = localStorage.getItem(PORTFOLIO_STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

/**
 * Save a prop to user's portfolio
 *
 * @param item - Prop to add
 */
export function addToPortfolio(item: PortfolioItem): void {
  if (typeof window === 'undefined') return

  try {
    const portfolio = getPortfolio()
    portfolio.push(item)
    localStorage.setItem(PORTFOLIO_STORAGE_KEY, JSON.stringify(portfolio))
  } catch (error) {
    console.error('Failed to save portfolio:', error)
  }
}

/**
 * Remove prop from portfolio
 *
 * @param id - ID of prop to remove
 */
export function removeFromPortfolio(id: string): void {
  if (typeof window === 'undefined') return

  try {
    const portfolio = getPortfolio().filter(item => item.id !== id)
    localStorage.setItem(PORTFOLIO_STORAGE_KEY, JSON.stringify(portfolio))
  } catch (error) {
    console.error('Failed to update portfolio:', error)
  }
}
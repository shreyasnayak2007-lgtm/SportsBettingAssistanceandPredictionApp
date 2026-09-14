'use client'

import { useEffect, useState } from 'react'
import { GameDetailView } from '@/components/dashboard/GameDetailView'
import {
  ArrowRight,
  BarChart3,
  Bot,
  CalendarDays,
  ChevronDown,
  Clock3,
  Info,
  Menu,
  Search,
  Sparkles,
  TrendingUp,
  X,
  Sun,
  Moon,
} from 'lucide-react'

const teamLogos: Record<string, { label: string; url: string }> = {
  CLE: { label: 'Cleveland Guardians', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/114.svg' },
  BAL: { label: 'Baltimore Orioles', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/110.svg' },
  MIN: { label: 'Minnesota Twins', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/142.svg' },
  DET: { label: 'Detroit Tigers', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/116.svg' },
  HOU: { label: 'Houston Astros', url: 'https://www.mlbstatic.com/team-logos/team-primary-on-light/117.svg' },
  PHI: { label: 'Philadelphia Phillies', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/143.svg' },
  NYM: { label: 'New York Mets', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/121.svg' },
  MIA: { label: 'Miami Marlins', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/146.svg' },
  LAA: { label: 'Los Angeles Angels', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/108.svg' },
  BOS: { label: 'Boston Red Sox', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/111.svg' },
  COL: { label: 'Colorado Rockies', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/115.svg' },
  NYY: { label: 'New York Yankees', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/147.svg' },
  TB: { label: 'Tampa Bay Rays', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/139.svg' },
  ATL: { label: 'Atlanta Braves', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/144.svg' },
  PIT: { label: 'Pittsburgh Pirates', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/134.svg' },
  CWS: { label: 'Chicago White Sox', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/145.svg' },
  ARI: { label: 'Arizona Diamondbacks', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/109.svg' },
  KC: { label: 'Kansas City Royals', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/118.svg' },
  LAD: { label: 'Los Angeles Dodgers', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/119.svg' },
  SD: { label: 'San Diego Padres', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/135.svg' },
  SF: { label: 'San Francisco Giants', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/137.svg' },
  WSH: { label: 'Washington Nationals', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/120.svg' },
  MIL: { label: 'Milwaukee Brewers', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/158.svg' },
  CIN: { label: 'Cincinnati Reds', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/113.svg' },
  STL: { label: 'St. Louis Cardinals', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/138.svg' },
  CHC: { label: 'Chicago Cubs', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/112.svg' },
  TEX: { label: 'Texas Rangers', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/140.svg' },
  OAK: { label: 'Oakland Athletics', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/133.svg' },
  SEA: { label: 'Seattle Mariners', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/136.svg' },
  TOR: { label: 'Toronto Blue Jays', url: 'https://www.mlbstatic.com/team-logos/team-cap-on-light/141.svg' },
}

function TeamLogo({ team, size = 'size-14' }: { team: string; size?: string }) {
  const logo = teamLogos[team]
  return logo ? (
    <img src={logo.url} alt={`${logo.label} logo`} className={`${size} object-contain drop-shadow-lg`} />
  ) : (
    <span aria-label={`${team} team logo`} className={`inline-flex ${size} items-center justify-center rounded-full bg-muted text-sm font-black text-foreground`}>
      {team.slice(0, 2)}
    </span>
  )
}

const popularBets = [
  { player: 'T. Hernández', matchup: 'vs CIN', bet: 'Over 0.5 Hits', odds: '-133', hitRate: '8 of last 8', percent: '100%', reason: 'Strong recent form' },
  { player: 'H. Wesneski', matchup: '@ PHI', bet: 'Over 3.5 Strikeouts', odds: '-110', hitRate: '7 of last 7', percent: '100%', reason: 'Favorable matchup' },
  { player: 'C. Burnes', matchup: '@ KC', bet: 'Over 2.5 Strikeouts', odds: '-125', hitRate: '18 of last 18', percent: '100%', reason: 'Consistent volume' },
]

function Market({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/40 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [detailGame, setDetailGame] = useState<any>(null)
  const [stake, setStake] = useState('100')
  const [odds, setOdds] = useState('-110')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isLightMode, setIsLightMode] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('Ask about today\'s matchups, trends, or how to read a market.')

  // Fetch real games on mount
  useEffect(() => {
  async function loadGames() {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/games/today`,
        { cache: 'no-store' }
      )
      const data = await response.json()
      setGames(data.data || [])
    } catch (err) {
      console.error('Failed to load games:', err)
    }
  }

  loadGames()

  // Refresh every 10 seconds
  const interval = setInterval(loadGames, 10000)
  return () => clearInterval(interval)
}, [])

  const todayLabel = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())
  const selectedGame: typeof games[number] | undefined = games.length > 0 ? games[0] : undefined

  const payout = Math.max(0, (Number(stake) || 0) * (Number(odds) > 0 ? Number(odds) / 100 : 100 / Math.abs(Number(odds)))).toFixed(2)

  function askAssistant() {
    if (!question.trim()) return
    setAnswer(`For ${question.trim()}, start with the matchup context, then compare the market price with the underlying trend. This is a mock analysis for now.`)
    setQuestion('')
  }

  if (detailGame) {
    return (
      <div className={`${isLightMode ? 'light' : 'dark'} min-h-screen bg-background text-foreground`}>
        <GameDetailView game={detailGame} teamLogos={teamLogos} onBack={() => setDetailGame(null)} />
      </div>
    )
  }

  return (
    <div className={`${isLightMode ? 'light' : 'dark'} min-h-screen bg-background text-foreground`}>
      <header className="sticky top-0 z-30 border-b border-border/80 bg-background backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-4 sm:px-6">
          <button className="md:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}>
            <Menu className="size-5" />
          </button>
          <div className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <span className="inline-flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">L</span>
            LineMate
            <span className="text-muted-foreground">/</span>
            <span className="text-sm font-medium text-muted-foreground">MLB</span>
            <ChevronDown className="size-4 text-muted-foreground" />
          </div>
          <nav className="hidden items-center gap-6 text-sm font-medium md:flex">
            <a className="text-foreground" href="#today">Today</a>
            <a className="text-muted-foreground hover:text-foreground" href="#trending">Trends</a>
            <a className="text-muted-foreground hover:text-foreground" href="#tools">Tools</a>
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <button className="hidden text-sm text-muted-foreground sm:block">Log in</button>
            <button
              aria-label={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'}
              onClick={() => setIsLightMode((value) => !value)}
              className="inline-flex size-9 items-center justify-center rounded-lg border border-border text-muted-foreground transition hover:bg-muted"
            >
              {isLightMode ? <Moon className="size-4" /> : <Sun className="size-4" />}
            </button>
            <button className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">Start free trial</button>
          </div>
        </div>
      </header>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-background p-6 md:hidden">
          <div className="flex items-center justify-between">
            <span className="font-bold">Navigation</span>
            <button onClick={() => setMobileOpen(false)} aria-label="Close navigation">
              <X className="size-5" />
            </button>
          </div>
          <nav className="mt-8 flex flex-col gap-6 text-lg">
            <a href="#today" onClick={() => setMobileOpen(false)}>Today</a>
            <a href="#trending" onClick={() => setMobileOpen(false)}>Trends</a>
            <a href="#tools" onClick={() => setMobileOpen(false)}>Tools</a>
          </nav>
        </div>
      )}

      <main className="dashboard-shell mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <section className="mb-8 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="size-4" />
              {todayLabel}
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">Today</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Today&apos;s MLB matchups</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              {games.length > 0 ? `${games.length} real MLB matchups` : 'Loading games...'}; markets and analysis are mock data
            </p>
          </div>
          <button className="flex items-center gap-2 self-start rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-muted sm:self-auto">
            <Search className="size-4" />
            Search players or teams
          </button>
        </section>

        {/* Games Grid */}
        <section id="games" className="mb-10">
          <div className="grid gap-4 lg:grid-cols-3">
            {loading ? (
              <div className="col-span-full p-8 text-center">Loading games...</div>
            ) : games.length === 0 ? (
              <div className="col-span-full p-8 text-center">No games available</div>
            ) : (
              games.map((game: any) => (
                <div
                  key={game.gamePk}
                  onClick={() => setDetailGame(game)}
                  className="cursor-pointer rounded-2xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md hover:border-primary/50"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock3 className="size-4 text-muted-foreground" />
                      <span className="text-sm font-semibold">
                        {new Date(game.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${game.status === 'live' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                      {game.status === 'live' ? `Live - Inning ${game.inning || 1}` : 'Upcoming'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {/* Away Team */}
                    <div className="flex flex-col items-center gap-2">
                      <TeamLogo team={game.awayTeam} size="size-12" />
                      <span className="text-sm font-semibold">{game.awayTeam}</span>
                      <span className="text-2xl font-bold">{game.awayScore}</span>
                    </div>

                    {/* Home Team */}
                    <div className="flex flex-col items-center gap-2">
                      <TeamLogo team={game.homeTeam} size="size-12" />
                      <span className="text-sm font-semibold">{game.homeTeam}</span>
                      <span className="text-2xl font-bold">{game.homeScore}</span>
                    </div>
                  </div>

                  {/* Markets - Mock Data */}
                  <div className="space-y-2 border-t border-border pt-4">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">SPREAD:</span>
                      <span className="font-semibold text-yellow-600">{game.odds.spread}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">O/U:</span>
                      <span className="font-semibold text-yellow-600">{game.odds.overUnder}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">ML:</span>
                      <span className="font-semibold text-yellow-600">{game.odds.moneyline}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section id="trending" className="mb-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-5 flex items-end justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-primary">Trending today</p>
                <h2 className="mt-1 text-xl font-bold">Most popular bets</h2>
              </div>
              <select className="rounded-lg border border-border bg-background px-3 py-2 text-sm">
                <option>Most bet on</option>
                <option>Highest hit rate</option>
              </select>
            </div>
            <div className="flex flex-col gap-3">
              {popularBets.map((bet, index) => (
                <div key={bet.player} className="rounded-xl border border-border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <span className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-bold">{index + 1}</span>
                      <div>
                        <p className="font-semibold">
                          {bet.player} <span className="font-normal text-muted-foreground">{bet.matchup}</span>
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {bet.bet} <span className="font-semibold text-foreground">{bet.odds}</span>
                        </p>
                      </div>
                    </div>
                    <TrendingUp className="size-4 text-primary" />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {bet.reason} · {bet.hitRate}
                    </span>
                    <span className="font-bold text-primary">{bet.percent}</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary" style={{ width: bet.percent }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center gap-2">
              <Bot className="size-5 text-primary" />
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-primary">Ask the assistant</p>
                <h2 className="mt-1 text-xl font-bold">Make today easier to read</h2>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">Get a plain-English explanation of a matchup or market. This is a mock assistant for the prototype.</p>
            <div className="mt-5 rounded-xl bg-muted/50 p-4 text-sm leading-6">{answer}</div>
            <div className="mt-4 flex gap-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') askAssistant()
                }}
                placeholder="Ask about a game..."
                className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              />
              <button onClick={askAssistant} className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">
                Ask
              </button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => setQuestion('What should I know about today?')}
                className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted"
              >
                Today&apos;s overview
              </button>
              {games.length > 0 && (
                <button
                  onClick={() => setQuestion(`Explain ${games[0]?.awayTeam} vs ${games[0]?.homeTeam}`)}
                  className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted"
                >
                  Explain selected game
                </button>
              )}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 text-xs text-muted-foreground sm:flex-row sm:justify-between sm:px-6">
          <span>{games.length > 0 ? 'LineMate · Real MLB schedule connected' : 'LineMate · No games available'}</span>
          <span>No wagering or bet placement available</span>
        </div>
      </footer>
    </div>
  )
}
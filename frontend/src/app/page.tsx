'use client'

import useSWR from 'swr'
import { useMemo, useState } from 'react'
import { GameDetailView } from '@/components/dashboard/GameDetailView'
import { fetchTodayGames } from '@/lib/api'
import { mockGames } from '@/lib/mock-data'
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

const games = [
  { away: 'CLE', home: 'BAL', time: '10:35 PM', awayRecord: '72-70', homeRecord: '78-64', awayColor: 'bg-sky-500', homeColor: 'bg-orange-500', spread: 'BAL -1.5', total: '8.5', ml: 'BAL -125', note: 'Baltimore has won 6 of its last 8 at home.' },
  { away: 'MIN', home: 'DET', time: '10:40 PM', awayRecord: '75-67', homeRecord: '81-61', awayColor: 'bg-indigo-500', homeColor: 'bg-blue-700', spread: 'DET -1.5', total: '8.0', ml: 'DET -140', note: 'Detroit ranks top five in run differential this month.' },
  { away: 'HOU', home: 'PHI', time: '10:40 PM', awayRecord: '79-63', homeRecord: '84-58', awayColor: 'bg-orange-600', homeColor: 'bg-red-600', spread: 'PHI -1.5', total: '8.5', ml: 'PHI -155', note: 'Philadelphia is 18-9 against left-handed starters.' },
  { away: 'NYM', home: 'MIA', time: '10:40 PM', awayRecord: '77-65', homeRecord: '61-81', awayColor: 'bg-blue-600', homeColor: 'bg-teal-500', spread: 'NYM -1.5', total: '7.5', ml: 'NYM -175', note: 'New York has covered in 7 of its last 10.' },
  { away: 'LAA', home: 'BOS', time: '10:45 PM', awayRecord: '60-82', homeRecord: '76-66', awayColor: 'bg-red-500', homeColor: 'bg-red-700', spread: 'BOS -1.5', total: '9.0', ml: 'BOS -160', note: 'Fenway games are averaging 10.1 runs this season.' },
  { away: 'COL', home: 'NYY', time: '11:05 PM', awayRecord: '54-88', homeRecord: '86-56', awayColor: 'bg-purple-600', homeColor: 'bg-slate-900', spread: 'NYY -2.5', total: '9.5', ml: 'NYY -245', note: 'New York leads the league in home runs at home.' },
]

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
}

function TeamLogo({ team, size = 'size-14' }: { team: string; size?: string }) {
  const logo = teamLogos[team]
  return logo ? <img src={logo.url} alt={`${logo.label} logo`} className={`${size} object-contain drop-shadow-lg`} /> : <span aria-label={`${team} team logo`} className={`inline-flex ${size} items-center justify-center rounded-full bg-muted text-sm font-black text-foreground`}>{team.slice(0, 2)}</span>
}

const popularBets = [
  { player: 'T. Hernández', matchup: 'vs CIN', bet: 'Over 0.5 Hits', odds: '-133', hitRate: '8 of last 8', percent: '100%', reason: 'Strong recent form' },
  { player: 'H. Wesneski', matchup: '@ PHI', bet: 'Over 3.5 Strikeouts', odds: '-110', hitRate: '7 of last 7', percent: '100%', reason: 'Favorable matchup' },
  { player: 'C. Burnes', matchup: '@ KC', bet: 'Over 2.5 Strikeouts', odds: '-125', hitRate: '18 of last 18', percent: '100%', reason: 'Consistent volume' },
]

function TeamMark({ team, color }: { team: string; color: string }) {
  return <span className={`inline-flex size-9 items-center justify-center rounded-full text-[10px] font-bold text-white ${color}`}>{team}</span>
}

function Market({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-border bg-muted/40 px-3 py-2"><p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold text-foreground">{value}</p></div>
}

function toDashboardGame(game: import('@/lib/mock-data').Game) {
  return {
    ...game,
    away: game.awayTeamLogo || game.awayTeam,
    home: game.homeTeamLogo || game.homeTeam,
    awayRecord: 'Record unavailable',
    homeRecord: 'Record unavailable',
    awayColor: 'bg-slate-500',
    homeColor: 'bg-slate-700',
    spread: game.odds.spread,
    total: game.odds.overUnder,
    ml: game.odds.moneyline,
    note: 'Live matchup data loaded from the backend. Additional analysis remains mocked.',
  }
}

export default function Dashboard() {
  const { data: backendGames, error: gamesError } = useSWR('today-games', fetchTodayGames, { revalidateOnFocus: false })
  const displayGames = backendGames?.length ? backendGames.map(toDashboardGame) : games
  const [selectedGame, setSelectedGame] = useState(games[0])
  const [detailGame, setDetailGame] = useState<(typeof games)[number] | null>(null)
  const [stake, setStake] = useState('100')
  const [odds, setOdds] = useState('-110')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isLightMode, setIsLightMode] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('Ask about today\'s matchups, trends, or how to read a market.')

  const payout = useMemo(() => {
    const amount = Number(stake) || 0
    const line = Number(odds) || 0
    if (!amount || !line) return '0.00'
    return (line > 0 ? amount * (line / 100) : amount * (100 / Math.abs(line))).toFixed(2)
  }, [stake, odds])

  function askAssistant() {
    if (!question.trim()) return
    setAnswer(`For ${question.trim()}, start with the matchup context, then compare the market price with the underlying trend. This is a mock analysis for now.`)
    setQuestion('')
  }

  if (detailGame) {
    return <div className={`${isLightMode ? 'light' : 'dark'} min-h-screen bg-background text-foreground`}><GameDetailView game={detailGame} teamLogos={teamLogos} onBack={() => setDetailGame(null)} /></div>
  }

  return (
    <div className={`${isLightMode ? 'light' : 'dark'} min-h-screen bg-background text-foreground`}>
      <header className="sticky top-0 z-30 border-b border-border/80 bg-background backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-8 px-4 sm:px-6">
          <button className="md:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu className="size-5" /></button>
          <div className="flex items-center gap-2 text-lg font-bold tracking-tight"><span className="inline-flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">L</span>LineMate<span className="text-muted-foreground">/</span><span className="text-sm font-medium text-muted-foreground">MLB</span><ChevronDown className="size-4 text-muted-foreground" /></div>
          <nav className="hidden items-center gap-6 text-sm font-medium md:flex"><a className="text-foreground" href="#today">Today</a><a className="text-muted-foreground hover:text-foreground" href="#trending">Trends</a><a className="text-muted-foreground hover:text-foreground" href="#tools">Tools</a></nav>
          <div className="ml-auto flex items-center gap-3"><button className="hidden text-sm text-muted-foreground sm:block">Log in</button><button aria-label={isLightMode ? 'Switch to dark mode' : 'Switch to light mode'} onClick={() => setIsLightMode((value) => !value)} className="inline-flex size-9 items-center justify-center rounded-lg border border-border text-muted-foreground transition hover:bg-muted">{isLightMode ? <Moon className="size-4" /> : <Sun className="size-4" />}</button><button className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">Start free trial</button></div>
        </div>
      </header>

      {mobileOpen && <div className="fixed inset-0 z-50 bg-background p-6 md:hidden"><div className="flex items-center justify-between"><span className="font-bold">Navigation</span><button onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X className="size-5" /></button></div><nav className="mt-8 flex flex-col gap-6 text-lg"><a href="#today" onClick={() => setMobileOpen(false)}>Today</a><a href="#trending" onClick={() => setMobileOpen(false)}>Trends</a><a href="#tools" onClick={() => setMobileOpen(false)}>Tools</a></nav></div>}

      <main className="dashboard-shell mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <section className="mb-8 flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div><div className="mb-3 flex items-center gap-2 text-sm text-muted-foreground"><CalendarDays className="size-4" /> Tuesday, September 8 <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">Today</span></div><h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Today&apos;s MLB matchups</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">A simple daily view of the games, markets, and trends worth knowing before first pitch.</p></div>
          <button className="flex items-center gap-2 self-start rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-muted sm:self-auto"><Search className="size-4" /> Search players or teams</button>
        </section>

        <section id="today" className="mb-10">
          <div className="mb-4 flex items-center justify-between"><div><h2 className="text-xl font-bold">Games today</h2><p className="text-sm text-muted-foreground">{displayGames.length} matchups with consensus markets · {gamesError ? 'Using mock games while the API is unavailable' : backendGames ? 'Backend matchup data' : 'Loading backend matchup data'}</p></div><button className="text-sm font-semibold text-primary">Show all <ArrowRight className="ml-1 inline size-4" /></button></div>
          <div className="games-today-grid grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{displayGames.map((game) => <button key={`${game.away}-${game.home}`} onClick={() => { setSelectedGame(game); setDetailGame(game) }} className={`games-today-card min-h-[286px] rounded-2xl border bg-card p-5 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-xl ${selectedGame === game ? 'border-primary ring-2 ring-primary/25' : 'border-border'}`}><div className="mb-7 flex items-center justify-between text-xs text-muted-foreground"><span className="flex items-center gap-1"><Clock3 className="size-3.5" /> {game.time}</span><span className="rounded-full border border-border px-2.5 py-1">Preview</span></div><div className="flex items-center justify-between gap-3"><div className="flex min-w-0 flex-col items-center gap-3 text-center"><TeamLogo team={game.away} size="size-16" /><div><p className="font-bold">{game.away}</p><p className="text-xs text-muted-foreground">{game.awayRecord}</p></div></div><div className="flex flex-col items-center gap-1 text-center"><span className="text-xs font-bold uppercase tracking-widest text-primary">Today</span><span className="text-xs font-medium text-muted-foreground">at</span></div><div className="flex min-w-0 flex-col items-center gap-3 text-center"><TeamLogo team={game.home} size="size-16" /><div><p className="font-bold">{game.home}</p><p className="text-xs text-muted-foreground">{game.homeRecord}</p></div></div></div><div className="mt-8 grid grid-cols-3 gap-2"><Market label="Spread" value={game.spread} /><Market label="O/U" value={game.total} /><Market label="ML" value={game.ml} /></div></button>)}</div>
        </section>

        <section className="mb-10 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm"><div className="mb-5 flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Game summary</p><h2 className="mt-1 text-2xl font-bold">{selectedGame.away} at {selectedGame.home}</h2><p className="mt-1 text-sm text-muted-foreground">{selectedGame.time} · Market snapshot</p></div><span className="rounded-full bg-muted px-3 py-1 text-xs font-semibold">Mock analysis</span></div><div className="grid gap-3 sm:grid-cols-3"><Market label="Run line" value={selectedGame.spread} /><Market label="Total runs" value={selectedGame.total} /><Market label="Moneyline" value={selectedGame.ml} /></div><div className="mt-5 rounded-xl bg-muted/50 p-4"><div className="flex gap-3"><Sparkles className="mt-0.5 size-5 shrink-0 text-primary" /><div><p className="font-semibold">What stands out</p><p className="mt-1 text-sm leading-6 text-muted-foreground">{selectedGame.note} Use this summary as a starting point, then review the price and your own assumptions.</p></div></div></div><div className="mt-5 grid gap-3 sm:grid-cols-3"><div><p className="text-xs text-muted-foreground">Recent form</p><p className="mt-1 font-semibold">{selectedGame.home} 7-3</p></div><div><p className="text-xs text-muted-foreground">Projected runs</p><p className="mt-1 font-semibold">{selectedGame.home} 4.6 · {selectedGame.away} 3.8</p></div><div><p className="text-xs text-muted-foreground">Consensus</p><p className="mt-1 font-semibold text-primary">62% {selectedGame.home}</p></div></div></div>
          <div id="tools" className="rounded-2xl border border-border bg-card p-5 shadow-sm"><div className="mb-5 flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Quick tool</p><h2 className="mt-1 text-xl font-bold">Betting calculator</h2></div><BarChart3 className="size-5 text-muted-foreground" /></div><label className="text-sm font-medium">Stake</label><div className="mt-2 flex items-center rounded-lg border border-border px-3"><span className="text-muted-foreground">$</span><input value={stake} onChange={(e) => setStake(e.target.value)} className="w-full bg-transparent px-2 py-2 outline-none" inputMode="decimal" /></div><label className="mt-4 block text-sm font-medium">American odds</label><input value={odds} onChange={(e) => setOdds(e.target.value)} className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:ring-2 focus:ring-primary/20" /><div className="mt-5 flex items-end justify-between rounded-xl bg-primary/5 p-4"><div><p className="text-xs text-muted-foreground">Potential profit</p><p className="mt-1 text-2xl font-bold text-primary">${payout}</p></div><p className="text-right text-xs text-muted-foreground">Total return<br /><span className="font-semibold text-foreground">${(Number(stake || 0) + Number(payout)).toFixed(2)}</span></p></div><p className="mt-3 flex gap-2 text-xs leading-5 text-muted-foreground"><Info className="size-3.5 shrink-0" /> For education and planning only. No bets are placed here.</p></div>
        </section>

        <section id="trending" className="mb-10 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm"><div className="mb-5 flex items-end justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Trending today</p><h2 className="mt-1 text-xl font-bold">Most popular bets</h2></div><select className="rounded-lg border border-border bg-background px-3 py-2 text-sm"><option>Most bet on</option><option>Highest hit rate</option></select></div><div className="flex flex-col gap-3">{popularBets.map((bet, index) => <div key={bet.player} className="rounded-xl border border-border p-4"><div className="flex items-start justify-between gap-4"><div className="flex items-start gap-3"><span className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-bold">{index + 1}</span><div><p className="font-semibold">{bet.player} <span className="font-normal text-muted-foreground">{bet.matchup}</span></p><p className="mt-1 text-sm text-muted-foreground">{bet.bet} <span className="font-semibold text-foreground">{bet.odds}</span></p></div></div><TrendingUp className="size-4 text-primary" /></div><div className="mt-3 flex items-center justify-between text-xs"><span className="text-muted-foreground">{bet.reason} · {bet.hitRate}</span><span className="font-bold text-primary">{bet.percent}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: bet.percent }} /></div></div>)}</div></div>
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm"><div className="flex items-center gap-2"><Bot className="size-5 text-primary" /><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Ask the assistant</p><h2 className="mt-1 text-xl font-bold">Make today easier to read</h2></div></div><p className="mt-3 text-sm leading-6 text-muted-foreground">Get a plain-English explanation of a matchup or market. This is a mock assistant for the prototype.</p><div className="mt-5 rounded-xl bg-muted/50 p-4 text-sm leading-6">{answer}</div><div className="mt-4 flex gap-2"><input value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') askAssistant() }} placeholder="Ask about a game..." className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20" /><button onClick={askAssistant} className="rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground">Ask</button></div><div className="mt-4 flex flex-wrap gap-2"><button onClick={() => setQuestion('What should I know about today?')} className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted">Today&apos;s overview</button><button onClick={() => setQuestion(`Explain ${selectedGame.home} vs ${selectedGame.away}`)} className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-muted">Explain selected game</button></div></div>
        </section>
      </main>
      <footer className="border-t border-border py-6"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 text-xs text-muted-foreground sm:flex-row sm:justify-between sm:px-6"><span>LineMate prototype · Mock data only</span><span>No wagering or bet placement available</span></div></footer>
    </div>
  )
}

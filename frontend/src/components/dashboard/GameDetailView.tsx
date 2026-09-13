'use client'

import { useState } from 'react'
import { ArrowLeft, CalendarDays, ChevronRight, CircleHelp, Clock3, MapPin, ShieldCheck, TrendingUp, Users } from 'lucide-react'

type DetailGame = {
  away: string
  home: string
  time: string
  awayRecord: string
  homeRecord: string
  spread: string
  total: string
  ml: string
  note: string
}

type TeamLogo = { label: string; url: string }

type Props = {
  game: DetailGame
  teamLogos: Record<string, TeamLogo>
  onBack: () => void
}

const tabs = ['Overview', 'Head-to-head', 'Last 5', 'Rankings', 'Injuries', 'SGP ideas']

const playerInsights = [
  { team: 'Away team', player: 'Starting pitcher', value: '6.2 K / game', detail: 'Consistent strikeout volume in recent starts.' },
  { team: 'Home team', player: 'Top hitter', value: '.318 AVG', detail: 'Strong contact profile against this pitching style.' },
  { team: 'Matchup', player: 'Recent form', value: '7–3', detail: 'Home team has won seven of its last ten.' },
]

const recentGames = [
  ['Sep 7', 'W', '5–3'],
  ['Sep 5', 'L', '2–4'],
  ['Sep 3', 'W', '6–2'],
  ['Sep 1', 'W', '4–1'],
  ['Aug 30', 'L', '3–5'],
]

function TeamBadge({ team, teamLogos, size = 'size-14' }: { team: string; teamLogos: Record<string, TeamLogo>; size?: string }) {
  const logo = teamLogos[team]
  return logo ? <img src={logo.url} alt={`${logo.label} logo`} className={`${size} object-contain`} /> : <span className={`inline-flex ${size} items-center justify-center rounded-full bg-muted text-sm font-bold text-foreground`}>{team}</span>
}

export function GameDetailView({ game, teamLogos, onBack }: Props) {
  const [activeTab, setActiveTab] = useState('Overview')

  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex min-h-20 max-w-[1500px] items-center gap-4 px-4 py-4 sm:px-8">
          <button onClick={onBack} className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold transition hover:bg-muted" aria-label="Back to today’s games"><ArrowLeft className="size-4" /> <span className="hidden sm:inline">Today&apos;s games</span></button>
          <div className="flex items-center gap-3"><TeamBadge team={game.away} teamLogos={teamLogos} size="size-10" /><span className="text-lg font-bold text-muted-foreground">@</span><TeamBadge team={game.home} teamLogos={teamLogos} size="size-10" /></div>
          <div><p className="text-xs font-bold uppercase tracking-widest text-primary">Game detail</p><h1 className="text-lg font-bold sm:text-2xl">{game.away} at {game.home}</h1></div>
          <span className="ml-auto hidden rounded-full border border-border px-3 py-1 text-xs font-semibold text-muted-foreground sm:inline-flex">Mock data</span>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1500px] gap-5 px-4 py-5 sm:px-8 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="order-2 rounded-2xl border border-border bg-card p-4 lg:order-1">
          <div className="mb-4 flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Player view</p><h2 className="mt-1 text-lg font-bold">Key information</h2></div><Users className="size-5 text-muted-foreground" /></div>
          <div className="flex flex-col gap-3">{playerInsights.map((item) => <article key={item.player} className="rounded-xl border border-border bg-background p-3"><div className="flex items-center justify-between gap-2"><span className="text-xs font-semibold text-muted-foreground">{item.team}</span><ChevronRight className="size-4 text-muted-foreground" /></div><h3 className="mt-2 font-semibold">{item.player}</h3><p className="mt-1 text-lg font-bold text-primary">{item.value}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p></article>)}</div>
          <p className="mt-4 text-xs leading-5 text-muted-foreground">Use these as context, not predictions. Player availability and lines are mocked for this prototype.</p>
        </aside>

        <main className="order-1 min-w-0 lg:order-2">
          <section className="rounded-2xl border border-border bg-card p-4 sm:p-6">
            <div className="flex flex-col gap-5 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">Game summary</p><h2 className="mt-1 text-2xl font-bold sm:text-3xl">{game.away} at {game.home}</h2><p className="mt-2 text-sm text-muted-foreground">Today · {game.time} · Summary-first view</p></div><div className="flex items-center gap-5"><div className="text-center"><TeamBadge team={game.away} teamLogos={teamLogos} size="size-12" /><p className="mt-1 text-xs font-bold">{game.away}</p><p className="text-xs text-muted-foreground">{game.awayRecord}</p></div><span className="text-sm font-bold text-muted-foreground">VS</span><div className="text-center"><TeamBadge team={game.home} teamLogos={teamLogos} size="size-12" /><p className="mt-1 text-xs font-bold">{game.home}</p><p className="text-xs text-muted-foreground">{game.homeRecord}</p></div></div></div>

            <nav className="mt-5 grid grid-cols-2 gap-2 rounded-xl bg-muted p-1 sm:grid-cols-3 lg:grid-cols-6" aria-label="Game summary tabs">{tabs.map((tab) => <button key={tab} onClick={() => setActiveTab(tab)} className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${activeTab === tab ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>{tab}</button>)}</nav>

            <div className="mt-6">{activeTab === 'Overview' && <Overview game={game} />}{activeTab === 'Head-to-head' && <HeadToHead game={game} />}{activeTab === 'Last 5' && <LastFive game={game} teamLogos={teamLogos} />}{activeTab === 'Rankings' && <Rankings game={game} />}{activeTab === 'Injuries' && <Injuries game={game} />}{activeTab === 'SGP ideas' && <SgpIdeas game={game} />}</div>
          </section>
        </main>
      </div>
    </div>
  )
}

function Overview({ game }: { game: DetailGame }) {
  return <div className="grid gap-5 xl:grid-cols-[1fr_280px]"><div><SectionTitle title="Matchup information" /><div className="grid gap-4 sm:grid-cols-2"><TeamSummary team={game.away} record={game.awayRecord} rank="7th" /><TeamSummary team={game.home} record={game.homeRecord} rank="4th" /></div><div className="mt-5 grid gap-3 sm:grid-cols-3"><InfoRow icon={<CalendarDays className="size-4" />} label="Game time" value={game.time} /><InfoRow icon={<MapPin className="size-4" />} label="Venue" value="Mockball Park" /><InfoRow icon={<Clock3 className="size-4" />} label="Status" value="Preview" /></div><div className="mt-6"><SectionTitle title="Game context" /><div className="rounded-xl border border-border bg-background p-4"><div className="flex gap-3"><TrendingUp className="mt-0.5 size-5 shrink-0 text-primary" /><p className="text-sm leading-6 text-muted-foreground">{game.note} This plain-English note is a starting point for understanding the matchup before reviewing each market.</p></div></div></div></div><MarketSnapshot game={game} /></div>
}

function HeadToHead({ game }: { game: DetailGame }) {
  const rows = [['Runs', '4', '3'], ['Hits', '9', '7'], ['Home runs', '2', '1'], ['ERA', '3.84', '4.21'], ['Walks', '3', '4']]
  return <div><SectionTitle title="Head-to-head snapshot" /><p className="mb-4 text-sm text-muted-foreground">Recent meetings summarized by the most useful game stats.</p><div className="overflow-hidden rounded-xl border border-border"><div className="grid grid-cols-3 bg-muted px-4 py-3 text-sm font-bold"><span>{game.away}</span><span className="text-center">Stat</span><span className="text-right">{game.home}</span></div>{rows.map(([label, away, home]) => <div key={label} className="grid grid-cols-3 border-t border-border px-4 py-4 text-sm"><span>{away}</span><span className="text-center text-muted-foreground">{label}</span><span className="text-right">{home}</span></div>)}</div></div>
}

function LastFive({ game, teamLogos }: { game: DetailGame; teamLogos: Record<string, TeamLogo> }) {
  return <div><SectionTitle title="Last 5 games" /><div className="grid gap-5 lg:grid-cols-2"><RecentTeam name={game.away} teamLogos={teamLogos} games={recentGames} /><RecentTeam name={game.home} teamLogos={teamLogos} games={recentGames.map(([date, result, score]) => [date, result === 'W' ? 'L' : 'W', score])} /></div></div>
}

function RecentTeam({ name, teamLogos, games }: { name: string; teamLogos: Record<string, TeamLogo>; games: string[][] }) {
  return <div className="rounded-xl border border-border bg-background p-4"><div className="mb-4 flex items-center gap-3"><TeamBadge team={name} teamLogos={teamLogos} size="size-9" /><h3 className="font-bold">{name}</h3></div><div className="flex flex-col gap-2">{games.map(([date, result, score]) => <div key={date} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm"><span className="text-muted-foreground">{date}</span><span className={result === 'W' ? 'font-bold text-primary' : 'font-bold text-destructive'}>{result}</span><span>{score}</span></div>)}</div></div>
}

function Rankings({ game }: { game: DetailGame }) {
  const rows = [['Runs scored', '8th', '14th'], ['Runs allowed', '11th', '6th'], ['Home runs', '5th', '9th'], ['Bullpen ERA', '12th', '7th']]
  return <div><SectionTitle title="Team rankings" /><div className="overflow-hidden rounded-xl border border-border"><div className="grid grid-cols-3 bg-muted px-4 py-3 text-sm font-bold"><span>{game.away}</span><span className="text-center">Category</span><span className="text-right">{game.home}</span></div>{rows.map(([away, label, home]) => <div key={label} className="grid grid-cols-3 border-t border-border px-4 py-4 text-sm"><span>{away}</span><span className="text-center text-muted-foreground">{label}</span><span className="text-right">{home}</span></div>)}</div></div>
}

function Injuries({ game }: { game: DetailGame }) {
  const rows = [['Starting pitcher', 'Questionable', 'Rest day'], ['Outfielder', '10-day IL', 'Wrist'], ['Reliever', 'Available', '—']]
  return <div><SectionTitle title="Injuries & availability" /><p className="mb-4 text-sm text-muted-foreground">Mock availability notes to keep lineup context easy to scan.</p><div className="overflow-hidden rounded-xl border border-border"><div className="grid grid-cols-3 bg-muted px-4 py-3 text-sm font-bold"><span>Role</span><span>{game.away}</span><span>{game.home}</span></div>{rows.map(([role, away, home]) => <div key={role} className="grid grid-cols-3 border-t border-border px-4 py-4 text-sm"><span>{role}</span><span className="text-muted-foreground">{away}</span><span className="text-muted-foreground">{home}</span></div>)}</div></div>
}

function SgpIdeas({ game }: { game: DetailGame }) {
  const ideas = [`${game.home} moneyline`, `${game.away} +1.5`, `Over ${game.total} runs`]
  return <div><SectionTitle title="Same-game ideas" /><p className="mb-4 text-sm text-muted-foreground">Educational combinations to compare. Nothing can be placed from this prototype.</p><div className="grid gap-3 sm:grid-cols-3">{ideas.map((idea, index) => <div key={idea} className="rounded-xl border border-border bg-background p-4"><p className="text-xs font-bold uppercase tracking-widest text-primary">Leg {index + 1}</p><p className="mt-2 font-semibold">{idea}</p><p className="mt-2 text-xs leading-5 text-muted-foreground">Review independently before combining assumptions.</p></div>)}</div><div className="mt-5 flex gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4 text-sm leading-6"><CircleHelp className="mt-0.5 size-5 shrink-0 text-primary" /> Mock education only. This platform does not place wagers.</div></div>
}

function MarketSnapshot({ game }: { game: DetailGame }) {
  return <aside className="rounded-xl border border-border bg-background p-4"><div className="mb-4 flex items-center justify-between"><h3 className="font-bold">Market snapshot</h3><ShieldCheck className="size-4 text-primary" /></div><div className="flex flex-col gap-3"><MarketLine label="Spread" value={game.spread} /><MarketLine label="Over / under" value={game.total} /><MarketLine label="Moneyline" value={game.ml} /></div><p className="mt-4 text-xs leading-5 text-muted-foreground">Lines are mock examples for learning how markets are displayed.</p></aside>
}

function MarketLine({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between rounded-lg border border-border px-3 py-3"><span className="text-sm text-muted-foreground">{label}</span><span className="font-semibold text-primary">{value}</span></div>
}

function TeamSummary({ team, record, rank }: { team: string; record: string; rank: string }) {
  return <div className="rounded-xl border border-border bg-background p-4"><p className="font-bold">{team}</p><p className="mt-3 text-sm text-muted-foreground">Record <span className="font-semibold text-foreground">{record}</span></p><p className="mt-2 text-sm text-muted-foreground">Division rank <span className="font-semibold text-foreground">{rank}</span></p></div>
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="flex items-center gap-3 rounded-xl border border-border bg-background p-3"><span className="text-primary">{icon}</span><div><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold">{value}</p></div></div>
}

function SectionTitle({ title }: { title: string }) {
  return <h3 className="mb-4 text-xl font-bold">{title}</h3>
}

function Market({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-border bg-muted/40 px-3 py-2"><p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p><p className="mt-1 text-sm font-semibold text-foreground">{value}</p></div>
}

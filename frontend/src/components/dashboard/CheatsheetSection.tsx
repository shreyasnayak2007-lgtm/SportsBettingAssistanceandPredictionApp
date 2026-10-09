'use client'

import { ArrowLeft, BarChart3, Check, ChevronRight, Flame, TrendingUp } from 'lucide-react'

export type PropCard = {
  id: string
  player: string
  team: string
  matchup: string
  market: string
  line: string
  odds: string
  hitRate: string
  streak: string
  category: 'Hitting' | 'Pitching'
  recentResults: string[]
  reason: string
}

const props: PropCard[] = [
  { id: 'hernandez-hits', player: 'Teoscar Hernandez', team: 'LAD', matchup: 'vs COL', market: 'Hits', line: 'Over 0.5', odds: '-133', hitRate: '100%', streak: '8 of last 8', category: 'Hitting', recentResults: ['1 H', '2 H', '1 H', '1 H', '2 H'], reason: 'Strong recent contact profile with consistent plate appearances.' },
  { id: 'wesneski-strikeouts', player: 'Hayden Wesneski', team: 'HOU', matchup: '@ PHI', market: 'Strikeouts', line: 'Over 3.5', odds: '-110', hitRate: '100%', streak: '7 of last 7', category: 'Pitching', recentResults: ['5 K', '6 K', '4 K', '5 K', '7 K'], reason: 'Reliable strikeout volume across his recent starts.' },
  { id: 'burnes-strikeouts', player: 'Corbin Burnes', team: 'ARI', matchup: '@ KC', market: 'Strikeouts', line: 'Over 2.5', odds: '-125', hitRate: '100%', streak: '18 of last 18', category: 'Pitching', recentResults: ['5 K', '4 K', '6 K', '3 K', '5 K'], reason: 'Consistent swing-and-miss results and steady workload.' },
  { id: 'judge-total-bases', player: 'Aaron Judge', team: 'NYY', matchup: 'vs BOS', market: 'Total bases', line: 'Over 1.5', odds: '-115', hitRate: '100%', streak: '6 of last 6', category: 'Hitting', recentResults: ['2 TB', '3 TB', '2 TB', '4 TB', '2 TB'], reason: 'Power output has stayed above this line in every listed game.', },
]

export function PropsSection({ onSelect }: { onSelect: (prop: PropCard) => void }) {
  return (
    <section id="props" className="mb-10 border-y border-border py-10">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-primary"><BarChart3 className="size-4" /> Props</div>
          <h2 className="mt-2 text-2xl font-bold tracking-tight">Perfect recent hit rate</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Mock player props that cleared their listed line in every game in the sample.</p>
        </div>
        <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">100% hit rate</span>
      </div>
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="hidden grid-cols-[1.4fr_1fr_0.8fr_0.8fr_32px] gap-4 border-b border-border bg-muted/40 px-5 py-3 text-xs font-bold uppercase tracking-wider text-muted-foreground md:grid"><span>Player</span><span>Prop</span><span>Hit rate</span><span>Streak</span><span /></div>
        {props.map((prop) => (
          <button key={prop.id} type="button" onClick={() => onSelect(prop)} className="grid w-full gap-3 border-b border-border px-5 py-4 text-left transition last:border-b-0 hover:bg-muted/40 md:grid-cols-[1.4fr_1fr_0.8fr_0.8fr_32px] md:items-center md:gap-4">
            <span className="min-w-0"><span className="flex items-center gap-2 font-bold">{prop.player}<span className="text-xs font-semibold text-muted-foreground">{prop.team}</span></span><span className="mt-1 block text-xs text-muted-foreground">{prop.matchup} · {prop.category}</span></span>
            <span><span className="block text-sm font-semibold">{prop.market} {prop.line}</span><span className="mt-1 block text-xs text-muted-foreground">{prop.odds} odds</span></span>
            <span className="flex items-center gap-1.5 text-sm font-bold text-emerald-600"><Check className="size-4" />{prop.hitRate}</span>
            <span className="text-sm font-semibold">{prop.streak}</span>
            <ChevronRight className="size-5 text-muted-foreground" />
          </button>
        ))}
      </div>
    </section>
  )
}

export function PropDetailView({ prop, onBack }: { prop: PropCard; onBack: () => void }) {
  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur"><div className="mx-auto flex min-h-20 max-w-5xl items-center gap-4 px-4 py-4 sm:px-8"><button type="button" onClick={onBack} className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-semibold transition hover:bg-muted"><ArrowLeft className="size-4" /> Back to dashboard</button><span className="ml-auto text-xs font-bold uppercase tracking-widest text-primary">Prop detail</span></div></header>
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-8">
        <div className="flex flex-col gap-5 border-b border-border pb-8 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-primary">{prop.category} · {prop.matchup}</p><h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">{prop.player}</h1><p className="mt-3 text-lg text-muted-foreground">{prop.market} {prop.line} <span className="font-semibold text-foreground">({prop.odds})</span></p></div><div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-emerald-600"><Flame className="size-5" /><span className="text-xl font-bold">{prop.hitRate}</span></div></div>
        <div className="mt-8 grid gap-5 lg:grid-cols-[1fr_300px]"><section className="rounded-2xl border border-border bg-card p-6 sm:p-8"><div className="flex items-center gap-2"><TrendingUp className="size-5 text-primary" /><h2 className="text-xl font-bold">Recent results</h2></div><div className="mt-6 grid grid-cols-5 gap-2">{prop.recentResults.map((result, index) => <div key={`${result}-${index}`} className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-center"><p className="text-xs text-muted-foreground">Game {index + 1}</p><p className="mt-2 font-bold text-emerald-600">{result}</p></div>)}</div><div className="mt-8 rounded-xl border border-border bg-background p-4"><p className="text-sm leading-6 text-muted-foreground">{prop.reason}</p></div></section><aside className="rounded-2xl border border-border bg-card p-5"><h2 className="font-bold">Prop snapshot</h2><div className="mt-4 space-y-3"><div className="rounded-xl border border-border bg-background p-3"><p className="text-xs text-muted-foreground">Hit rate</p><p className="mt-1 text-lg font-bold text-emerald-600">{prop.hitRate}</p></div><div className="rounded-xl border border-border bg-background p-3"><p className="text-xs text-muted-foreground">Current streak</p><p className="mt-1 text-sm font-semibold">{prop.streak}</p></div><div className="rounded-xl border border-border bg-background p-3"><p className="text-xs text-muted-foreground">Matchup</p><p className="mt-1 text-sm font-semibold">{prop.matchup}</p></div></div><p className="mt-5 text-xs leading-5 text-muted-foreground">Mock data for interface preview. This app does not place wagers.</p></aside></div>
      </main>
    </div>
  )
}

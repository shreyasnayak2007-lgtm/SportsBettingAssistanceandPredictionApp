import React from 'react'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import type { Game } from '@/lib/mock-data'

interface GameCardProps {
  game: Game
}

export function GameCard({ game }: GameCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <Badge
            variant={
              game.status === 'live'
                ? 'error'
                : game.status === 'final'
                  ? 'info'
                  : 'default'
            }
          >
            {game.status === 'live'
              ? `Live - Inning ${game.inning}`
              : game.status === 'final'
                ? 'Final'
                : game.time}
          </Badge>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="text-center">
            <span className="inline-flex size-10 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{game.homeTeamLogo}</span>
            <p className="text-sm font-semibold mt-1">{game.homeTeam}</p>
            <p className="text-2xl font-bold text-primary">{game.homeScore}</p>
          </div>

          <div className="flex items-center justify-center">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">vs</p>
              {game.inning && <p className="text-xs font-semibold">{game.inning}</p>}
            </div>
          </div>

          <div className="text-center">
            <span className="inline-flex size-10 items-center justify-center rounded-full bg-accent/10 text-xs font-bold text-accent">{game.awayTeamLogo}</span>
            <p className="text-sm font-semibold mt-1">{game.awayTeam}</p>
            <p className="text-2xl font-bold">{game.awayScore}</p>
          </div>
        </div>

        <div className="space-y-2 pt-3 border-t border-border">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Spread:</span>
            <span className="font-semibold">{game.odds.spread}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">O/U:</span>
            <span className="font-semibold">{game.odds.overUnder}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">ML:</span>
            <span className="font-semibold">{game.odds.moneyline}</span>
          </div>
        </div>

        <p className="mt-4 text-center text-xs text-muted-foreground">Analysis and market education only</p>
      </CardContent>
    </Card>
  )
}

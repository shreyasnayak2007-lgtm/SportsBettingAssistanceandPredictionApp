'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

const sports = ['MLB', 'NFL', 'NBA', 'Soccer', 'Hockey']
const leagues = ['MLB', 'AL East', 'AL West', 'NL East', 'NL West']

export function Sidebar() {
  const [expandedLeagues, setExpandedLeagues] = useState(false)

  return (
    <aside className="w-48 bg-muted border-r border-border p-4 overflow-y-auto h-screen">
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-muted-foreground mb-3">Sports</h2>
        <div className="space-y-2">
          {sports.map((sport) => (
            <button
              key={sport}
              className={cn(
                'w-full text-left px-3 py-2 rounded text-sm font-medium transition-colors',
                sport === 'MLB'
                  ? 'bg-primary text-primary-foreground'
                  : 'text-foreground hover:bg-border'
              )}
            >
              {sport}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <button
          onClick={() => setExpandedLeagues(!expandedLeagues)}
          className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors"
        >
          Leagues
          <ChevronDown
            size={16}
            className={cn(
              'transition-transform',
              expandedLeagues && 'rotate-180'
            )}
          />
        </button>
        {expandedLeagues && (
          <div className="mt-2 space-y-1">
            {leagues.map((league) => (
              <button
                key={league}
                className="w-full text-left px-3 py-1.5 rounded text-xs text-foreground hover:bg-border transition-colors"
              >
                {league}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <button className="w-full text-left px-3 py-2 rounded text-sm text-foreground hover:bg-border transition-colors">
          Favorites
        </button>
        <button className="w-full text-left px-3 py-2 rounded text-sm text-foreground hover:bg-border transition-colors">
          Trending
        </button>
      </div>
    </aside>
  )
}

'use client'

import React from 'react'
import { Search, Bell, User, Menu } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function TopNav() {
  return (
    <header className="bg-background border-b border-border sticky top-0 z-40">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <h1 className="text-2xl font-bold text-primary">SportsBetr</h1>
          <div className="hidden md:flex items-center bg-muted rounded-lg px-3 py-2">
            <Search size={18} className="text-muted-foreground" />
            <input
              type="text"
              placeholder="Search games, teams, players..."
              className="bg-transparent ml-2 text-sm focus:outline-none w-48"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm">
            <Bell size={20} />
          </Button>
          <Button variant="ghost" size="sm">
            <User size={20} />
          </Button>
          <Button variant="primary" size="sm">
            Sign In
          </Button>
        </div>
      </div>
    </header>
  )
}

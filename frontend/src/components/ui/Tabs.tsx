'use client'

import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface TabsProps {
  tabs: { label: string; id: string }[]
  children: React.ReactNode
  defaultTab?: string
}

interface TabsContentProps {
  tab: string
  active: boolean
  children: React.ReactNode
}

export function Tabs({ tabs, children, defaultTab }: TabsProps) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id)

  return (
    <div>
      <div className="flex gap-1 border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActive(tab.id)}
            className={cn(
              'px-4 py-2 text-sm font-medium transition-colors',
              active === tab.id
                ? 'text-primary border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<TabsContentProps>, {
              active: child.props.tab === active,
            })
          }
          return child
        })}
      </div>
    </div>
  )
}

export function TabsContent({ tab, active, children }: TabsContentProps) {
  if (!active) return null
  return <div>{children}</div>
}

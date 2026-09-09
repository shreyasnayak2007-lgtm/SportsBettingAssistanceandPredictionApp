'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { calculatePayout } from '@/lib/utils'

export function Calculator() {
  const [stake, setStake] = useState('100')
  const [odds, setOdds] = useState('-110')

  const payout = calculatePayout(parseFloat(stake) || 0, odds)
  const totalReturn = (parseFloat(stake) || 0) + payout

  return (
    <Card>
      <CardHeader>
        <CardTitle>Betting Calculator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Stake ($)</label>
          <Input
            type="number"
            value={stake}
            onChange={(e) => setStake(e.target.value)}
            placeholder="100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Odds</label>
          <Input
            value={odds}
            onChange={(e) => setOdds(e.target.value)}
            placeholder="-110"
          />
        </div>

        <div className="pt-4 border-t border-border space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Potential Win:</span>
            <span className="font-semibold text-success">
              ${payout.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total Return:</span>
            <span className="font-semibold text-lg">
              ${totalReturn.toFixed(2)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

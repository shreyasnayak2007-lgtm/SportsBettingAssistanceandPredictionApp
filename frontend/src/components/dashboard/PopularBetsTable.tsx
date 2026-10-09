import React from 'react'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table'
import { Badge } from '@/components/ui/Badge'
import type { PopularBet } from '@/lib/mock-data'

interface PopularBetsTableProps {
  bets: PopularBet[]
}

export function PopularBetsTable({ bets }: PopularBetsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Matchup</TableHead>
          <TableHead>Bet</TableHead>
          <TableHead>Odds</TableHead>
          <TableHead>Consensus</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {bets.map((bet) => (
          <TableRow key={bet.id}>
            <TableCell className="font-medium">{bet.matchup}</TableCell>
            <TableCell>{bet.bet}</TableCell>
            <TableCell className="font-semibold text-primary">{bet.odds}</TableCell>
            <TableCell>
              <Badge variant="success">{bet.consensus}%</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

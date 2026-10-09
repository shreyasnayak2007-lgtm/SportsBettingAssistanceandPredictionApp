export function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

export function formatOdds(odds: string): { decimal: number; sign: string } {
  const sign = odds.startsWith('-') ? 'negative' : 'positive'
  const value = Math.abs(parseInt(odds))
  
  if (sign === 'negative') {
    return {
      decimal: 1 + 100 / value,
      sign: '-',
    }
  } else {
    return {
      decimal: 1 + value / 100,
      sign: '+',
    }
  }
}

export function calculatePayout(stake: number, odds: string): number {
  const { decimal } = formatOdds(odds)
  return stake * decimal - stake
}

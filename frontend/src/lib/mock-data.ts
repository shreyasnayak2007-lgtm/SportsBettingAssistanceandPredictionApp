export interface Game {
  id: string
  homeTeam: string
  awayTeam: string
  homeTeamLogo: string
  awayTeamLogo: string
  status: 'live' | 'upcoming' | 'final'
  inning?: number
  homeScore: number
  awayScore: number
  time: string
  odds: {
    spread: string
    overUnder: string
    moneyline: string
  }
}

export interface PopularBet {
  id: string
  matchup: string
  bet: string
  odds: string
  consensus: number
}

export interface PlayerProp {
  id: string
  player: string
  team: string
  prop: string
  over: string
  under: string
}

export interface CommunityPost {
  id: string
  author: string
  timestamp: string
  content: string
  likes: number
  replies: number
  tags: string[]
}

export const mockGames: Game[] = [
  {
    id: '1',
    homeTeam: 'Yankees',
    awayTeam: 'Red Sox',
    homeTeamLogo: 'NYY',
    awayTeamLogo: 'BOS',
    status: 'live',
    inning: 6,
    homeScore: 4,
    awayScore: 2,
    time: 'Live - Bot 6',
    odds: {
      spread: 'NYY -1.5 (-110)',
      overUnder: 'O/U 8.5 (-110)',
      moneyline: 'NYY -180, BOS +155',
    },
  },
  {
    id: '2',
    homeTeam: 'Dodgers',
    awayTeam: 'Giants',
    homeTeamLogo: 'LAD',
    awayTeamLogo: 'SF',
    status: 'upcoming',
    homeScore: 0,
    awayScore: 0,
    time: '7:10 PM PT',
    odds: {
      spread: 'LAD -1.5 (-105)',
      overUnder: 'O/U 7.5 (-110)',
      moneyline: 'LAD -220, SF +185',
    },
  },
  {
    id: '3',
    homeTeam: 'Astros',
    awayTeam: 'Rangers',
    homeTeamLogo: 'HOU',
    awayTeamLogo: 'TEX',
    status: 'upcoming',
    homeScore: 0,
    awayScore: 0,
    time: '8:05 PM CT',
    odds: {
      spread: 'HOU -1.5 (-110)',
      overUnder: 'O/U 8.0 (-110)',
      moneyline: 'HOU -165, TEX +145',
    },
  },
]

export const mockPopularBets: PopularBet[] = [
  {
    id: '1',
    matchup: 'NYY vs BOS',
    bet: 'Yankees -1.5',
    odds: '-110',
    consensus: 72,
  },
  {
    id: '2',
    matchup: 'LAD vs SF',
    bet: 'Dodgers ML',
    odds: '-220',
    consensus: 68,
  },
  {
    id: '3',
    matchup: 'HOU vs TEX',
    bet: 'Over 8.0',
    odds: '-110',
    consensus: 65,
  },
  {
    id: '4',
    matchup: 'NYY vs BOS',
    bet: 'Over 8.5',
    odds: '-110',
    consensus: 61,
  },
  {
    id: '5',
    matchup: 'LAD vs SF',
    bet: 'Dodgers -1.5',
    odds: '-105',
    consensus: 58,
  },
]

export const mockPlayerProps: PlayerProp[] = [
  {
    id: '1',
    player: 'Aaron Judge',
    team: 'Yankees',
    prop: 'HR (Home Runs)',
    over: '0.5 (-130)',
    under: '0.5 (+110)',
  },
  {
    id: '2',
    player: 'Juan Soto',
    team: 'Mets',
    prop: 'Hits',
    over: '1.5 (-110)',
    under: '1.5 (-110)',
  },
  {
    id: '3',
    player: 'Mike Trout',
    team: 'Angels',
    prop: 'RBIs',
    over: '0.5 (-120)',
    under: '0.5 (+100)',
  },
  {
    id: '4',
    player: 'Mookie Betts',
    team: 'Dodgers',
    prop: 'Runs',
    over: '0.5 (-110)',
    under: '0.5 (-110)',
  },
]

export const mockCommunityPosts: CommunityPost[] = [
  {
    id: '1',
    author: 'BetMaster42',
    timestamp: '2 hours ago',
    content: 'Yankees looking strong today. Their pitching is on point. Might tail the spread here.',
    likes: 156,
    replies: 24,
    tags: ['yankees', 'mlb', 'picks'],
  },
  {
    id: '2',
    author: 'StatsNerd88',
    timestamp: '4 hours ago',
    content: 'Interesting trend: Judge has 18 HRs in his last 50 games. That over 0.5 might be worth considering.',
    likes: 298,
    replies: 67,
    tags: ['playerprop', 'analysis', 'yankees'],
  },
  {
    id: '3',
    author: 'CasualBettor',
    timestamp: '1 hour ago',
    content: 'Just hit a 3-leg parlay! Great day in the office. 🔥',
    likes: 89,
    replies: 12,
    tags: ['wins', 'parlay'],
  },
  {
    id: '4',
    author: 'DataDrivenDave',
    timestamp: '3 hours ago',
    content: 'Over/Under historically favors the over by 2.3% at this park. Worth noting for tonight.',
    likes: 213,
    replies: 43,
    tags: ['research', 'ouanalysis', 'trends'],
  },
]

export const mockCalculatorExamples = [
  {
    bet: 'Yankees -1.5',
    stake: 100,
    odds: '-110',
    potentialWin: 90.91,
  },
  {
    bet: 'Dodgers ML',
    stake: 50,
    odds: '-220',
    potentialWin: 22.73,
  },
  {
    bet: 'Parlay 3-Leg',
    stake: 20,
    odds: '+500',
    potentialWin: 120,
  },
]

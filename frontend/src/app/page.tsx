'use client'

import { Sidebar } from '@/components/navigation/Sidebar'
import { TopNav } from '@/components/navigation/TopNav'
import { GameCard } from '@/components/dashboard/GameCard'
import { PopularBetsTable } from '@/components/dashboard/PopularBetsTable'
import { Calculator } from '@/components/dashboard/Calculator'
import { CommunityFeed } from '@/components/dashboard/CommunityFeed'
import { ChatBot } from '@/components/dashboard/ChatBot'
import { Tabs, TabsContent } from '@/components/ui/Tabs'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/Table'
import {
  mockGames,
  mockPopularBets,
  mockPlayerProps,
  mockCommunityPosts,
} from '@/lib/mock-data'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <TopNav />
      <div className="flex">
        <Sidebar />

        <main className="flex-1 overflow-auto">
          <div className="p-6 max-w-7xl mx-auto">
            {/* Hero Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground mb-1">Live Games</p>
                  <p className="text-3xl font-bold text-primary">
                    {mockGames.filter((g) => g.status === 'live').length}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground mb-1">Today&apos;s Matchups</p>
                  <p className="text-3xl font-bold text-primary">{mockGames.length}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground mb-1">Avg Consensus</p>
                  <p className="text-3xl font-bold text-accent">
                    {(
                      mockPopularBets.reduce((sum, b) => sum + b.consensus, 0) /
                      mockPopularBets.length
                    ).toFixed(0)}
                    %
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-muted-foreground mb-1">Trending Posts</p>
                  <p className="text-3xl font-bold text-success">
                    {mockCommunityPosts.length}
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Main Content Area */}
              <div className="lg:col-span-2 space-y-6">
                {/* Live Games Section */}
                <section>
                  <h2 className="text-xl font-bold mb-4">Live Games</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {mockGames.map((game) => (
                      <GameCard key={game.id} game={game} />
                    ))}
                  </div>
                </section>

                {/* Popular Bets & Props Tabs */}
                <section>
                  <Tabs
                    tabs={[
                      { label: 'Most Popular', id: 'popular' },
                      { label: 'Player Props', id: 'props' },
                    ]}
                    defaultTab="popular"
                  >
                    <TabsContent tab="popular" active={true}>
                      <Card>
                        <CardHeader>
                          <CardTitle>Most Popular Bets</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <PopularBetsTable bets={mockPopularBets} />
                        </CardContent>
                      </Card>
                    </TabsContent>
                    <TabsContent tab="props" active={false}>
                      <Card>
                        <CardHeader>
                          <CardTitle>Player Props</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Player</TableHead>
                                <TableHead>Team</TableHead>
                                <TableHead>Prop</TableHead>
                                <TableHead>Over</TableHead>
                                <TableHead>Under</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {mockPlayerProps.map((prop) => (
                                <TableRow key={prop.id}>
                                  <TableCell className="font-semibold">
                                    {prop.player}
                                  </TableCell>
                                  <TableCell>{prop.team}</TableCell>
                                  <TableCell>{prop.prop}</TableCell>
                                  <TableCell className="text-success">
                                    {prop.over}
                                  </TableCell>
                                  <TableCell className="text-destructive">
                                    {prop.under}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>
                    </TabsContent>
                  </Tabs>
                </section>
              </div>

              {/* Sidebar Widgets */}
              <div className="space-y-6">
                <Calculator />

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Community</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CommunityFeed posts={mockCommunityPosts.slice(0, 3)} />
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Chat Bot - Full Width */}
            <div className="mt-6 max-w-2xl">
              <ChatBot />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

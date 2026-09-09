import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Today’s MLB Matchups | LineMate',
  description: 'A simple daily view of MLB matchups, markets, trends, and game summaries.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-background text-foreground">
        {children}
      </body>
    </html>
  )
}

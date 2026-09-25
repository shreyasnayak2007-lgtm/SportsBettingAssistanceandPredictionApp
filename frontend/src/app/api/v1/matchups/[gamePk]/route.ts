import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

type RouteContext = {
  params: { gamePk: string }
}

export async function GET(_request: Request, { params }: RouteContext) {
  const backendUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

  try {
    const response = await fetch(`${backendUrl}/api/v1/matchups/${params.gamePk}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(12_000),
    })
    const body = await response.json().catch(() => ({ detail: 'Backend returned invalid JSON' }))
    return NextResponse.json(body, { status: response.status })
  } catch {
    return NextResponse.json(
      { detail: 'Backend API is unavailable.' },
      { status: 503 },
    )
  }
}

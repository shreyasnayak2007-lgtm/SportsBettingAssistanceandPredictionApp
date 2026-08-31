// src/lib/api-clients.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function getTodayGames() {
  try {
    const res = await fetch(`${API_BASE_URL}/games/today`, { next: { revalidate: 300 } });
    if (!res.ok) throw new Error('Failed to fetch schedule');
    return await res.json();
  } catch (error) {
    console.error('API Error:', error);
    return [];
  }
}
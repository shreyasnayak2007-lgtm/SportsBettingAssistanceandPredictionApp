import { getTodayGames } from '@/lib/api-client';

export default async function HomePage() {
  const games = await getTodayGames();

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', fontFamily: 'system-ui, sans-serif', padding: '0 20px' }}>
      <h1>Sports Betting & Prediction Dashboard</h1>

      {!games || games.length === 0 ? (
        <p style={{ color: '#666' }}>No games found or backend server (port 8000) is unreachable.</p>
      ) : (
        <div style={{ display: 'grid', gap: '16px', marginTop: '20px' }}>
          {games.map((game: any, index: number) => (
            <div key={game.id || index} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
              <h3>{game.home_team} vs {game.away_team}</h3>
              <p>Prediction: {game.prediction}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
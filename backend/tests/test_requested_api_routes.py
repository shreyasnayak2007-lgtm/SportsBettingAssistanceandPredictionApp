import unittest
from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import players
from app.api.v1.endpoints.boxscore import router as boxscore_router
from app.api.v1.endpoints.games import router as games_router
from app.api.v1.endpoints.stats import router as stats_router
from app.db.database import Base, get_db
from app.db.models import (
    BattingSeasonStat,
    Game,
    PitchingSeasonStat,
    Player,
    StatcastPitch,
    Team,
)


class RequestedApiRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

        with cls.Session() as db:
            today = datetime.now(ZoneInfo("America/New_York")).date()
            away = Team(mlb_team_id=101, abbreviation="AAA", name="Away")
            home = Team(mlb_team_id=102, abbreviation="BBB", name="Home")
            db.add_all([away, home])
            db.flush()
            batter = Player(
                mlbam_id=9001,
                full_name="Test Batter",
                team_id=away.id,
                jersey_number="7",
                active=True,
                position="C",
            )
            pitcher = Player(
                mlbam_id=9002,
                full_name="Test Pitcher",
                team_id=home.id,
                jersey_number="12",
                active=True,
                position="P",
                pitch_hand="R",
            )
            db.add_all([batter, pitcher])
            db.flush()
            db.add(BattingSeasonStat(
                player_id=batter.id,
                season=today.year,
                games=3,
                plate_appearances=4,
                at_bats=3,
                runs=1,
                hits=3,
                singles=1,
                doubles=1,
                home_runs=1,
                rbi=3,
                batting_average=1.0,
            ))
            db.add(PitchingSeasonStat(
                player_id=pitcher.id,
                season=today.year,
                games=1,
                games_started=1,
                innings_outs=9,
                earned_runs=2,
                batters_faced=3,
                hits_allowed=3,
                singles_allowed=1,
                doubles_allowed=1,
                home_runs_allowed=1,
                era=6.0,
                whip=1.0,
            ))
            db.add(Game(
                game_pk=777001,
                game_date=today,
                season=today.year,
                away_team_id=away.id,
                home_team_id=home.id,
                status="Final",
                away_score=1,
                home_score=0,
            ))
            for at_bat, event in enumerate(("single", "double", "home_run"), start=1):
                db.add(StatcastPitch(
                    game_pk=777001,
                    game_date=today,
                    at_bat_number=at_bat,
                    pitch_number=4,
                    pitcher_id=9002,
                    batter_id=9001,
                    events=event,
                    description="hit_into_play",
                    launch_speed=100,
                ))
            db.commit()

        cls.app = FastAPI()
        cls.app.include_router(players.router, prefix="/api/v1/players")
        cls.app.include_router(games_router, prefix="/api/v1")
        cls.app.include_router(stats_router, prefix="/api/v1")
        cls.app.include_router(boxscore_router, prefix="/api/v1")

        def override_get_db():
            with cls.Session() as db:
                yield db

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def test_get_player_by_internal_id_returns_json_200(self):
        response = self.client.get("/api/v1/players/1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))
        self.assertEqual(response.json()["mlbam_id"], 9001)

    def test_missing_player_returns_json_404(self):
        response = self.client.get("/api/v1/players/999999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Player not found"})

    def test_stats_telemetry_returns_json_200(self):
        response = self.client.get("/api/v1/stats/telemetry")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))
        self.assertEqual(response.json()["totals"]["statcast_pitches"], 3)

    def test_player_season_stats_return_batting_and_pitching_records(self):
        season = datetime.now(ZoneInfo("America/New_York")).year
        response = self.client.get(
            "/api/v1/players/mlbam/9001/stats",
            params={"season": season},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["batting"]["singles"], 1)
        self.assertEqual(response.json()["batting"]["home_runs"], 1)

        pitcher_response = self.client.get(
            "/api/v1/players/mlbam/9002/pitching-stats",
            params={"season": season},
        )
        self.assertEqual(pitcher_response.status_code, 200, pitcher_response.text)
        self.assertEqual(pitcher_response.json()["era"], 6.0)
        self.assertEqual(pitcher_response.json()["innings_pitched"], "3.0")

    def test_today_games_include_statcast_telemetry(self):
        response = self.client.get("/api/v1/games/today")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()[0]["stats"]["pitches"], 3)
        self.assertEqual(response.json()[0]["stats"]["balls_in_play"], 3)

    def test_boxscore_returns_batting_json_200(self):
        response = self.client.get(
            "/api/v1/boxscore",
            params={"game_pk": 777001},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.headers["content-type"].startswith("application/json"))
        line = response.json()["away_team"]["batting"][0]
        self.assertEqual(line["hits"], 3)
        self.assertEqual(line["singles"], 1)
        self.assertEqual(line["doubles"], 1)
        self.assertEqual(line["home_runs"], 1)

    def test_routes_are_in_openapi(self):
        paths = self.app.openapi()["paths"]
        self.assertIn("/api/v1/players/{player_id}", paths)
        self.assertIn("/api/v1/players/mlbam/{mlbam_id}/stats", paths)
        self.assertIn("/api/v1/stats/telemetry", paths)
        self.assertIn("/api/v1/boxscore", paths)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class EnforcementHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_seed_demo = db.SEED_DEMO
        self.original_app_ready = main._app_ready
        self.original_auto_sync = main.auto_sync_registry

        db.DB_PATH = Path(self.temp_dir.name) / "parking-test.db"
        db.SEED_DEMO = False
        main._app_ready = False
        main.auto_sync_registry = lambda: None

        db.init_db()
        db.seed_users()
        with db.connect() as con:
            con.executemany(
                """
                INSERT INTO enforcement_events
                (site_code, plate, verdict, verdict_message, unit, owner_name, inspector, location, memo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("APT1100", "12가3456", "OK", "정상 등록", "101-1203", "홍길동", "경비1조", "정문", "정상 확인", "2026-04-20 08:10:00"),
                    ("APT1100", "34나5678", "UNREGISTERED", "미등록 차량", None, None, "경비2조", "후문", "소화전 앞", "2026-04-21 09:20:00"),
                    ("APT1100", "77하9999", "BLOCKED", "차단 차량", "103-1502", "김차단", "경비1조", "지하 1층", "차단 확인", "2026-04-22 10:30:00"),
                ],
            )
            con.commit()

        self.client = TestClient(main.app)
        login = self.client.post(
            "/login",
            data={"site_code": "APT1100", "username": "admin", "password": "admin1234"},
            follow_redirects=False,
        )
        self.assertEqual(login.status_code, 302)

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_history_supports_pagination(self):
        first_page = self.client.get("/api/enforcement/history", params={"limit": 2})
        second_page = self.client.get("/api/enforcement/history", params={"limit": 2, "offset": 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertTrue(first_page.json()["has_more"])
        self.assertEqual(first_page.json()["next_offset"], 2)
        self.assertEqual([row["plate"] for row in first_page.json()["items"]], ["77하9999", "34나5678"])
        self.assertFalse(second_page.json()["has_more"])
        self.assertEqual([row["plate"] for row in second_page.json()["items"]], ["12가3456"])

    def test_history_filters_by_query_verdict_and_date_range(self):
        query = self.client.get("/api/enforcement/history", params={"q": "소화전"})
        verdict = self.client.get("/api/enforcement/history", params={"verdict": "BLOCKED"})
        date_range = self.client.get(
            "/api/enforcement/history",
            params={"date_from": "2026-04-21T00:00", "date_to": "2026-04-21T23:59"},
        )

        self.assertEqual(query.status_code, 200)
        self.assertEqual(verdict.status_code, 200)
        self.assertEqual(date_range.status_code, 200)
        self.assertEqual([row["plate"] for row in query.json()["items"]], ["34나5678"])
        self.assertEqual([row["plate"] for row in verdict.json()["items"]], ["77하9999"])
        self.assertEqual([row["plate"] for row in date_range.json()["items"]], ["34나5678"])


if __name__ == "__main__":
    unittest.main()

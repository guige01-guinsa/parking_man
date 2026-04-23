import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class RegistryCheckTests(unittest.TestCase):
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
                INSERT INTO vehicles
                (site_code, plate, unit, owner_name, phone, status, valid_from, valid_to, note, source_file, source_sheet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("APT1100", "12가3456", "101-1203", "홍길동", "010-1111-2222", "active", "2026-01-01", "2027-12-31", "정상", "sample.xlsx", "vehicles"),
                    ("APT1100", "77하3456", "103-1402", "김철수", "010-2222-3333", "temp", "2026-04-01", "2026-12-31", "임시", "sample.xlsx", "vehicles"),
                ],
            )

        self.client = TestClient(main.app)
        login = self.client.post("/login", data={"username": "admin", "password": "admin1234"}, follow_redirects=False)
        self.assertEqual(login.status_code, 302)

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_exact_check_returns_single_match(self):
        response = self.client.get("/api/registry/check", params={"plate": "12가3456"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["plate"], "12가3456")
        self.assertEqual(body["phone"], "010-1111-2222")
        self.assertEqual(body["match_mode"], "exact")
        self.assertEqual(body["match_count"], 1)

    def test_suffix_check_returns_multiple_matches(self):
        response = self.client.get("/api/registry/check", params={"plate": "3456"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["requested_plate"], "3456")
        self.assertEqual(body["match_mode"], "suffix")
        self.assertEqual(body["match_count"], 2)
        self.assertEqual(body["plate"], "12가3456")
        self.assertEqual(body["phone"], "010-1111-2222")
        self.assertEqual([item["plate"] for item in body["matches"]], ["12가3456", "77하3456"])
        self.assertEqual([item["phone"] for item in body["matches"]], ["010-1111-2222", "010-2222-3333"])

    def test_suffix_check_returns_unregistered_when_missing(self):
        response = self.client.get("/api/registry/check", params={"plate": "9999"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["requested_plate"], "9999")
        self.assertEqual(body["match_mode"], "suffix")
        self.assertEqual(body["match_count"], 0)
        self.assertEqual(body["verdict"], "UNREGISTERED")

    def test_search_returns_phone_field(self):
        response = self.client.get("/api/registry/search", params={"q": "홍길동"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["plate"], "12가3456")
        self.assertEqual(body[0]["phone"], "010-1111-2222")


if __name__ == "__main__":
    unittest.main()

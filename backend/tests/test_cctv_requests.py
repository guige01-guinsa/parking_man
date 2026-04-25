import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class CctvRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_seed_demo = db.SEED_DEMO
        self.original_app_ready = main._app_ready
        self.original_auto_sync = main.auto_sync_registry
        self.original_upload_dir = main.UPLOAD_DIR

        root = Path(self.temp_dir.name)
        db.DB_PATH = root / "parking-test.db"
        db.SEED_DEMO = False
        main._app_ready = False
        main.auto_sync_registry = lambda: None
        main.UPLOAD_DIR = root / "uploads"
        main.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        db.init_db()
        db.seed_users()
        with db.connect() as con:
            con.execute(
                "INSERT INTO users(username, pw_hash, role) VALUES (?, ?, ?)",
                ("teamlead", main.pbkdf2_hash("teamlead123"), "team_lead"),
            )
            con.commit()

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        main.UPLOAD_DIR = self.original_upload_dir
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def login(self, username: str, password: str) -> TestClient:
        client = TestClient(main.app)
        response = client.post("/login", data={"username": username, "password": password}, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        return client

    def create_request(self, client: TestClient):
        return client.post(
            "/api/cctv/requests",
            data={
                "location": "103동 1층 출입구",
                "search_start_time": "2026-04-25T12:20",
                "search_end_time": "2026-04-25T12:40",
                "content": "차량 이동 경로 확인",
            },
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )

    def test_user_can_create_cctv_request(self):
        client = self.login("cleaner", "cleaner1234")

        response = self.create_request(client)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["requester_username"], "cleaner")
        self.assertEqual(body["status"], "requested")
        self.assertEqual(body["work_weight"], 1)
        self.assertEqual(body["search_start_time"], "2026-04-25T12:20")
        self.assertEqual(body["search_end_time"], "2026-04-25T12:40")
        self.assertIn("/uploads/", body["photo_path"])

        listing = client.get("/api/cctv/requests")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

    def test_admin_can_assign_and_guard_can_see_assigned_request(self):
        cleaner = self.login("cleaner", "cleaner1234")
        created = self.create_request(cleaner)
        request_id = created.json()["id"]

        admin = self.login("admin", "admin1234")
        assigned = admin.patch(
            f"/api/cctv/requests/{request_id}",
            json={
                "assigned_to": "guard",
                "work_weight": 4,
                "instruction": "12:20~12:40 출입구 방향 확인",
                "status": "assigned",
            },
        )
        self.assertEqual(assigned.status_code, 200)
        body = assigned.json()
        self.assertEqual(body["assigned_to"], "guard")
        self.assertEqual(body["work_weight"], 4)
        self.assertEqual(body["instruction"], "12:20~12:40 출입구 방향 확인")

        guard = self.login("guard", "guard1234")
        listing = guard.get("/api/cctv/requests")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([row["id"] for row in listing.json()], [request_id])

    def test_non_admin_cannot_assign_request(self):
        cleaner = self.login("cleaner", "cleaner1234")
        created = self.create_request(cleaner)
        request_id = created.json()["id"]

        response = cleaner.patch(
            f"/api/cctv/requests/{request_id}",
            json={"assigned_to": "guard", "work_weight": 3, "status": "assigned"},
        )
        self.assertEqual(response.status_code, 403)

    def test_team_lead_can_assign_request(self):
        cleaner = self.login("cleaner", "cleaner1234")
        created = self.create_request(cleaner)
        request_id = created.json()["id"]

        team_lead = self.login("teamlead", "teamlead123")
        response = team_lead.patch(
            f"/api/cctv/requests/{request_id}",
            json={"assigned_to": "guard", "work_weight": 3, "status": "assigned"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["assigned_by"], "teamlead")

    def test_cctv_request_requires_required_fields(self):
        client = self.login("cleaner", "cleaner1234")
        response = client.post(
            "/api/cctv/requests",
            data={
                "location": "103동",
                "search_start_time": "2026-04-25T12:20",
                "search_end_time": "2026-04-25T12:40",
                "content": " ",
            },
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("요청 내용", response.json()["detail"])

    def test_cctv_request_requires_end_time(self):
        client = self.login("cleaner", "cleaner1234")
        response = client.post(
            "/api/cctv/requests",
            data={
                "location": "103동",
                "search_start_time": "2026-04-25T12:20",
                "content": "차량 이동 경로 확인",
            },
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("검색 끝 시간", response.json()["detail"])

    def test_cctv_request_rejects_end_time_before_start_time(self):
        client = self.login("cleaner", "cleaner1234")
        response = client.post(
            "/api/cctv/requests",
            data={
                "location": "103동",
                "search_start_time": "2026-04-25T12:40",
                "search_end_time": "2026-04-25T12:20",
                "content": "차량 이동 경로 확인",
            },
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("끝 시간", response.json()["detail"])

    def test_init_db_migrates_existing_single_search_time_column(self):
        with db.connect() as con:
            con.execute("DROP TABLE cctv_search_requests")
            con.execute(
                """
                CREATE TABLE cctv_search_requests (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  site_code TEXT NOT NULL,
                  requester_username TEXT NOT NULL,
                  photo_path TEXT NOT NULL,
                  location TEXT NOT NULL,
                  search_time TEXT NOT NULL,
                  content TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'requested',
                  work_weight INTEGER NOT NULL DEFAULT 1,
                  assigned_to TEXT,
                  instruction TEXT,
                  assigned_by TEXT,
                  assigned_at TEXT,
                  completed_at TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now')),
                  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            con.execute(
                """
                INSERT INTO cctv_search_requests
                (site_code, requester_username, photo_path, location, search_time, content)
                VALUES ('APT1100', 'viewer', '/uploads/old.jpg', '103동', '2026-04-25T12:30', '기존 요청')
                """
            )
            con.commit()

        db.init_db()

        with db.connect() as con:
            row = con.execute("SELECT search_start_time, search_end_time FROM cctv_search_requests").fetchone()
            columns = {item["name"] for item in con.execute("PRAGMA table_info(cctv_search_requests)").fetchall()}
        self.assertEqual(row["search_start_time"], "2026-04-25T12:30")
        self.assertEqual(row["search_end_time"], "2026-04-25T12:30")
        self.assertNotIn("search_time", columns)


if __name__ == "__main__":
    unittest.main()

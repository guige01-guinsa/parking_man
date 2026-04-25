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
                "search_time": "2026-04-25T12:30",
                "content": "차량 이동 경로 확인",
            },
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )

    def test_user_can_create_cctv_request(self):
        client = self.login("viewer", "viewer1234")

        response = self.create_request(client)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["requester_username"], "viewer")
        self.assertEqual(body["status"], "requested")
        self.assertEqual(body["work_weight"], 1)
        self.assertIn("/uploads/", body["photo_path"])

        listing = client.get("/api/cctv/requests")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()), 1)

    def test_admin_can_assign_and_guard_can_see_assigned_request(self):
        viewer = self.login("viewer", "viewer1234")
        created = self.create_request(viewer)
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
        viewer = self.login("viewer", "viewer1234")
        created = self.create_request(viewer)
        request_id = created.json()["id"]

        response = viewer.patch(
            f"/api/cctv/requests/{request_id}",
            json={"assigned_to": "guard", "work_weight": 3, "status": "assigned"},
        )
        self.assertEqual(response.status_code, 403)

    def test_cctv_request_requires_required_fields(self):
        client = self.login("viewer", "viewer1234")
        response = client.post(
            "/api/cctv/requests",
            data={"location": "103동", "search_time": "2026-04-25T12:30", "content": " "},
            files={"photo": ("request.jpg", b"fake-image", "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("요청 내용", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class UserManagementTests(unittest.TestCase):
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

        self.client = TestClient(main.app)
        self.login(self.client, "admin", "admin1234")

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def login(self, client: TestClient, username: str, password: str):
        return client.post("/login", data={"username": username, "password": password}, follow_redirects=False)

    def test_admin_can_create_update_and_delete_user(self):
        created = self.client.post(
            "/api/users",
            json={"username": "guard02", "password": "guardpass123", "role": "guard"},
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["username"], "guard02")
        self.assertEqual(created.json()["role"], "guard")

        listing = self.client.get("/api/users")
        self.assertEqual(listing.status_code, 200)
        self.assertIn("guard02", [row["username"] for row in listing.json()])

        updated = self.client.patch(
            "/api/users/guard02",
            json={"role": "viewer", "password": "viewerpass123"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["role"], "viewer")

        relogin = TestClient(main.app)
        bad_login = self.login(relogin, "guard02", "guardpass123")
        self.assertEqual(bad_login.status_code, 401)
        good_login = self.login(relogin, "guard02", "viewerpass123")
        self.assertEqual(good_login.status_code, 302)

        deleted = self.client.delete("/api/users/guard02")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])

    def test_guard_cannot_access_user_management_api(self):
        guard_client = TestClient(main.app)
        login = self.login(guard_client, "guard", "guard1234")
        self.assertEqual(login.status_code, 302)

        response = guard_client.get("/api/users")
        self.assertEqual(response.status_code, 403)

    def test_cannot_delete_current_user(self):
        response = self.client.delete("/api/users/admin")
        self.assertEqual(response.status_code, 400)
        self.assertIn("삭제할 수 없습니다", response.json()["detail"])

    def test_duplicate_username_is_rejected(self):
        response = self.client.post(
            "/api/users",
            json={"username": "admin", "password": "admin1234", "role": "admin"},
        )
        self.assertEqual(response.status_code, 409)

    def test_login_failure_renders_friendly_message(self):
        relogin = TestClient(main.app)
        response = self.login(relogin, "admin", "wrong-password")

        self.assertEqual(response.status_code, 401)
        self.assertIn("로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해 주세요.", response.text)
        self.assertIn("주차 관리 시스템에 오신 것을 환영합니다.", response.text)
        self.assertIn('value="admin"', response.text)


if __name__ == "__main__":
    unittest.main()

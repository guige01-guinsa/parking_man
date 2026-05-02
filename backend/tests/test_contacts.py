import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class ContactManagementTests(unittest.TestCase):
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

        self.admin = TestClient(main.app)
        self.login(self.admin, "admin", "admin1234")

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def login(self, client: TestClient, username: str, password: str):
        return client.post("/login", data={"username": username, "password": password}, follow_redirects=False)

    def test_admin_can_create_update_delete_and_user_can_view_contacts(self):
        created = self.admin.post(
            "/api/contacts",
            json={
                "category": "public",
                "name": "구청 교통과",
                "phone": "051-123-4567",
                "duty": "불법주차 민원",
                "memo": "평일 주간",
                "is_favorite": True,
                "sort_order": 2,
            },
        )
        self.assertEqual(created.status_code, 200)
        contact_id = created.json()["id"]
        self.assertEqual(created.json()["category_label"], "공공기관")
        self.assertTrue(created.json()["is_favorite"])

        guard = TestClient(main.app)
        self.assertEqual(self.login(guard, "guard", "guard1234").status_code, 302)
        listing = guard.get("/api/contacts", params={"q": "교통"})
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([row["name"] for row in listing.json()], ["구청 교통과"])

        blocked = guard.post(
            "/api/contacts",
            json={"category": "vendor", "name": "견인업체", "phone": "010-0000-0000"},
        )
        self.assertEqual(blocked.status_code, 403)

        updated = self.admin.patch(
            f"/api/contacts/{contact_id}",
            json={
                "category": "vendor",
                "name": "협력 견인업체",
                "phone": "010-2222-3333",
                "duty": "견인",
                "memo": "",
                "is_favorite": False,
                "sort_order": 1,
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["category"], "vendor")
        self.assertFalse(updated.json()["is_favorite"])

        deleted = self.admin.delete(f"/api/contacts/{contact_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()["deleted"])

        empty = self.admin.get("/api/contacts")
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), [])

    def test_contact_validation_rejects_unknown_category(self):
        response = self.admin.post(
            "/api/contacts",
            json={"category": "etc", "name": "테스트", "phone": "010-0000-0000"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()

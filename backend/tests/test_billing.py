import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_seed_demo = db.SEED_DEMO
        self.original_app_ready = main._app_ready
        self.original_auto_sync = main.auto_sync_registry
        self.original_billing_provider = main.BILLING_PROVIDER
        self.original_billing_enforcement = main.BILLING_ENFORCEMENT_ENABLED
        self.original_sales_contact_url = main.SALES_CONTACT_URL

        db.DB_PATH = Path(self.temp_dir.name) / "parking-test.db"
        db.SEED_DEMO = False
        main._app_ready = False
        main.auto_sync_registry = lambda: None
        main.BILLING_PROVIDER = "manual"
        main.BILLING_ENFORCEMENT_ENABLED = False
        main.SALES_CONTACT_URL = ""

        db.init_db()
        db.seed_users()

        self.client = TestClient(main.app)
        self.login(self.client, "admin", "admin1234")

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        main.BILLING_PROVIDER = self.original_billing_provider
        main.BILLING_ENFORCEMENT_ENABLED = self.original_billing_enforcement
        main.SALES_CONTACT_URL = self.original_sales_contact_url
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def login(self, client: TestClient, username: str, password: str):
        return client.post("/login", data={"username": username, "password": password}, follow_redirects=False)

    def test_admin_can_view_billing_status(self):
        response = self.client.get("/api/billing/status")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["billing"]["plan"], "trial")
        self.assertEqual(body["billing"]["status"], "trialing")
        self.assertEqual(body["current_plan"]["users_limit"], 3)
        self.assertGreaterEqual(body["usage"]["users"], 3)
        self.assertEqual([plan["code"] for plan in body["plans"]], ["starter", "standard", "pro"])

    def test_admin_can_create_upgrade_inquiry(self):
        response = self.client.post(
            "/api/billing/inquiries",
            json={
                "requested_plan": "standard",
                "contact_name": "관리소장",
                "contact_phone": "010-0000-0000",
                "message": "2개 단지 사용 상담 요청",
            },
        )

        self.assertEqual(response.status_code, 200)
        inquiries = response.json()["latest_inquiries"]
        self.assertEqual(inquiries[0]["requested_plan"], "standard")
        self.assertEqual(inquiries[0]["contact_name"], "관리소장")

        with db.connect() as con:
            row = con.execute("SELECT requested_plan, contact_phone FROM billing_inquiries").fetchone()
        self.assertEqual(row["requested_plan"], "standard")
        self.assertEqual(row["contact_phone"], "010-0000-0000")

    def test_non_admin_cannot_access_billing_api(self):
        guard_client = TestClient(main.app)
        login = self.login(guard_client, "guard", "guard1234")
        self.assertEqual(login.status_code, 302)

        response = guard_client.get("/api/billing/status")
        self.assertEqual(response.status_code, 403)

    def test_new_site_gets_trial_billing_row(self):
        created = self.client.post(
            "/api/sites",
            json={
                "site_code": "APT5500",
                "name": "수익 테스트 단지",
                "admin_username": "admin5500",
                "admin_password": "admin5500123",
            },
        )
        self.assertEqual(created.status_code, 200)

        with db.connect() as con:
            row = con.execute("SELECT plan, status FROM site_billing WHERE site_code = ?", ("APT5500",)).fetchone()
        self.assertEqual(row["plan"], "trial")
        self.assertEqual(row["status"], "trialing")

    def test_billing_enforcement_can_block_user_over_limit(self):
        main.BILLING_ENFORCEMENT_ENABLED = True
        response = self.client.post(
            "/api/users",
            json={"username": "overlimit", "password": "password123", "role": "guard"},
        )

        self.assertEqual(response.status_code, 402)
        self.assertIn("요금제", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

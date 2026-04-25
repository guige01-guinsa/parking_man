import tempfile
import unittest
import base64
import json
from pathlib import Path
from unittest.mock import patch

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
        self.original_google_play_package = main.GOOGLE_PLAY_PACKAGE_NAME
        self.original_google_play_service_account_json = main.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
        self.original_google_play_service_account_file = main.GOOGLE_PLAY_SERVICE_ACCOUNT_FILE
        self.original_google_play_auto_acknowledge = main.GOOGLE_PLAY_AUTO_ACKNOWLEDGE
        self.original_google_play_rtdn_token = main.GOOGLE_PLAY_RTDN_TOKEN
        self.original_google_play_product_ids = dict(main.GOOGLE_PLAY_PRODUCT_IDS)

        db.DB_PATH = Path(self.temp_dir.name) / "parking-test.db"
        db.SEED_DEMO = False
        main._app_ready = False
        main.auto_sync_registry = lambda: None
        main.BILLING_PROVIDER = "manual"
        main.BILLING_ENFORCEMENT_ENABLED = False
        main.SALES_CONTACT_URL = ""
        main.GOOGLE_PLAY_PACKAGE_NAME = "com.parkingmanagement.app"
        main.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON = ""
        main.GOOGLE_PLAY_SERVICE_ACCOUNT_FILE = ""
        main.GOOGLE_PLAY_AUTO_ACKNOWLEDGE = True
        main.GOOGLE_PLAY_RTDN_TOKEN = ""
        main.GOOGLE_PLAY_PRODUCT_IDS = {
            "starter": "parking_starter_monthly",
            "standard": "parking_standard_monthly",
            "pro": "parking_pro_monthly",
        }

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
        main.GOOGLE_PLAY_PACKAGE_NAME = self.original_google_play_package
        main.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON = self.original_google_play_service_account_json
        main.GOOGLE_PLAY_SERVICE_ACCOUNT_FILE = self.original_google_play_service_account_file
        main.GOOGLE_PLAY_AUTO_ACKNOWLEDGE = self.original_google_play_auto_acknowledge
        main.GOOGLE_PLAY_RTDN_TOKEN = self.original_google_play_rtdn_token
        main.GOOGLE_PLAY_PRODUCT_IDS = self.original_google_play_product_ids
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

    def test_google_play_status_exposes_product_ids(self):
        main.BILLING_PROVIDER = "google_play"
        response = self.client.get("/api/billing/status")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["play_billing_required"])
        self.assertEqual(body["google_play"]["products"]["standard"], "parking_standard_monthly")
        self.assertEqual(
            [plan["google_play_product_id"] for plan in body["plans"]],
            ["parking_starter_monthly", "parking_standard_monthly", "parking_pro_monthly"],
        )

    def test_google_play_verify_updates_site_plan(self):
        main.BILLING_PROVIDER = "google_play"
        subscription = {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_PENDING",
            "latestOrderId": "GPA.1234-5678-9012-34567",
            "lineItems": [
                {
                    "productId": "parking_standard_monthly",
                    "expiryTime": "2099-01-01T00:00:00Z",
                }
            ],
        }

        with patch.object(main, "fetch_google_play_subscription", return_value=subscription), patch.object(
            main, "acknowledge_google_play_subscription", return_value=True
        ):
            response = self.client.post(
                "/api/billing/google-play/verify",
                json={"product_id": "parking_standard_monthly", "purchase_token": "token-123"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["entitlement_active"])
        self.assertEqual(body["plan"], "standard")
        self.assertEqual(body["billing_status"]["billing"]["plan"], "standard")
        self.assertEqual(body["billing_status"]["billing"]["status"], "active")

        with db.connect() as con:
            billing = con.execute("SELECT plan, status, payment_provider FROM site_billing").fetchone()
            purchase = con.execute("SELECT product_id, plan, acknowledgement_state FROM google_play_purchases").fetchone()
        self.assertEqual(billing["plan"], "standard")
        self.assertEqual(billing["payment_provider"], "google_play")
        self.assertEqual(purchase["product_id"], "parking_standard_monthly")
        self.assertEqual(purchase["acknowledgement_state"], "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED")

    def test_google_play_rtdn_revalidates_known_purchase_token(self):
        main.BILLING_PROVIDER = "google_play"
        main.GOOGLE_PLAY_RTDN_TOKEN = "secret-token"
        with db.connect() as con:
            con.execute(
                """
                INSERT INTO google_play_purchases
                (site_code, username, package_name, product_id, plan, purchase_token)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "APT1100",
                    "admin",
                    "com.parkingmanagement.app",
                    "parking_standard_monthly",
                    "standard",
                    "known-token",
                ),
            )
            con.commit()

        notification = {
            "version": "1.0",
            "packageName": "com.parkingmanagement.app",
            "eventTimeMillis": "4070908800000",
            "subscriptionNotification": {
                "version": "1.0",
                "notificationType": 4,
                "purchaseToken": "known-token",
                "subscriptionId": "parking_standard_monthly",
            },
        }
        encoded = base64.b64encode(json.dumps(notification).encode("utf-8")).decode("ascii")
        subscription = {
            "subscriptionState": "SUBSCRIPTION_STATE_CANCELED",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
            "latestOrderId": "GPA.9999",
            "lineItems": [
                {
                    "productId": "parking_standard_monthly",
                    "expiryTime": "2099-01-01T00:00:00Z",
                }
            ],
        }

        with patch.object(main, "fetch_google_play_subscription", return_value=subscription):
            response = self.client.post(
                "/api/billing/google-play/rtdn?token=secret-token",
                json={"message": {"data": encoded}},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["billing_status"]["billing"]["plan"], "standard")


if __name__ == "__main__":
    unittest.main()

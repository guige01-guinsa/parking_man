import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import db, main
from app.ocr import OCRScanResult
from app.ocr_learning import get_learning_candidates, normalize_ocr_key, parse_candidates_json, record_ocr_feedback


class OCRLearningTests(unittest.TestCase):
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
                    ("APT1100", "12가3456", "101-1203", "홍길동", "010-1111-2222", "active", "2026-01-01", "2027-12-31", "상시 등록", "test.xlsx", "vehicles"),
                    ("APT1100", "12가3458", "102-803", "김영희", "010-2222-3333", "active", "2026-01-01", "2027-12-31", "상시 등록", "test.xlsx", "vehicles"),
                ],
            )
            con.commit()
        self.client = TestClient(main.app)
        login = self.client.post("/login", data={"username": "admin", "password": "admin1234"}, follow_redirects=False)
        self.assertEqual(login.status_code, 302)

    def tearDown(self):
        main.auto_sync_registry = self.original_auto_sync
        main._app_ready = self.original_app_ready
        db.SEED_DEMO = self.original_seed_demo
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_normalize_ocr_key(self):
        self.assertEqual(normalize_ocr_key(" I2-가 34S6 "), "I2가34S6")

    def test_parse_candidates_json(self):
        self.assertEqual(parse_candidates_json('["12가 3456", "12가3456", null, ""]'), ["12가3456"])

    def test_learning_candidates_prefer_corrected_plate(self):
        record_ocr_feedback(
            site_code="APT1100",
            raw_ocr_text="번호판: I2가34S6",
            suggested_plate="12가3458",
            corrected_plate="12가3456",
            candidates=["12가3458", "12가3456"],
        )

        learned, boosts = get_learning_candidates("APT1100", "번호판: I2가34S6", ["12가3458"])
        self.assertGreater(boosts.get("12가3456", 0.0), boosts.get("12가3458", 0.0))
        self.assertEqual(learned[0], "12가3456")

    def test_best_candidate_uses_learning_feedback(self):
        record_ocr_feedback(
            site_code="APT1100",
            raw_ocr_text="번호판: I2가34S6",
            suggested_plate="12가3458",
            corrected_plate="12가3456",
            candidates=["12가3458", "12가3456"],
        )

        best_plate, ordered = main.choose_best_scan_candidate("APT1100", "번호판: I2가34S6", None, ["12가3458"])
        self.assertEqual(best_plate, "12가3456")
        self.assertEqual(ordered[0], "12가3456")

    def test_scan_endpoint_uses_client_ocr_without_tesseract(self):
        original_scan_plate_image = main.scan_plate_image

        def fail_if_called(_image_bytes):
            raise AssertionError("server OCR should not run when client OCR produced a candidate")

        main.scan_plate_image = fail_if_called
        try:
            response = self.client.post(
                "/api/ocr/scan",
                data={
                    "client_ocr_provider": "android-mlkit",
                    "client_ocr_raw_text": "[android-korean] 12 가 3456",
                    "client_ocr_candidates": '["12가3456"]',
                },
                files={"photo": ("plate.jpg", io.BytesIO(b"client-ocr-first"), "image/jpeg")},
            )
        finally:
            main.scan_plate_image = original_scan_plate_image

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["provider"], "android-mlkit")
        self.assertFalse(body["server_ocr_used"])
        self.assertEqual(body["best_plate"], "12가3456")
        self.assertEqual(body["match"]["verdict"], "OK")

    def test_scan_endpoint_falls_back_to_server_ocr_without_client_candidate(self):
        original_scan_plate_image = main.scan_plate_image

        def fake_scan(_image_bytes):
            return OCRScanResult(provider="tesseract", raw_text="번호판 12가3456", candidates=["12가3456"])

        main.scan_plate_image = fake_scan
        try:
            response = self.client.post(
                "/api/ocr/scan",
                files={"photo": ("plate.jpg", io.BytesIO(b"needs-server-ocr"), "image/jpeg")},
            )
        finally:
            main.scan_plate_image = original_scan_plate_image

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["server_ocr_used"])
        self.assertEqual(body["provider"], "tesseract")
        self.assertEqual(body["best_plate"], "12가3456")


if __name__ == "__main__":
    unittest.main()

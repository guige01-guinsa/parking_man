import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.excel_import import (
    build_safe_excel_filename,
    is_temporary_excel_filename,
    list_excel_files,
    resolve_header_field,
    store_registry_upload,
)
from app.plates import evaluate_vehicle_row, extract_plate_candidates, normalize_plate, normalize_status


class PlateTests(unittest.TestCase):
    def test_normalize_plate_removes_spaces(self):
        self.assertEqual(normalize_plate(" 12가 3456 "), "12가3456")

    def test_extract_plate_candidates(self):
        text = "차량번호는 123다4567 입니다."
        self.assertEqual(extract_plate_candidates(text), ["123다4567"])

    def test_extract_plate_candidates_repairs_digit_confusion(self):
        text = "번호판: I2가34S6"
        self.assertIn("12가3456", extract_plate_candidates(text))

    def test_normalize_plate_prefers_repaired_candidate(self):
        self.assertEqual(normalize_plate("123허34B6"), "123허3486")

    def test_status_aliases(self):
        self.assertEqual(normalize_status("차단"), "blocked")
        self.assertEqual(normalize_status("임시"), "temp")

    def test_evaluate_unregistered(self):
        verdict = evaluate_vehicle_row(None, today=date(2026, 4, 23))
        self.assertEqual(verdict.verdict, "UNREGISTERED")

    def test_evaluate_expired(self):
        verdict = evaluate_vehicle_row(
            {"status": "active", "valid_to": "2026-04-01", "unit": "101-1203", "owner_name": "홍길동"},
            today=date(2026, 4, 23),
        )
        self.assertEqual(verdict.verdict, "EXPIRED")


class ExcelHeaderTests(unittest.TestCase):
    def test_resolve_korean_headers(self):
        self.assertEqual(resolve_header_field("차량번호"), "plate")
        self.assertEqual(resolve_header_field("동호수"), "unit")
        self.assertEqual(resolve_header_field("차주"), "owner_name")

    def test_build_safe_excel_filename(self):
        self.assertEqual(build_safe_excel_filename("../차량 목록.xlsx"), "차량-목록.xlsx")

    def test_store_registry_upload_rejects_invalid_suffix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                store_registry_upload(Path(temp_dir), "registry.csv", b"bad-data")

    def test_store_registry_upload_rejects_temporary_excel_lock_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "임시 잠금 파일"):
                store_registry_upload(Path(temp_dir), "~$registry.xlsx", b"bad-data")

    def test_list_excel_files_ignores_temporary_lock_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "registry.xlsx").write_bytes(b"real")
            (root / "~$registry.xlsx").write_bytes(b"lock")
            self.assertEqual([path.name for path in list_excel_files(root)], ["registry.xlsx"])

    def test_is_temporary_excel_filename(self):
        self.assertTrue(is_temporary_excel_filename("~$registry.xlsx"))
        self.assertFalse(is_temporary_excel_filename("registry.xlsx"))


if __name__ == "__main__":
    unittest.main()

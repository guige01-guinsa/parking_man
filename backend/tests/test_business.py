import unittest
from datetime import date

from app.excel_import import resolve_header_field
from app.plates import evaluate_vehicle_row, extract_plate_candidates, normalize_plate, normalize_status


class PlateTests(unittest.TestCase):
    def test_normalize_plate_removes_spaces(self):
        self.assertEqual(normalize_plate(" 12가 3456 "), "12가3456")

    def test_extract_plate_candidates(self):
        text = "차량번호는 123다4567 입니다."
        self.assertEqual(extract_plate_candidates(text), ["123다4567"])

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


if __name__ == "__main__":
    unittest.main()


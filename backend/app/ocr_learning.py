from __future__ import annotations

import json
import re
from typing import Any

from .db import connect
from .plates import normalize_plate


def normalize_ocr_key(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    compact = re.sub(r"[\s\-_/.:]", "", text)
    compact = re.sub(r"[^\dA-Z가-힣|!$]", "", compact)
    return compact[:120]


def parse_candidates_json(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in loaded:
        plate = normalize_plate(item)
        if not plate or plate in seen:
            continue
        seen.add(plate)
        normalized.append(plate)
    return normalized


def dump_candidates_json(candidates: list[str]) -> str:
    return json.dumps(candidates, ensure_ascii=False)


def record_ocr_feedback(
    site_code: str,
    raw_ocr_text: str | None,
    suggested_plate: str | None,
    corrected_plate: str | None,
    candidates: list[str] | None = None,
    photo_path: str | None = None,
) -> None:
    corrected = normalize_plate(corrected_plate)
    suggested = normalize_plate(suggested_plate)
    raw_key = normalize_ocr_key(raw_ocr_text)

    normalized_candidates: list[str] = []
    seen: set[str] = set()
    for item in candidates or []:
        plate = normalize_plate(item)
        if not plate or plate in seen:
            continue
        seen.add(plate)
        normalized_candidates.append(plate)

    if not corrected:
        return
    if not raw_key and not suggested and not normalized_candidates:
        return

    with connect() as con:
        con.execute(
            """
            INSERT INTO ocr_feedback
            (site_code, raw_key, raw_ocr_text, suggested_plate, corrected_plate, accepted, candidates_json, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                site_code,
                raw_key or None,
                raw_ocr_text,
                suggested or None,
                corrected,
                1 if suggested and suggested == corrected else 0,
                dump_candidates_json(normalized_candidates),
                photo_path,
            ),
        )
        con.commit()


def get_learning_candidates(site_code: str, raw_ocr_text: str | None, scanned_candidates: list[str]) -> tuple[list[str], dict[str, float]]:
    normalized_scanned: list[str] = []
    seen: set[str] = set()
    for item in scanned_candidates:
        plate = normalize_plate(item)
        if not plate or plate in seen:
            continue
        seen.add(plate)
        normalized_scanned.append(plate)

    boosts: dict[str, float] = {}
    raw_key = normalize_ocr_key(raw_ocr_text)

    with connect() as con:
        if raw_key:
            rows = con.execute(
                """
                SELECT corrected_plate, SUM(CASE WHEN accepted = 1 THEN 3 ELSE 5 END) AS weight
                FROM ocr_feedback
                WHERE site_code = ? AND raw_key = ?
                GROUP BY corrected_plate
                ORDER BY weight DESC, MAX(id) DESC
                LIMIT 5
                """,
                (site_code, raw_key),
            ).fetchall()
            for row in rows:
                plate = normalize_plate(row["corrected_plate"])
                if plate:
                    boosts[plate] = boosts.get(plate, 0.0) + float(row["weight"] or 0.0) + 40.0

        for candidate in normalized_scanned[:5]:
            rows = con.execute(
                """
                SELECT corrected_plate, SUM(CASE WHEN accepted = 1 THEN 2 ELSE 6 END) AS weight
                FROM ocr_feedback
                WHERE site_code = ? AND suggested_plate = ?
                GROUP BY corrected_plate
                ORDER BY weight DESC, MAX(id) DESC
                LIMIT 4
                """,
                (site_code, candidate),
            ).fetchall()
            for row in rows:
                plate = normalize_plate(row["corrected_plate"])
                if plate:
                    boosts[plate] = boosts.get(plate, 0.0) + float(row["weight"] or 0.0)

    ranked = sorted(boosts.items(), key=lambda item: item[1], reverse=True)
    return [plate for plate, _ in ranked], boosts


def get_learning_status(site_code: str) -> dict[str, Any]:
    with connect() as con:
        counts = con.execute(
            """
            SELECT
              COUNT(*) AS total_feedback,
              SUM(CASE WHEN accepted = 0 THEN 1 ELSE 0 END) AS corrected_feedback
            FROM ocr_feedback
            WHERE site_code = ?
            """,
            (site_code,),
        ).fetchone()
        last_item = con.execute(
            """
            SELECT corrected_plate, suggested_plate, accepted, created_at
            FROM ocr_feedback
            WHERE site_code = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (site_code,),
        ).fetchone()

    return {
        "total_feedback": int(counts["total_feedback"] or 0),
        "corrected_feedback": int(counts["corrected_feedback"] or 0),
        "last_feedback": dict(last_item) if last_item else None,
    }

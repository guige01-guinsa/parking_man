import re
from dataclasses import dataclass
from datetime import date
from typing import Any

PLATE_PATTERN = re.compile(r"\d{2,3}[가-힣]\d{4}")

STATUS_ALIASES = {
    "active": "active",
    "normal": "active",
    "registered": "active",
    "정상": "active",
    "등록": "active",
    "상시": "active",
    "blocked": "blocked",
    "blacklist": "blocked",
    "ban": "blocked",
    "차단": "blocked",
    "블랙": "blocked",
    "temp": "temp",
    "temporary": "temp",
    "guest": "temp",
    "visitor": "temp",
    "임시": "temp",
    "방문": "temp",
}


@dataclass(slots=True)
class PlateVerdict:
    verdict: str
    message: str
    unit: str | None = None
    owner_name: str | None = None
    status: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


def normalize_plate(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    compact = re.sub(r"[\s\-_/.:]", "", text)
    compact = re.sub(r"[^\dA-Z가-힣]", "", compact)
    matches = PLATE_PATTERN.findall(compact)
    if matches:
        return matches[0]
    return compact


def extract_plate_candidates(value: Any) -> list[str]:
    text = str(value or "")
    candidates: list[str] = []
    seen: set[str] = set()
    variants = [
        text,
        re.sub(r"\s+", "", text),
        re.sub(r"[\s\-_/.:]", "", text),
    ]
    for variant in variants:
        compact = re.sub(r"[^\dA-Z가-힣]", "", variant.upper())
        for match in PLATE_PATTERN.findall(compact):
            if match not in seen:
                seen.add(match)
                candidates.append(match)
    normalized = normalize_plate(text)
    if PLATE_PATTERN.fullmatch(normalized) and normalized not in seen:
        candidates.append(normalized)
    return candidates


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    compact = re.sub(r"\s+", "", text)
    return STATUS_ALIASES.get(compact, STATUS_ALIASES.get(text, "active"))


def parse_iso_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def evaluate_vehicle_row(row: dict[str, Any] | None, today: date | None = None) -> PlateVerdict:
    if not row:
        return PlateVerdict(verdict="UNREGISTERED", message="미등록 차량")

    today = today or date.today()
    status = normalize_status(row.get("status"))
    valid_from = str(row.get("valid_from") or "").strip() or None
    valid_to = str(row.get("valid_to") or "").strip() or None

    if status == "blocked":
        return PlateVerdict(
            verdict="BLOCKED",
            message="차단 차량",
            unit=row.get("unit"),
            owner_name=row.get("owner_name"),
            status=status,
            valid_from=valid_from,
            valid_to=valid_to,
        )

    start_date = parse_iso_date(valid_from)
    end_date = parse_iso_date(valid_to)

    if start_date and today < start_date:
        return PlateVerdict(
            verdict="TEMP",
            message="등록 시작 전",
            unit=row.get("unit"),
            owner_name=row.get("owner_name"),
            status=status,
            valid_from=valid_from,
            valid_to=valid_to,
        )

    if end_date and today > end_date:
        return PlateVerdict(
            verdict="EXPIRED",
            message="등록 기간 만료",
            unit=row.get("unit"),
            owner_name=row.get("owner_name"),
            status=status,
            valid_from=valid_from,
            valid_to=valid_to,
        )

    if status == "temp":
        return PlateVerdict(
            verdict="TEMP",
            message="임시 등록 차량",
            unit=row.get("unit"),
            owner_name=row.get("owner_name"),
            status=status,
            valid_from=valid_from,
            valid_to=valid_to,
        )

    return PlateVerdict(
        verdict="OK",
        message="정상 등록 차량",
        unit=row.get("unit"),
        owner_name=row.get("owner_name"),
        status=status,
        valid_from=valid_from,
        valid_to=valid_to,
    )


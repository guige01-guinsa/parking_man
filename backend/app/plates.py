import re
from dataclasses import dataclass
from datetime import date
from typing import Any

PLATE_MIDDLE_CHARS = "가나다라마바사아자거너더러머버서어저고노도로모보소오조구누두루무부수우주바사자배허하호"
PLATE_PATTERN = re.compile(rf"\d{{2,3}}[{re.escape(PLATE_MIDDLE_CHARS)}]\d{{4}}")
PLATE_MIDDLE_SET = set(PLATE_MIDDLE_CHARS)

DIGIT_SIMILAR_MAP = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "U": "0",
    "I": "1",
    "L": "1",
    "|": "1",
    "!": "1",
    "Z": "2",
    "A": "4",
    "S": "5",
    "$": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}

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
    candidates = extract_plate_candidates(text)
    if candidates:
        return candidates[0]
    compact = compact_plate_text(text)
    matches = PLATE_PATTERN.findall(compact)
    if matches:
        return matches[0]
    return compact


def compact_plate_text(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    compact = re.sub(r"[\s\-_/.:]", "", text)
    return re.sub(r"[^\dA-Z가-힣|!$]", "", compact)


def _repair_digit_fragment(fragment: str) -> tuple[str, int] | None:
    digits: list[str] = []
    repairs = 0
    for char in fragment:
        if char.isdigit():
            digits.append(char)
            continue
        mapped = DIGIT_SIMILAR_MAP.get(char)
        if not mapped:
            return None
        digits.append(mapped)
        repairs += 1
    return "".join(digits), repairs


def _candidate_from_window(window: str) -> tuple[str, int] | None:
    expected_len = len(window)
    middle_index = expected_len - 5
    if middle_index not in {2, 3}:
        return None

    middle_char = window[middle_index]
    if middle_char not in PLATE_MIDDLE_SET:
        return None

    head = _repair_digit_fragment(window[:middle_index])
    tail = _repair_digit_fragment(window[middle_index + 1 :])
    if not head or not tail:
        return None

    candidate = f"{head[0]}{middle_char}{tail[0]}"
    if not PLATE_PATTERN.fullmatch(candidate):
        return None
    return candidate, head[1] + tail[1]


def extract_plate_candidates(value: Any) -> list[str]:
    text = str(value or "")
    ranked: dict[str, tuple[int, int, int]] = {}
    boundary_sensitive = set("0123456789") | set(DIGIT_SIMILAR_MAP) | PLATE_MIDDLE_SET
    variants = [
        text,
        re.sub(r"\s+", "", text),
        re.sub(r"[\s\-_/.:]", "", text),
    ]

    def add_candidate(candidate: str, repairs: int, exact_match: bool) -> None:
        current = ranked.get(candidate)
        score_tuple = (1 if exact_match else 0, -repairs, 1)
        if current is None:
            ranked[candidate] = score_tuple
            return
        ranked[candidate] = (
            max(current[0], score_tuple[0]),
            max(current[1], score_tuple[1]),
            current[2] + 1,
        )

    for variant in variants:
        compact = compact_plate_text(variant)
        for match in PLATE_PATTERN.findall(compact):
            add_candidate(match, repairs=0, exact_match=True)

        for window_size in (7, 8):
            if len(compact) < window_size:
                continue
            for index in range(len(compact) - window_size + 1):
                if index > 0 and compact[index - 1] in boundary_sensitive:
                    continue
                window_end = index + window_size
                if window_end < len(compact) and compact[window_end] in boundary_sensitive:
                    continue
                repaired = _candidate_from_window(compact[index : index + window_size])
                if repaired:
                    add_candidate(repaired[0], repairs=repaired[1], exact_match=False)

    sorted_items = sorted(
        ranked.items(),
        key=lambda item: (item[1][0], item[1][1], item[1][2], len(item[0])),
        reverse=True,
    )
    return [item[0] for item in sorted_items]


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


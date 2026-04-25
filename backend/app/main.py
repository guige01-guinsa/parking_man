from __future__ import annotations

import os
import re
import shutil
import threading
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .auth import COOKIE_NAME, make_session, pbkdf2_hash, pbkdf2_verify, read_session, require_role
from .db import DEFAULT_SITE_CODE, DEFAULT_SITE_NAME, connect, init_db, maybe_seed_demo, normalize_site_code, seed_users
from .excel_import import describe_excel_files, store_registry_upload, sync_registry_from_dir
from .ocr_learning import get_learning_candidates, get_learning_status, parse_candidates_json, record_ocr_feedback
from .ocr import scan_plate_image
from .plates import PlateVerdict, evaluate_vehicle_row, normalize_plate

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path(os.getenv("PARKING_UPLOAD_DIR", str(BASE_DIR / "uploads")))
IMPORT_DIR = Path(os.getenv("PARKING_IMPORT_DIR", str(BASE_DIR.parent / "imports")))
APP_TITLE = os.getenv("PARKING_APP_TITLE", "아파트 주차단속 시스템")
ROOT_PATH = os.getenv("PARKING_ROOT_PATH", "").strip()
LOCAL_LOGIN_ENABLED = os.getenv("PARKING_LOCAL_LOGIN_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
SUPPORT_KAKAO_URL = os.getenv("PARKING_SUPPORT_KAKAO_URL", "").strip()
SUPPORT_KAKAO_LABEL = os.getenv("PARKING_SUPPORT_KAKAO_LABEL", "카카오톡 문의").strip() or "카카오톡 문의"

if ROOT_PATH and not ROOT_PATH.startswith("/"):
    ROOT_PATH = f"/{ROOT_PATH}"
ROOT_PATH = ROOT_PATH.rstrip("/")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMPORT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=APP_TITLE, version="2.0.0", root_path=ROOT_PATH)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
_ready_lock = threading.Lock()
_app_ready = False
LOGIN_INVALID_MESSAGE = "로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해 주세요."
LOGIN_FORMAT_MESSAGE = "아이디 형식을 다시 확인해 주세요. 영문 소문자와 숫자를 사용해 입력할 수 있습니다."
LOGIN_SITE_FORMAT_MESSAGE = "아파트 코드는 영문, 숫자, 하이픈(-), 밑줄(_)만 사용해 2~32자로 입력해 주세요."


class CheckMatch(BaseModel):
    plate: str
    verdict: str
    message: str
    unit: str | None = None
    owner_name: str | None = None
    phone: str | None = None
    status: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


class CheckResponse(CheckMatch):
    site_code: str
    requested_plate: str | None = None
    match_mode: str = "exact"
    match_count: int = 1
    match_index: int = 0
    matches: list[CheckMatch] = Field(default_factory=list)


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str


class UserUpdateRequest(BaseModel):
    role: str | None = None
    password: str | None = None


class SiteCreateRequest(BaseModel):
    site_code: str
    name: str
    admin_username: str
    admin_password: str


class CctvAssignmentRequest(BaseModel):
    assigned_to: str | None = None
    work_weight: int | None = Field(None, ge=1, le=5)
    instruction: str | None = None
    status: str | None = None


USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")
SITE_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,31}$")
ROLE_LABELS = {
    "admin": "관리자",
    "director": "소장",
    "manager": "과장",
    "section_chief": "계장",
    "team_lead": "팀장",
    "staff": "주임",
    "guard": "경비",
    "cleaner": "미화",
}
VALID_USER_ROLES = set(ROLE_LABELS)
ROLE_ORDER = list(ROLE_LABELS)
VIEW_ROLES = set(ROLE_LABELS)
ENFORCEMENT_WRITE_ROLES = {"admin", "director", "manager", "section_chief", "team_lead", "staff", "guard"}
CCTV_ASSIGNMENT_ROLES = {"admin", "director", "manager", "section_chief", "team_lead"}
CCTV_STATUS_LABELS = {
    "requested": "요청",
    "assigned": "배정",
    "in_progress": "진행",
    "done": "완료",
    "cancelled": "취소",
}
CCTV_STATUSES = set(CCTV_STATUS_LABELS)


def app_url(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{ROOT_PATH}{path}" if ROOT_PATH else path


def role_order_case(column: str = "role") -> str:
    clauses = " ".join(f"WHEN '{role}' THEN {index}" for index, role in enumerate(ROLE_ORDER))
    return f"CASE {column} {clauses} ELSE {len(ROLE_ORDER)} END"


def session_cookie_path() -> str:
    return ROOT_PATH or "/"


def render_login_page(
    request: Request,
    *,
    status_code: int = 200,
    username: str = "",
    site_code: str = DEFAULT_SITE_CODE,
    error: str | None = None,
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_title": APP_TITLE,
            "username": username,
            "site_code": site_code,
            "login_error": error,
            "support_kakao_url": SUPPORT_KAKAO_URL,
            "support_kakao_label": SUPPORT_KAKAO_LABEL,
        },
        status_code=status_code,
    )


def normalize_login_site_code(value: str | None) -> str:
    site_code = normalize_site_code(value)
    if not SITE_CODE_PATTERN.fullmatch(site_code):
        raise HTTPException(status_code=400, detail=LOGIN_SITE_FORMAT_MESSAGE)
    return site_code


def normalize_required_site_code(value: str | None) -> str:
    if not str(value or "").strip():
        raise HTTPException(status_code=400, detail="아파트 코드를 입력해 주세요.")
    return normalize_login_site_code(value)


def normalize_site_name(value: str | None) -> str:
    name = str(value or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="아파트명을 입력해 주세요.")
    if len(name) > 80:
        raise HTTPException(status_code=400, detail="아파트명은 80자 이내로 입력해 주세요.")
    return name


def site_storage_key(site_code: str) -> str:
    key = re.sub(r"[^A-Z0-9_-]+", "-", normalize_site_code(site_code)).strip("-_").lower()
    return key or normalize_site_code(DEFAULT_SITE_CODE).lower()


def site_import_dir(site_code: str) -> Path:
    normalized_site = normalize_site_code(site_code)
    if normalized_site == normalize_site_code(DEFAULT_SITE_CODE):
        return IMPORT_DIR
    return IMPORT_DIR / site_storage_key(normalized_site)


def site_upload_dir(site_code: str) -> Path:
    return UPLOAD_DIR / site_storage_key(site_code)


def site_upload_url(site_code: str, filename: str) -> str:
    return app_url(f"/uploads/{site_storage_key(site_code)}/{filename}")


def site_public_dict(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "site_code": row["site_code"],
        "name": row["name"],
        "created_at": row["created_at"],
        "users_count": row.get("users_count", 0),
        "vehicles_count": row.get("vehicles_count", 0),
    }


def site_name_for_code(site_code: str) -> str:
    with connect() as con:
        row = con.execute("SELECT name FROM sites WHERE site_code = ?", (normalize_site_code(site_code),)).fetchone()
    return row["name"] if row else normalize_site_code(site_code)


def current_site_code(request: Request) -> str:
    session = read_session(request)
    if session and session.get("sc"):
        return normalize_site_code(session["sc"])
    return normalize_site_code(DEFAULT_SITE_CODE)


def ensure_ready() -> None:
    global _app_ready
    if _app_ready:
        return
    with _ready_lock:
        if _app_ready:
            return
        init_db()
        seed_users()
        maybe_seed_demo()
        auto_sync_registry()
        _app_ready = True


def lookup_vehicle(site_code: str, plate: str) -> dict[str, Any] | None:
    ensure_ready()
    normalized = normalize_plate(plate)
    with connect() as con:
        row = con.execute(
            "SELECT * FROM vehicles WHERE site_code = ? AND plate = ?",
            (site_code, normalized),
        ).fetchone()
    return dict(row) if row else None


def lookup_vehicles_by_suffix(site_code: str, suffix: str) -> list[dict[str, Any]]:
    ensure_ready()
    with connect() as con:
        rows = con.execute(
            """
            SELECT *
            FROM vehicles
            WHERE site_code = ? AND plate LIKE ?
            ORDER BY plate
            """,
            (site_code, f"%{suffix}"),
        ).fetchall()
    return [dict(row) for row in rows]


def is_suffix_plate_query(value: str) -> bool:
    raw = re.sub(r"\s+", "", str(value or ""))
    return len(raw) == 4 and raw.isdigit()


def build_check_match(plate: str, vehicle: dict[str, Any] | None) -> CheckMatch:
    verdict: PlateVerdict = evaluate_vehicle_row(vehicle)
    normalized = normalize_plate(plate)
    return CheckMatch(
        plate=normalized,
        verdict=verdict.verdict,
        message=verdict.message,
        unit=verdict.unit,
        owner_name=verdict.owner_name,
        phone=(vehicle or {}).get("phone"),
        status=verdict.status,
        valid_from=verdict.valid_from,
        valid_to=verdict.valid_to,
    )


def choose_best_scan_candidate(site_code: str, raw_ocr_text: str | None, manual_plate: str | None, candidates: list[str]) -> tuple[str | None, list[str]]:
    manual_normalized = normalize_plate(manual_plate)
    learned_candidates, learning_scores = get_learning_candidates(site_code, raw_ocr_text, candidates)
    source_candidates: list[str] = []
    if manual_normalized:
        source_candidates.append(manual_normalized)
    source_candidates.extend(learned_candidates)
    source_candidates.extend(candidates)

    normalized_candidates: list[str] = []
    seen: set[str] = set()

    for candidate in source_candidates:
        normalized = normalize_plate(candidate)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_candidates.append(normalized)

    if not normalized_candidates:
        return None, []

    ranked: list[tuple[str, float]] = []
    for index, candidate in enumerate(normalized_candidates):
        vehicle = lookup_vehicle(site_code, candidate)
        verdict = evaluate_vehicle_row(vehicle)
        score = learning_scores.get(candidate, 0.0)
        if candidate == manual_normalized:
            score += 1000.0
        if verdict.verdict != "UNREGISTERED":
            score += 220.0
            if verdict.verdict == "OK":
                score += 40.0
        score += max(0.0, 30.0 - (index * 2.0))
        ranked.append((candidate, score))

    ranked.sort(key=lambda item: item[1], reverse=True)
    ordered = [candidate for candidate, _ in ranked[:8]]
    return ordered[0], ordered


def build_check_response(site_code: str, plate: str) -> CheckResponse:
    requested = str(plate or "").strip()
    normalized = normalize_plate(requested)
    if not normalized and not is_suffix_plate_query(requested):
        raise HTTPException(status_code=400, detail="차량번호를 입력해 주세요.")

    if is_suffix_plate_query(requested):
        suffix_matches = [
            build_check_match(row["plate"], row)
            for row in lookup_vehicles_by_suffix(site_code, requested)
        ]
        suffix_matches.sort(
            key=lambda item: (
                {"OK": 0, "TEMP": 1, "EXPIRED": 2, "BLOCKED": 3, "UNREGISTERED": 4}.get(item.verdict, 9),
                item.plate,
            )
        )
        if not suffix_matches:
            unmatched = build_check_match(requested, None)
            return CheckResponse(
                site_code=site_code,
                requested_plate=requested,
                match_mode="suffix",
                match_count=0,
                match_index=0,
                matches=[],
                **unmatched.model_dump(),
            )

        primary = suffix_matches[0]
        return CheckResponse(
            site_code=site_code,
            requested_plate=requested,
            match_mode="suffix",
            match_count=len(suffix_matches),
            match_index=0,
            matches=suffix_matches,
            **primary.model_dump(),
        )

    match = build_check_match(normalized, lookup_vehicle(site_code, normalized))
    return CheckResponse(
        site_code=site_code,
        requested_plate=requested or normalized,
        match_mode="exact",
        match_count=1,
        match_index=0,
        matches=[],
        **match.model_dump(),
    )


def normalize_username(value: str | None) -> str:
    username = str(value or "").strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(status_code=400, detail="아이디는 영문 소문자, 숫자, 마침표(.), 밑줄(_), 하이픈(-)만 사용해 3~32자로 입력해 주세요.")
    return username


def normalize_user_role(value: str | None) -> str:
    role = str(value or "").strip().lower()
    if role not in VALID_USER_ROLES:
        labels = ", ".join(ROLE_LABELS.values())
        raise HTTPException(status_code=400, detail=f"권한은 {labels} 중 하나여야 합니다.")
    return role


def normalize_cctv_status(value: str | None) -> str:
    status = str(value or "").strip().lower()
    if status not in CCTV_STATUSES:
        raise HTTPException(status_code=400, detail="CCTV 요청 상태를 다시 확인해 주세요.")
    return status


def require_form_text(value: str | None, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"{label}을 입력해 주세요.")
    return text


def validate_cctv_time_range(search_start_time: str, search_end_time: str) -> None:
    if search_end_time < search_start_time:
        raise HTTPException(status_code=400, detail="검색 끝 시간은 시작 시간 이후로 입력해 주세요.")


def normalize_history_datetime(value: str | None, *, end_of_range: bool = False) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = text.replace("T", " ")
    if len(text) == 10:
        return f"{text} {'23:59:59' if end_of_range else '00:00:00'}"
    if len(text) == 16:
        return f"{text}:{'59' if end_of_range else '00'}"
    return text


def normalize_new_password(value: str | None, *, required: bool) -> str | None:
    if value is None:
        if required:
            raise HTTPException(status_code=400, detail="비밀번호를 입력해 주세요.")
        return None

    password = str(value)
    if not password:
        if required:
            raise HTTPException(status_code=400, detail="비밀번호를 입력해 주세요.")
        return None
    if password != password.strip():
        raise HTTPException(status_code=400, detail="비밀번호 앞뒤 공백은 사용할 수 없습니다.")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")
    return password


def user_public_dict(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "site_code": row["site_code"],
        "username": row["username"],
        "role": row["role"],
        "role_label": ROLE_LABELS.get(row["role"], row["role"]),
        "created_at": row["created_at"],
    }


def require_existing_user(con, site_code: str, username: str) -> dict[str, Any]:
    row = con.execute(
        "SELECT site_code, username, role, created_at FROM users WHERE site_code = ? AND username = ?",
        (normalize_site_code(site_code), username),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")
    return dict(row)


def ensure_not_last_admin(con, site_code: str, username: str, *, next_role: str | None = None, deleting: bool = False) -> None:
    normalized_site = normalize_site_code(site_code)
    target = require_existing_user(con, normalized_site, username)
    if target["role"] != "admin":
        return

    if not deleting and (next_role is None or next_role == "admin"):
        return

    admin_count = con.execute(
        "SELECT COUNT(*) AS cnt FROM users WHERE site_code = ? AND role = 'admin'",
        (normalized_site,),
    ).fetchone()["cnt"]
    if int(admin_count) <= 1:
        raise HTTPException(status_code=400, detail="마지막 관리자 계정은 삭제하거나 다른 권한으로 변경할 수 없습니다.")


def save_photo(photo: UploadFile, site_code: str) -> str | None:
    if not photo.filename:
        return None
    target_dir = site_upload_dir(site_code)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(photo.filename).suffix.lower() or ".jpg"
    name = f"{uuid.uuid4().hex}{suffix}"
    file_path = target_dir / name
    with file_path.open("wb") as target:
        shutil.copyfileobj(photo.file, target)
    return site_upload_url(site_code, name)


def save_photo_bytes(filename: str | None, payload: bytes, site_code: str) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="사진 파일을 선택해 주세요.")
    if not payload:
        raise HTTPException(status_code=400, detail="사진 파일이 비어 있습니다.")
    target_dir = site_upload_dir(site_code)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix.lower() or ".jpg"
    name = f"{uuid.uuid4().hex}{suffix}"
    (target_dir / name).write_bytes(payload)
    return site_upload_url(site_code, name)


def cctv_request_dict(row: dict[str, Any] | Any) -> dict[str, Any]:
    data = dict(row)
    start_time = data.get("search_start_time") or data.get("search_time")
    end_time = data.get("search_end_time") or start_time
    data["search_start_time"] = start_time
    data["search_end_time"] = end_time
    data["status_label"] = CCTV_STATUS_LABELS.get(data.get("status"), data.get("status") or "-")
    return data


def require_cctv_request(con, site_code: str, request_id: int) -> dict[str, Any]:
    row = con.execute(
        "SELECT * FROM cctv_search_requests WHERE site_code = ? AND id = ?",
        (site_code, request_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="CCTV 검색요청을 찾을 수 없습니다.")
    return dict(row)


def normalize_cctv_assignee(con, site_code: str, username: str | None) -> str | None:
    assignee = str(username or "").strip()
    if not assignee:
        return None
    row = con.execute(
        "SELECT username, role FROM users WHERE site_code = ? AND username = ?",
        (normalize_site_code(site_code), assignee),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="담당자 계정을 찾을 수 없습니다.")
    if row["role"] not in VALID_USER_ROLES:
        raise HTTPException(status_code=400, detail="담당자 권한을 다시 확인해 주세요.")
    return row["username"]


def auto_sync_registry() -> None:
    with connect() as con:
        site_codes = [row["site_code"] for row in con.execute("SELECT site_code FROM sites ORDER BY site_code").fetchall()]

    for site_code in site_codes:
        source_dir = site_import_dir(site_code)
        excel_files = [
            path
            for path in source_dir.iterdir()
            if source_dir.exists() and path.is_file() and path.suffix.lower() in {".xlsx", ".xlsm"} and not path.name.startswith("~$")
        ] if source_dir.exists() else []
        if not excel_files:
            continue
        try:
            sync_registry_from_dir(source_dir, site_code)
        except Exception as exc:
            print(f"[startup] registry sync failed for {site_code}: {exc}")


@app.on_event("startup")
def on_startup() -> None:
    ensure_ready()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/")
def root(request: Request):
    if read_session(request):
        return RedirectResponse(url=app_url("/field"), status_code=302)
    return RedirectResponse(url=app_url("/login"), status_code=302)


@app.head("/", include_in_schema=False)
def root_head():
    return Response(status_code=302, headers={"Location": app_url("/login")})


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if read_session(request):
        return RedirectResponse(url=app_url("/field"), status_code=302)
    if not LOCAL_LOGIN_ENABLED:
        return HTMLResponse("<h2>통합 로그인 모드입니다.</h2>", status_code=403)
    return render_login_page(request, site_code=DEFAULT_SITE_CODE)


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    site_code: str | None = Form(None),
):
    if not LOCAL_LOGIN_ENABLED:
        raise HTTPException(status_code=403, detail="통합 로그인 전용입니다.")

    ensure_ready()
    raw_site_code = str(site_code or DEFAULT_SITE_CODE).strip()
    try:
        user_site_code = normalize_login_site_code(raw_site_code)
    except HTTPException:
        return render_login_page(
            request,
            status_code=400,
            username=str(username or "").strip(),
            site_code=raw_site_code,
            error=LOGIN_SITE_FORMAT_MESSAGE,
        )
    try:
        user_name = normalize_username(username)
    except HTTPException:
        return render_login_page(
            request,
            status_code=400,
            username=str(username or "").strip(),
            site_code=user_site_code,
            error=LOGIN_FORMAT_MESSAGE,
        )
    with connect() as con:
        row = con.execute(
            "SELECT * FROM users WHERE site_code = ? AND username = ?",
            (user_site_code, user_name),
        ).fetchone()
    if not row or not pbkdf2_verify(password, row["pw_hash"]):
        return render_login_page(
            request,
            status_code=401,
            username=user_name,
            site_code=user_site_code,
            error=LOGIN_INVALID_MESSAGE,
        )

    token = make_session(user_name, row["role"], user_site_code)
    response = RedirectResponse(url=app_url("/field"), status_code=302)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        path=session_cookie_path(),
    )
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse(url=app_url("/login"), status_code=302)
    response.delete_cookie(COOKIE_NAME, path=session_cookie_path())
    return response


@app.get("/field", response_class=HTMLResponse)
def field_page(request: Request):
    ensure_ready()
    session = require_role(request, VIEW_ROLES)
    site_code = normalize_site_code(session.get("sc"))
    return templates.TemplateResponse(
        request=request,
        name="field.html",
        context={
            "app_title": APP_TITLE,
            "site_code": site_code,
            "site_name": site_name_for_code(site_code),
            "role": session.get("r"),
            "username": session.get("u"),
            "is_admin": session.get("r") == "admin",
            "import_dir": str(site_import_dir(site_code)),
            "ocr_provider": os.getenv("PARKING_OCR_PROVIDER", "tesseract"),
        },
    )


@app.get("/api/me")
def api_me(request: Request):
    ensure_ready()
    session = require_role(request, VIEW_ROLES)
    return {
        "username": session.get("u"),
        "role": session.get("r"),
        "site_code": normalize_site_code(session.get("sc")),
        "site_name": site_name_for_code(session.get("sc")),
    }


@app.get("/api/users")
def api_users_list(request: Request, q: str = "", role: str = "", limit: int = 50, offset: int = 0):
    ensure_ready()
    require_role(request, {"admin"})
    site_code = current_site_code(request)
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    where = ["site_code = ?"]
    params: list[Any] = [site_code]
    query = str(q or "").strip().lower()
    if query:
        where.append("username LIKE ?")
        params.append(f"%{query}%")

    normalized_role = str(role or "").strip().lower()
    if normalized_role:
        normalized_role = normalize_user_role(normalized_role)
        where.append("role = ?")
        params.append(normalized_role)

    params.extend([limit, offset])
    with connect() as con:
        rows = con.execute(
            f"""
            SELECT site_code, username, role, created_at
            FROM users
            WHERE {' AND '.join(where)}
            ORDER BY {role_order_case()}, username
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
    return [user_public_dict(dict(row)) for row in rows]


@app.post("/api/users")
def api_users_create(request: Request, payload: UserCreateRequest):
    ensure_ready()
    require_role(request, {"admin"})
    site_code = current_site_code(request)

    username = normalize_username(payload.username)
    role = normalize_user_role(payload.role)
    password = normalize_new_password(payload.password, required=True)

    with connect() as con:
        exists = con.execute(
            "SELECT 1 FROM users WHERE site_code = ? AND username = ?",
            (site_code, username),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")

        con.execute(
            "INSERT INTO users(site_code, username, pw_hash, role) VALUES (?, ?, ?, ?)",
            (site_code, username, pbkdf2_hash(password), role),
        )
        row = require_existing_user(con, site_code, username)
        con.commit()
    return user_public_dict(row)


@app.patch("/api/users/{username}")
def api_users_update(request: Request, username: str, payload: UserUpdateRequest):
    ensure_ready()
    session = require_role(request, {"admin"})
    site_code = current_site_code(request)
    normalized_username = normalize_username(username)
    next_role = normalize_user_role(payload.role) if payload.role is not None else None
    next_password = normalize_new_password(payload.password, required=False)

    with connect() as con:
        current = require_existing_user(con, site_code, normalized_username)

        if normalized_username == session.get("u") and next_role is not None and next_role != current["role"]:
            raise HTTPException(status_code=400, detail="현재 로그인한 본인 계정의 권한은 여기서 변경할 수 없습니다.")

        ensure_not_last_admin(con, site_code, normalized_username, next_role=next_role, deleting=False)

        fields: list[str] = []
        values: list[Any] = []

        if next_role is not None and next_role != current["role"]:
            fields.append("role = ?")
            values.append(next_role)

        if next_password is not None:
            fields.append("pw_hash = ?")
            values.append(pbkdf2_hash(next_password))

        if not fields:
            return user_public_dict(current)

        values.extend([site_code, normalized_username])
        con.execute(f"UPDATE users SET {', '.join(fields)} WHERE site_code = ? AND username = ?", values)
        row = require_existing_user(con, site_code, normalized_username)
        con.commit()
    return user_public_dict(row)


@app.delete("/api/users/{username}")
def api_users_delete(request: Request, username: str):
    ensure_ready()
    session = require_role(request, {"admin"})
    site_code = current_site_code(request)
    normalized_username = normalize_username(username)

    if normalized_username == session.get("u"):
        raise HTTPException(status_code=400, detail="현재 로그인한 계정은 삭제할 수 없습니다.")

    with connect() as con:
        require_existing_user(con, site_code, normalized_username)
        ensure_not_last_admin(con, site_code, normalized_username, deleting=True)
        con.execute("DELETE FROM users WHERE site_code = ? AND username = ?", (site_code, normalized_username))
        con.commit()

    return {"deleted": True, "username": normalized_username}


@app.get("/api/sites")
def api_sites_list(request: Request, q: str = "", limit: int = 50, offset: int = 0):
    ensure_ready()
    require_role(request, {"admin"})
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    query = str(q or "").strip()
    where = ""
    params: list[Any] = []
    if query:
        where = "WHERE s.site_code LIKE ? OR s.name LIKE ?"
        like = f"%{query}%"
        params.extend([like, like])
    params.extend([limit, offset])
    with connect() as con:
        rows = con.execute(
            f"""
            SELECT
              s.site_code,
              s.name,
              s.created_at,
              COUNT(DISTINCT u.id) AS users_count,
              COUNT(DISTINCT v.plate) AS vehicles_count
            FROM sites s
            LEFT JOIN users u ON u.site_code = s.site_code
            LEFT JOIN vehicles v ON v.site_code = s.site_code
            {where}
            GROUP BY s.site_code, s.name, s.created_at
            ORDER BY s.site_code
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
    return [site_public_dict(dict(row)) for row in rows]


@app.post("/api/sites")
def api_sites_create(request: Request, payload: SiteCreateRequest):
    ensure_ready()
    require_role(request, {"admin"})

    site_code = normalize_required_site_code(payload.site_code)
    site_name = normalize_site_name(payload.name)
    admin_username = normalize_username(payload.admin_username)
    admin_password = normalize_new_password(payload.admin_password, required=True)

    with connect() as con:
        exists = con.execute("SELECT 1 FROM sites WHERE site_code = ?", (site_code,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="이미 등록된 아파트 코드입니다.")

        con.execute("INSERT INTO sites(site_code, name) VALUES (?, ?)", (site_code, site_name))
        con.execute(
            "INSERT INTO users(site_code, username, pw_hash, role) VALUES (?, ?, ?, 'admin')",
            (site_code, admin_username, pbkdf2_hash(admin_password)),
        )
        row = con.execute(
            """
            SELECT
              s.site_code,
              s.name,
              s.created_at,
              COUNT(DISTINCT u.id) AS users_count,
              COUNT(DISTINCT v.plate) AS vehicles_count
            FROM sites s
            LEFT JOIN users u ON u.site_code = s.site_code
            LEFT JOIN vehicles v ON v.site_code = s.site_code
            WHERE s.site_code = ?
            GROUP BY s.site_code, s.name, s.created_at
            """,
            (site_code,),
        ).fetchone()
        con.commit()
    return site_public_dict(dict(row))


@app.get("/api/cctv/assignees")
def api_cctv_assignees(request: Request):
    ensure_ready()
    require_role(request, CCTV_ASSIGNMENT_ROLES)
    site_code = current_site_code(request)
    with connect() as con:
        rows = con.execute(
            f"""
            SELECT site_code, username, role, created_at
            FROM users
            WHERE site_code = ?
            ORDER BY {role_order_case()}, username
            """,
            (site_code,),
        ).fetchall()
    return [user_public_dict(dict(row)) for row in rows]


@app.get("/api/cctv/requests")
def api_cctv_requests(request: Request, limit: int = 50, offset: int = 0):
    ensure_ready()
    session = require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    base_query = """
        SELECT *
        FROM cctv_search_requests
        WHERE site_code = ?
          AND status NOT IN ('done', 'cancelled')
    """
    params: list[Any] = [site_code]
    if session.get("r") not in CCTV_ASSIGNMENT_ROLES:
        base_query += " AND (requester_username = ? OR assigned_to = ?)"
        params.extend([session.get("u"), session.get("u")])

    base_query += """
        ORDER BY
          CASE status
            WHEN 'requested' THEN 0
            WHEN 'assigned' THEN 1
            WHEN 'in_progress' THEN 2
            WHEN 'done' THEN 3
            ELSE 4
          END,
          work_weight DESC,
          search_start_time ASC,
          created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with connect() as con:
        rows = con.execute(base_query, params).fetchall()
    return [cctv_request_dict(row) for row in rows]


@app.post("/api/cctv/requests")
async def api_cctv_request_create(
    request: Request,
    photo: UploadFile = File(...),
    location: str = Form(...),
    search_start_time: str | None = Form(None),
    search_end_time: str | None = Form(None),
    search_time: str | None = Form(None),
    content: str = Form(...),
):
    ensure_ready()
    session = require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    normalized_location = require_form_text(location, "위치")
    normalized_search_start_time = require_form_text(search_start_time or search_time, "검색 시작 시간")
    normalized_search_end_time = require_form_text(search_end_time or search_time, "검색 끝 시간")
    validate_cctv_time_range(normalized_search_start_time, normalized_search_end_time)
    normalized_content = require_form_text(content, "요청 내용")
    payload = await photo.read()
    photo_path = save_photo_bytes(photo.filename, payload, site_code)

    with connect() as con:
        cur = con.execute(
            """
            INSERT INTO cctv_search_requests
            (site_code, requester_username, photo_path, location, search_start_time, search_end_time, content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                site_code,
                session.get("u"),
                photo_path,
                normalized_location,
                normalized_search_start_time,
                normalized_search_end_time,
                normalized_content,
            ),
        )
        row = con.execute("SELECT * FROM cctv_search_requests WHERE id = ?", (cur.lastrowid,)).fetchone()
        con.commit()
    return cctv_request_dict(row)


@app.patch("/api/cctv/requests/{request_id}")
def api_cctv_request_update(request: Request, request_id: int, payload: CctvAssignmentRequest):
    ensure_ready()
    session = require_role(request, CCTV_ASSIGNMENT_ROLES)
    site_code = current_site_code(request)
    with connect() as con:
        current = require_cctv_request(con, site_code, request_id)
        fields_set = payload.model_fields_set
        updates: list[str] = []
        values: list[Any] = []

        if "assigned_to" in fields_set:
            assignee = normalize_cctv_assignee(con, site_code, payload.assigned_to)
            updates.append("assigned_to = ?")
            values.append(assignee)
            updates.append("assigned_by = ?")
            values.append(session.get("u") if assignee else None)
            updates.append("assigned_at = datetime('now')" if assignee else "assigned_at = NULL")
            if assignee and "status" not in fields_set and current["status"] == "requested":
                updates.append("status = ?")
                values.append("assigned")

        if "work_weight" in fields_set and payload.work_weight is not None:
            updates.append("work_weight = ?")
            values.append(payload.work_weight)

        if "instruction" in fields_set:
            updates.append("instruction = ?")
            values.append(str(payload.instruction or "").strip() or None)

        next_status: str | None = None
        if "status" in fields_set and payload.status is not None:
            next_status = normalize_cctv_status(payload.status)
            updates.append("status = ?")
            values.append(next_status)
            updates.append("completed_at = datetime('now')" if next_status == "done" else "completed_at = NULL")

        if not updates:
            return cctv_request_dict(current)

        updates.append("updated_at = datetime('now')")
        values.extend([request_id, site_code])
        con.execute(
            f"UPDATE cctv_search_requests SET {', '.join(updates)} WHERE id = ? AND site_code = ?",
            values,
        )
        row = con.execute("SELECT * FROM cctv_search_requests WHERE site_code = ? AND id = ?", (site_code, request_id)).fetchone()
        con.commit()
    return cctv_request_dict(row)


@app.get("/api/registry/check", response_model=CheckResponse)
def api_registry_check(request: Request, plate: str):
    require_role(request, VIEW_ROLES)
    return build_check_response(current_site_code(request), plate)


@app.get("/api/registry/search")
def api_registry_search(request: Request, q: str = "", limit: int = 20):
    ensure_ready()
    require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    limit = min(max(limit, 1), 50)
    query = normalize_plate(q) or q.strip()
    like = f"%{query}%"
    with connect() as con:
        rows = con.execute(
            """
            SELECT plate, unit, owner_name, phone, status, valid_from, valid_to, note, source_file, source_sheet
            FROM vehicles
            WHERE site_code = ?
              AND (
                plate LIKE ?
                OR COALESCE(unit, '') LIKE ?
                OR COALESCE(owner_name, '') LIKE ?
              )
            ORDER BY updated_at DESC, plate
            LIMIT ?
            """,
            (site_code, like, like, like, limit),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/registry/status")
def api_registry_status(request: Request):
    ensure_ready()
    require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    source_dir = site_import_dir(site_code)
    with connect() as con:
        vehicle_count = con.execute("SELECT COUNT(*) AS cnt FROM vehicles WHERE site_code = ?", (site_code,)).fetchone()["cnt"]
        last_run = con.execute(
            """
            SELECT id, source_dir, files_count, rows_count, imported_at, status, message
            FROM import_runs
            WHERE site_code = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (site_code,),
        ).fetchone()
    return {
        "site_code": site_code,
        "site_name": site_name_for_code(site_code),
        "vehicle_count": vehicle_count,
        "import_dir": str(source_dir),
        "import_files": describe_excel_files(source_dir),
        "ocr_provider": os.getenv("PARKING_OCR_PROVIDER", "tesseract"),
        "ocr_learning": get_learning_status(site_code),
        "last_sync": dict(last_run) if last_run else None,
    }


@app.post("/api/registry/sync")
def api_registry_sync(request: Request):
    ensure_ready()
    require_role(request, {"admin"})
    site_code = current_site_code(request)
    try:
        return sync_registry_from_dir(site_import_dir(site_code), site_code)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/registry/upload")
async def api_registry_upload(request: Request, files: list[UploadFile] = File(...)):
    ensure_ready()
    require_role(request, {"admin"})
    site_code = current_site_code(request)
    source_dir = site_import_dir(site_code)

    if not files:
        raise HTTPException(status_code=400, detail="업로드할 Excel 파일을 선택해 주세요.")

    pending: list[tuple[str | None, bytes]] = []
    for item in files:
        payload = await item.read()
        pending.append((item.filename, payload))

    saved_names: set[str] = set()
    uploaded_paths: list[Path] = []
    try:
        for filename, payload in pending:
            try:
                uploaded = store_registry_upload(source_dir, filename, payload, saved_names)
            except ValueError as exc:
                display_name = Path(str(filename or "")).name or "이름 없는 파일"
                raise ValueError(f"{display_name}: {exc}") from exc
            uploaded_paths.append(uploaded)
            saved_names.add(uploaded.name)
        sync_result = sync_registry_from_dir(source_dir, site_code)
    except ValueError as exc:
        for path in uploaded_paths:
            if path.exists():
                path.unlink()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        for path in uploaded_paths:
            if path.exists():
                path.unlink()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        for path in uploaded_paths:
            if path.exists():
                path.unlink()
        raise HTTPException(status_code=400, detail=f"Excel 파일 처리 중 오류가 발생했습니다: {exc}") from exc

    return {
        "saved_count": len(uploaded_paths),
        "saved_files": [path.name for path in uploaded_paths],
        "import_dir": str(source_dir),
        "sync": sync_result,
    }


@app.post("/api/ocr/scan")
async def api_ocr_scan(request: Request, photo: UploadFile = File(...), manual_plate: str | None = Form(None)):
    ensure_ready()
    require_role(request, VIEW_ROLES)
    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="사진 파일이 비어 있습니다.")

    scan = scan_plate_image(image_bytes)
    site_code = current_site_code(request)
    best_plate, ordered_candidates = choose_best_scan_candidate(site_code, scan.raw_text, manual_plate, scan.candidates)
    match = build_check_response(current_site_code(request), best_plate).model_dump() if best_plate else None
    return {
        "provider": scan.provider,
        "raw_text": scan.raw_text,
        "candidates": ordered_candidates,
        "best_plate": best_plate,
        "match": match,
        "error": scan.error,
    }


@app.post("/api/enforcement/submit")
async def api_enforcement_submit(
    request: Request,
    plate: str = Form(...),
    inspector: str | None = Form(None),
    location: str | None = Form(None),
    memo: str | None = Form(None),
    raw_ocr_text: str | None = Form(None),
    ocr_best_plate: str | None = Form(None),
    ocr_candidates: str | None = Form(None),
    lat: float | None = Form(None),
    lng: float | None = Form(None),
    photo: UploadFile | None = File(None),
):
    ensure_ready()
    require_role(request, ENFORCEMENT_WRITE_ROLES)
    site_code = current_site_code(request)
    check = build_check_response(site_code, plate)
    photo_path = save_photo(photo, site_code) if photo else None
    learned_candidates = parse_candidates_json(ocr_candidates)

    with connect() as con:
        cur = con.execute(
            """
            INSERT INTO enforcement_events
            (site_code, plate, raw_ocr_text, verdict, verdict_message, unit, owner_name, vehicle_status, inspector, location, memo, photo_path, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                site_code,
                check.plate,
                raw_ocr_text,
                check.verdict,
                check.message,
                check.unit,
                check.owner_name,
                check.status,
                inspector,
                location,
                memo,
                photo_path,
                lat,
                lng,
            ),
        )
        event_id = cur.lastrowid
        row = con.execute("SELECT * FROM enforcement_events WHERE id = ?", (event_id,)).fetchone()
        con.commit()

    record_ocr_feedback(
        site_code=site_code,
        raw_ocr_text=raw_ocr_text,
        suggested_plate=ocr_best_plate,
        corrected_plate=check.plate,
        candidates=learned_candidates,
        photo_path=photo_path,
    )

    return dict(row)


@app.get("/api/enforcement/recent")
def api_enforcement_recent(request: Request, limit: int = 20):
    ensure_ready()
    require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    limit = min(max(limit, 1), 50)
    with connect() as con:
        rows = con.execute(
            """
            SELECT id, plate, verdict, verdict_message, unit, owner_name, inspector, location, memo, photo_path, created_at
            FROM enforcement_events
            WHERE site_code = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (site_code, limit),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/enforcement/history")
def api_enforcement_history(
    request: Request,
    q: str = "",
    verdict: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 20,
    offset: int = 0,
):
    ensure_ready()
    require_role(request, VIEW_ROLES)
    site_code = current_site_code(request)
    limit = min(max(limit, 1), 50)
    offset = max(offset, 0)

    where = ["site_code = ?"]
    params: list[Any] = [site_code]

    query = str(q or "").strip()
    if query:
        normalized_plate = normalize_plate(query)
        like = f"%{query}%"
        plate_like = f"%{normalized_plate or query}%"
        where.append(
            """
            (
              plate LIKE ?
              OR COALESCE(unit, '') LIKE ?
              OR COALESCE(owner_name, '') LIKE ?
              OR COALESCE(inspector, '') LIKE ?
              OR COALESCE(location, '') LIKE ?
              OR COALESCE(memo, '') LIKE ?
            )
            """
        )
        params.extend([plate_like, like, like, like, like, like])

    normalized_verdict = str(verdict or "").strip().upper()
    if normalized_verdict:
        where.append("verdict = ?")
        params.append(normalized_verdict)

    normalized_from = normalize_history_datetime(date_from)
    if normalized_from:
        where.append("created_at >= ?")
        params.append(normalized_from)

    normalized_to = normalize_history_datetime(date_to, end_of_range=True)
    if normalized_to:
        where.append("created_at <= ?")
        params.append(normalized_to)

    sql = f"""
        SELECT id, plate, verdict, verdict_message, unit, owner_name, inspector, location, memo, photo_path, created_at
        FROM enforcement_events
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit + 1, offset])

    with connect() as con:
        rows = [dict(row) for row in con.execute(sql, params).fetchall()]

    has_more = len(rows) > limit
    items = rows[:limit]
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + len(items) if has_more else None,
        "has_more": has_more,
    }

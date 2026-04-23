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
from .db import DEFAULT_SITE_CODE, connect, init_db, maybe_seed_demo, normalize_site_code, seed_users
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


VALID_USER_ROLES = {"admin", "guard", "viewer"}
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")
ROLE_LABELS = {
    "admin": "관리자",
    "guard": "경비",
    "viewer": "조회",
}


def app_url(path: str) -> str:
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{ROOT_PATH}{path}" if ROOT_PATH else path


def session_cookie_path() -> str:
    return ROOT_PATH or "/"


def render_login_page(request: Request, *, status_code: int = 200, username: str = "", error: str | None = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_title": APP_TITLE,
            "username": username,
            "login_error": error,
            "support_kakao_url": SUPPORT_KAKAO_URL,
            "support_kakao_label": SUPPORT_KAKAO_LABEL,
        },
        status_code=status_code,
    )


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
        raise HTTPException(status_code=400, detail="권한은 admin, guard, viewer 중 하나여야 합니다.")
    return role


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
        "username": row["username"],
        "role": row["role"],
        "role_label": ROLE_LABELS.get(row["role"], row["role"]),
        "created_at": row["created_at"],
    }


def require_existing_user(con, username: str) -> dict[str, Any]:
    row = con.execute(
        "SELECT username, role, created_at FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")
    return dict(row)


def ensure_not_last_admin(con, username: str, *, next_role: str | None = None, deleting: bool = False) -> None:
    target = require_existing_user(con, username)
    if target["role"] != "admin":
        return

    if not deleting and (next_role is None or next_role == "admin"):
        return

    admin_count = con.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin'").fetchone()["cnt"]
    if int(admin_count) <= 1:
        raise HTTPException(status_code=400, detail="마지막 관리자 계정은 삭제하거나 다른 권한으로 변경할 수 없습니다.")


def save_photo(photo: UploadFile) -> str | None:
    if not photo.filename:
        return None
    suffix = Path(photo.filename).suffix.lower() or ".jpg"
    name = f"{uuid.uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / name
    with file_path.open("wb") as target:
        shutil.copyfileobj(photo.file, target)
    return app_url(f"/uploads/{name}")


def auto_sync_registry() -> None:
    excel_files = [path for path in IMPORT_DIR.iterdir() if path.is_file() and path.suffix.lower() in {".xlsx", ".xlsm"} and not path.name.startswith("~$")]
    if not excel_files:
        return
    try:
        sync_registry_from_dir(IMPORT_DIR, DEFAULT_SITE_CODE)
    except Exception as exc:
        print(f"[startup] registry sync failed: {exc}")


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
    return render_login_page(request)


@app.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if not LOCAL_LOGIN_ENABLED:
        raise HTTPException(status_code=403, detail="통합 로그인 전용입니다.")

    ensure_ready()
    try:
        user_name = normalize_username(username)
    except HTTPException:
        return render_login_page(
            request,
            status_code=400,
            username=str(username or "").strip(),
            error=LOGIN_FORMAT_MESSAGE,
        )
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE username = ?", (user_name,)).fetchone()
    if not row or not pbkdf2_verify(password, row["pw_hash"]):
        return render_login_page(
            request,
            status_code=401,
            username=user_name,
            error=LOGIN_INVALID_MESSAGE,
        )

    token = make_session(user_name, row["role"], normalize_site_code(DEFAULT_SITE_CODE))
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
    session = require_role(request, {"admin", "guard", "viewer"})
    return templates.TemplateResponse(
        request=request,
        name="field.html",
        context={
            "app_title": APP_TITLE,
            "site_code": normalize_site_code(session.get("sc")),
            "role": session.get("r"),
            "username": session.get("u"),
            "is_admin": session.get("r") == "admin",
            "import_dir": str(IMPORT_DIR),
            "ocr_provider": os.getenv("PARKING_OCR_PROVIDER", "tesseract"),
        },
    )


@app.get("/api/me")
def api_me(request: Request):
    ensure_ready()
    session = require_role(request, {"admin", "guard", "viewer"})
    return {
        "username": session.get("u"),
        "role": session.get("r"),
        "site_code": normalize_site_code(session.get("sc")),
    }


@app.get("/api/users")
def api_users_list(request: Request):
    ensure_ready()
    require_role(request, {"admin"})
    with connect() as con:
        rows = con.execute(
            """
            SELECT username, role, created_at
            FROM users
            ORDER BY CASE role WHEN 'admin' THEN 0 WHEN 'guard' THEN 1 ELSE 2 END, username
            """
        ).fetchall()
    return [user_public_dict(dict(row)) for row in rows]


@app.post("/api/users")
def api_users_create(request: Request, payload: UserCreateRequest):
    ensure_ready()
    require_role(request, {"admin"})

    username = normalize_username(payload.username)
    role = normalize_user_role(payload.role)
    password = normalize_new_password(payload.password, required=True)

    with connect() as con:
        exists = con.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")

        con.execute(
            "INSERT INTO users(username, pw_hash, role) VALUES (?, ?, ?)",
            (username, pbkdf2_hash(password), role),
        )
        row = require_existing_user(con, username)
        con.commit()
    return user_public_dict(row)


@app.patch("/api/users/{username}")
def api_users_update(request: Request, username: str, payload: UserUpdateRequest):
    ensure_ready()
    session = require_role(request, {"admin"})
    normalized_username = normalize_username(username)
    next_role = normalize_user_role(payload.role) if payload.role is not None else None
    next_password = normalize_new_password(payload.password, required=False)

    with connect() as con:
        current = require_existing_user(con, normalized_username)

        if normalized_username == session.get("u") and next_role is not None and next_role != current["role"]:
            raise HTTPException(status_code=400, detail="현재 로그인한 본인 계정의 권한은 여기서 변경할 수 없습니다.")

        ensure_not_last_admin(con, normalized_username, next_role=next_role, deleting=False)

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

        values.append(normalized_username)
        con.execute(f"UPDATE users SET {', '.join(fields)} WHERE username = ?", values)
        row = require_existing_user(con, normalized_username)
        con.commit()
    return user_public_dict(row)


@app.delete("/api/users/{username}")
def api_users_delete(request: Request, username: str):
    ensure_ready()
    session = require_role(request, {"admin"})
    normalized_username = normalize_username(username)

    if normalized_username == session.get("u"):
        raise HTTPException(status_code=400, detail="현재 로그인한 계정은 삭제할 수 없습니다.")

    with connect() as con:
        require_existing_user(con, normalized_username)
        ensure_not_last_admin(con, normalized_username, deleting=True)
        con.execute("DELETE FROM users WHERE username = ?", (normalized_username,))
        con.commit()

    return {"deleted": True, "username": normalized_username}


@app.get("/api/registry/check", response_model=CheckResponse)
def api_registry_check(request: Request, plate: str):
    require_role(request, {"admin", "guard", "viewer"})
    return build_check_response(current_site_code(request), plate)


@app.get("/api/registry/search")
def api_registry_search(request: Request, q: str = "", limit: int = 20):
    ensure_ready()
    require_role(request, {"admin", "guard", "viewer"})
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
    require_role(request, {"admin", "guard", "viewer"})
    site_code = current_site_code(request)
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
        "vehicle_count": vehicle_count,
        "import_dir": str(IMPORT_DIR),
        "import_files": describe_excel_files(IMPORT_DIR),
        "ocr_provider": os.getenv("PARKING_OCR_PROVIDER", "tesseract"),
        "ocr_learning": get_learning_status(site_code),
        "last_sync": dict(last_run) if last_run else None,
    }


@app.post("/api/registry/sync")
def api_registry_sync(request: Request):
    ensure_ready()
    require_role(request, {"admin"})
    try:
        return sync_registry_from_dir(IMPORT_DIR, current_site_code(request))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/registry/upload")
async def api_registry_upload(request: Request, files: list[UploadFile] = File(...)):
    ensure_ready()
    require_role(request, {"admin"})

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
            uploaded = store_registry_upload(IMPORT_DIR, filename, payload, saved_names)
            uploaded_paths.append(uploaded)
            saved_names.add(uploaded.name)
        sync_result = sync_registry_from_dir(IMPORT_DIR, current_site_code(request))
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
        "import_dir": str(IMPORT_DIR),
        "sync": sync_result,
    }


@app.post("/api/ocr/scan")
async def api_ocr_scan(request: Request, photo: UploadFile = File(...), manual_plate: str | None = Form(None)):
    ensure_ready()
    require_role(request, {"admin", "guard", "viewer"})
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
    require_role(request, {"admin", "guard"})
    site_code = current_site_code(request)
    check = build_check_response(site_code, plate)
    photo_path = save_photo(photo) if photo else None
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
    require_role(request, {"admin", "guard", "viewer"})
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

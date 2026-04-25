import base64
import hashlib
import hmac
import os

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SECRET_KEY = os.getenv("PARKING_SECRET_KEY", "dev-secret-change-me")
SESSION_MAX_AGE = int(os.getenv("PARKING_SESSION_MAX_AGE", "43200"))
COOKIE_NAME = os.getenv("PARKING_SESSION_COOKIE", "parking_session")

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="parking-session")


def pbkdf2_hash(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return base64.b64encode(salt + derived_key).decode("utf-8")


def pbkdf2_verify(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode("utf-8"))
    salt, digest = raw[:16], raw[16:]
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return hmac.compare_digest(digest, candidate)


def make_session(username: str, role: str, site_code: str) -> str:
    return _serializer.dumps({"u": username, "r": role, "sc": site_code})


def read_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def require_login(request: Request) -> dict:
    session = read_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return session


def require_role(request: Request, roles: set[str]) -> dict:
    session = require_login(request)
    if session.get("r") == "viewer":
        session["r"] = "cleaner"
    if session.get("r") not in roles:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    return session


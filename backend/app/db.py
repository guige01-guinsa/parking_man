import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("PARKING_DB_PATH", str(BASE_DIR / "data" / "parking.db")))
DEFAULT_SITE_CODE = (os.getenv("PARKING_DEFAULT_SITE_CODE", "APT1100").strip().upper() or "APT1100")
SEED_DEMO = os.getenv("PARKING_SEED_DEMO", "1").strip().lower() in {"1", "true", "yes", "on"}
VALID_USER_ROLES = {
    "admin",
    "director",
    "manager",
    "section_chief",
    "team_lead",
    "staff",
    "guard",
    "cleaner",
}


class ClosingConnection(sqlite3.Connection):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def normalize_site_code(value: str | None) -> str:
    text = str(value or "").strip().upper()
    return text or DEFAULT_SITE_CODE


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, factory=ClosingConnection)
    con.row_factory = sqlite3.Row
    return con


def table_columns(con: sqlite3.Connection, table_name: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def create_cctv_request_indexes(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_status_range
        ON cctv_search_requests(site_code, status, search_start_time, search_end_time)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_requester
        ON cctv_search_requests(site_code, requester_username)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_assignee
        ON cctv_search_requests(site_code, assigned_to)
        """
    )


def rebuild_cctv_request_table(con: sqlite3.Connection) -> None:
    con.execute("DROP TABLE IF EXISTS cctv_search_requests_new")
    con.execute(
        """
        CREATE TABLE cctv_search_requests_new (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL,
          requester_username TEXT NOT NULL,
          photo_path TEXT NOT NULL,
          location TEXT NOT NULL,
          search_start_time TEXT NOT NULL,
          search_end_time TEXT NOT NULL,
          content TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'requested',
          work_weight INTEGER NOT NULL DEFAULT 1,
          assigned_to TEXT,
          instruction TEXT,
          assigned_by TEXT,
          assigned_at TEXT,
          completed_at TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        INSERT INTO cctv_search_requests_new
        (id, site_code, requester_username, photo_path, location, search_start_time, search_end_time, content,
         status, work_weight, assigned_to, instruction, assigned_by, assigned_at, completed_at, created_at, updated_at)
        SELECT
          id,
          site_code,
          requester_username,
          photo_path,
          location,
          COALESCE(NULLIF(search_start_time, ''), search_time),
          COALESCE(NULLIF(search_end_time, ''), NULLIF(search_start_time, ''), search_time),
          content,
          COALESCE(NULLIF(status, ''), 'requested'),
          COALESCE(work_weight, 1),
          assigned_to,
          instruction,
          assigned_by,
          assigned_at,
          completed_at,
          created_at,
          updated_at
        FROM cctv_search_requests
        """
    )
    con.execute("DROP TABLE cctv_search_requests")
    con.execute("ALTER TABLE cctv_search_requests_new RENAME TO cctv_search_requests")


def ensure_cctv_request_schema(con: sqlite3.Connection) -> None:
    columns = table_columns(con, "cctv_search_requests")
    if not columns:
        return

    if "search_start_time" not in columns:
        con.execute("ALTER TABLE cctv_search_requests ADD COLUMN search_start_time TEXT")
    if "search_end_time" not in columns:
        con.execute("ALTER TABLE cctv_search_requests ADD COLUMN search_end_time TEXT")

    if "search_time" in columns:
        con.execute(
            """
            UPDATE cctv_search_requests
            SET search_start_time = COALESCE(NULLIF(search_start_time, ''), search_time)
            WHERE search_start_time IS NULL OR search_start_time = ''
            """
        )
        con.execute(
            """
            UPDATE cctv_search_requests
            SET search_end_time = COALESCE(NULLIF(search_end_time, ''), search_start_time, search_time)
            WHERE search_end_time IS NULL OR search_end_time = ''
            """
        )
        rebuild_cctv_request_table(con)

    create_cctv_request_indexes(con)


def ensure_user_role_schema(con: sqlite3.Connection) -> None:
    columns = table_columns(con, "users")
    if not columns:
        return

    con.execute("UPDATE users SET role = 'cleaner' WHERE role = 'viewer'")
    placeholders = ", ".join("?" for _ in VALID_USER_ROLES)
    con.execute(
        f"""
        UPDATE users
        SET role = 'cleaner'
        WHERE role IS NULL OR role = '' OR role NOT IN ({placeholders})
        """,
        tuple(sorted(VALID_USER_ROLES)),
    )


def init_db() -> None:
    schema_path = BASE_DIR / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with connect() as con:
        con.executescript(schema_sql)
        ensure_cctv_request_schema(con)
        ensure_user_role_schema(con)
        con.commit()


def seed_users() -> None:
    from .auth import pbkdf2_hash

    demo_users = [
        ("admin", pbkdf2_hash("admin1234"), "admin"),
        ("guard", pbkdf2_hash("guard1234"), "guard"),
        ("cleaner", pbkdf2_hash("cleaner1234"), "cleaner"),
    ]
    with connect() as con:
        existing = con.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if int(existing["cnt"]) > 0:
            return
        con.executemany(
            "INSERT INTO users(username, pw_hash, role) VALUES (?, ?, ?)",
            demo_users,
        )
        con.commit()


def maybe_seed_demo() -> None:
    if not SEED_DEMO:
        return

    site_code = normalize_site_code(DEFAULT_SITE_CODE)
    demo_rows = [
        (site_code, "12가3456", "101-1203", "홍길동", "010-1111-2222", "active", "2026-01-01", "2027-12-31", "상시 등록", "demo.xlsx", "vehicles"),
        (site_code, "34나5678", "102-803", "김영희", "010-2222-3333", "blocked", None, None, "관리소 차단 차량", "demo.xlsx", "vehicles"),
        (site_code, "123다4567", "103-1502", "이철수", "010-3333-4444", "temp", "2026-04-01", "2026-04-30", "임시 등록", "demo.xlsx", "vehicles"),
    ]
    with connect() as con:
        exists = con.execute("SELECT COUNT(*) AS cnt FROM vehicles WHERE site_code = ?", (site_code,)).fetchone()
        if int(exists["cnt"]) > 0:
            return
        con.executemany(
            """
            INSERT OR IGNORE INTO vehicles
            (site_code, plate, unit, owner_name, phone, status, valid_from, valid_to, note, source_file, source_sheet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo_rows,
        )
        con.commit()


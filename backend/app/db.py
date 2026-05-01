import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("PARKING_DB_PATH", str(BASE_DIR / "data" / "parking.db")))
DEFAULT_SITE_CODE = (os.getenv("PARKING_DEFAULT_SITE_CODE", "APT1100").strip().upper() or "APT1100")
DEFAULT_SITE_NAME = os.getenv("PARKING_DEFAULT_SITE_NAME", "기본 아파트").strip() or "기본 아파트"
SEED_DEMO = os.getenv("PARKING_SEED_DEMO", "1").strip().lower() in {"1", "true", "yes", "on"}
BILLING_PROVIDER = os.getenv("PARKING_BILLING_PROVIDER", "manual").strip().lower() or "manual"
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
    con.execute("PRAGMA busy_timeout = 5000")
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA synchronous = NORMAL")
    con.execute("PRAGMA temp_store = MEMORY")
    return con


def table_columns(con: sqlite3.Connection, table_name: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def table_info(con: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    return con.execute(f"PRAGMA table_info({table_name})").fetchall()


def create_user_indexes(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_site_username
        ON users(site_code, username)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_site_role
        ON users(site_code, role)
        """
    )


def create_users_table(con: sqlite3.Connection, table_name: str = "users") -> None:
    default_site = normalize_site_code(DEFAULT_SITE_CODE).replace("'", "''")
    con.execute(
        f"""
        CREATE TABLE {table_name} (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL DEFAULT '{default_site}',
          username TEXT NOT NULL,
          pw_hash TEXT NOT NULL,
          role TEXT NOT NULL,
          can_manage_vehicles INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def ensure_site_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS sites (
          site_code TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        "INSERT OR IGNORE INTO sites(site_code, name) VALUES (?, ?)",
        (normalize_site_code(DEFAULT_SITE_CODE), DEFAULT_SITE_NAME),
    )


def ensure_billing_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS site_billing (
          site_code TEXT PRIMARY KEY,
          plan TEXT NOT NULL DEFAULT 'trial',
          status TEXT NOT NULL DEFAULT 'trialing',
          trial_ends_at TEXT,
          current_period_ends_at TEXT,
          payment_provider TEXT NOT NULL DEFAULT 'manual',
          external_customer_id TEXT,
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_inquiries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL,
          requested_plan TEXT NOT NULL,
          contact_name TEXT,
          contact_phone TEXT,
          contact_email TEXT,
          message TEXT,
          status TEXT NOT NULL DEFAULT 'new',
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS google_play_purchases (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL,
          username TEXT NOT NULL,
          package_name TEXT NOT NULL,
          product_id TEXT NOT NULL,
          plan TEXT NOT NULL,
          purchase_token TEXT NOT NULL UNIQUE,
          order_id TEXT,
          subscription_state TEXT,
          acknowledgement_state TEXT,
          expires_at TEXT,
          raw_response_json TEXT,
          verified_at TEXT NOT NULL DEFAULT (datetime('now')),
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_billing_inquiries_site_created_at
        ON billing_inquiries(site_code, created_at)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_google_play_purchases_site_verified
        ON google_play_purchases(site_code, verified_at)
        """
    )
    con.execute(
        """
        INSERT OR IGNORE INTO site_billing(site_code, plan, status, trial_ends_at, payment_provider)
        SELECT site_code, 'trial', 'trialing', date('now', '+14 days'), ?
        FROM sites
        """,
        (BILLING_PROVIDER,),
    )


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
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_active_order
        ON cctv_search_requests(site_code, status, work_weight, search_start_time, created_at)
        """
    )


def create_core_query_indexes(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_site_deleted_updated
        ON vehicles(site_code, deleted_at, updated_at)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_site_deleted_unit
        ON vehicles(site_code, deleted_at, unit)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_site_deleted_owner
        ON vehicles(site_code, deleted_at, owner_name)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicles_site_deleted_phone
        ON vehicles(site_code, deleted_at, phone)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_enforcement_site_id
        ON enforcement_events(site_code, id)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_enforcement_site_verdict_id
        ON enforcement_events(site_code, verdict, id)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_enforcement_site_plate_id
        ON enforcement_events(site_code, plate, id)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_import_runs_site_id
        ON import_runs(site_code, id)
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
    info = table_info(con, "users")
    if not info:
        return
    columns = {row["name"] for row in info}
    username_is_primary_key = any(row["name"] == "username" and int(row["pk"]) > 0 for row in info)

    if "id" not in columns or "site_code" not in columns or username_is_primary_key:
        con.execute("DROP TABLE IF EXISTS users_new")
        create_users_table(con, "users_new")

        site_expr = "COALESCE(NULLIF(site_code, ''), ?)" if "site_code" in columns else "?"
        role_expr = "COALESCE(NULLIF(role, ''), 'cleaner')" if "role" in columns else "'cleaner'"
        created_expr = "COALESCE(created_at, datetime('now'))" if "created_at" in columns else "datetime('now')"
        con.execute(
            f"""
            INSERT OR IGNORE INTO users_new(site_code, username, pw_hash, role, created_at)
            SELECT {site_expr}, username, pw_hash, {role_expr}, {created_expr}
            FROM users
            WHERE username IS NOT NULL AND username != ''
            """,
            (normalize_site_code(DEFAULT_SITE_CODE),),
        )
        con.execute("DROP TABLE users")
        con.execute("ALTER TABLE users_new RENAME TO users")
        columns = table_columns(con, "users")

    con.execute(
        "UPDATE users SET site_code = ? WHERE site_code IS NULL OR site_code = ''",
        (normalize_site_code(DEFAULT_SITE_CODE),),
    )
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
    create_user_indexes(con)

    for row in con.execute("SELECT DISTINCT site_code FROM users WHERE site_code IS NOT NULL AND site_code != ''").fetchall():
        site_code = normalize_site_code(row["site_code"])
        con.execute("INSERT OR IGNORE INTO sites(site_code, name) VALUES (?, ?)", (site_code, site_code))


def ensure_vehicle_schema(con: sqlite3.Connection) -> None:
    columns = table_columns(con, "vehicles")
    if not columns:
        return
    if "building" not in columns:
        con.execute("ALTER TABLE vehicles ADD COLUMN building TEXT")
    if "unit_number" not in columns:
        con.execute("ALTER TABLE vehicles ADD COLUMN unit_number TEXT")
    if "manual_override" not in columns:
        con.execute("ALTER TABLE vehicles ADD COLUMN manual_override INTEGER NOT NULL DEFAULT 0")
    if "deleted_at" not in columns:
        con.execute("ALTER TABLE vehicles ADD COLUMN deleted_at TEXT")


def ensure_vehicle_management_schema(con: sqlite3.Connection) -> None:
    if "can_manage_vehicles" not in table_columns(con, "users"):
        con.execute("ALTER TABLE users ADD COLUMN can_manage_vehicles INTEGER NOT NULL DEFAULT 0")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_backups (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL,
          backup_name TEXT NOT NULL,
          vehicles_json TEXT NOT NULL,
          vehicles_count INTEGER NOT NULL DEFAULT 0,
          created_by TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS vehicle_change_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_code TEXT NOT NULL,
          username TEXT,
          action TEXT NOT NULL,
          plate TEXT,
          before_json TEXT,
          after_json TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicle_backups_site_created
        ON vehicle_backups(site_code, created_at)
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_vehicle_change_logs_site_created
        ON vehicle_change_logs(site_code, created_at)
        """
    )
    create_core_query_indexes(con)


def init_db() -> None:
    schema_path = BASE_DIR / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with connect() as con:
        con.executescript(schema_sql)
        ensure_vehicle_schema(con)
        ensure_vehicle_management_schema(con)
        ensure_site_schema(con)
        ensure_billing_schema(con)
        ensure_cctv_request_schema(con)
        ensure_user_role_schema(con)
        create_core_query_indexes(con)
        ensure_billing_schema(con)
        con.commit()


def seed_users() -> None:
    from .auth import pbkdf2_hash

    site_code = normalize_site_code(DEFAULT_SITE_CODE)
    demo_users = [
        (site_code, "admin", pbkdf2_hash("admin1234"), "admin"),
        (site_code, "guard", pbkdf2_hash("guard1234"), "guard"),
        (site_code, "cleaner", pbkdf2_hash("cleaner1234"), "cleaner"),
    ]
    with connect() as con:
        con.execute("INSERT OR IGNORE INTO sites(site_code, name) VALUES (?, ?)", (site_code, DEFAULT_SITE_NAME))
        existing = con.execute("SELECT COUNT(*) AS cnt FROM users WHERE site_code = ?", (site_code,)).fetchone()
        if int(existing["cnt"]) > 0:
            return
        con.executemany(
            "INSERT INTO users(site_code, username, pw_hash, role) VALUES (?, ?, ?, ?)",
            demo_users,
        )
        con.commit()


def maybe_seed_demo() -> None:
    if not SEED_DEMO:
        return

    site_code = normalize_site_code(DEFAULT_SITE_CODE)
    demo_rows = [
        (site_code, "12가3456", "101-1203", "101", "1203", "홍길동", "010-1111-2222", "active", "2026-01-01", "2027-12-31", "상시 등록", "demo.xlsx", "vehicles"),
        (site_code, "34나5678", "102-803", "102", "803", "김영희", "010-2222-3333", "blocked", None, None, "관리소 차단 차량", "demo.xlsx", "vehicles"),
        (site_code, "123다4567", "103-1502", "103", "1502", "이철수", "010-3333-4444", "temp", "2026-04-01", "2026-04-30", "임시 등록", "demo.xlsx", "vehicles"),
    ]
    with connect() as con:
        exists = con.execute("SELECT COUNT(*) AS cnt FROM vehicles WHERE site_code = ?", (site_code,)).fetchone()
        if int(exists["cnt"]) > 0:
            return
        con.executemany(
            """
            INSERT OR IGNORE INTO vehicles
            (site_code, plate, unit, building, unit_number, owner_name, phone, status, valid_from, valid_to, note, source_file, source_sheet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo_rows,
        )
        con.commit()


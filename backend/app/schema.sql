PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS vehicles (
  site_code TEXT NOT NULL,
  plate TEXT NOT NULL,
  unit TEXT,
  owner_name TEXT,
  phone TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  valid_from TEXT,
  valid_to TEXT,
  note TEXT,
  source_file TEXT,
  source_sheet TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (site_code, plate)
);

CREATE TABLE IF NOT EXISTS import_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_code TEXT NOT NULL,
  source_dir TEXT NOT NULL,
  files_count INTEGER NOT NULL DEFAULT 0,
  rows_count INTEGER NOT NULL DEFAULT 0,
  imported_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL,
  message TEXT
);

CREATE TABLE IF NOT EXISTS enforcement_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_code TEXT NOT NULL,
  plate TEXT NOT NULL,
  raw_ocr_text TEXT,
  verdict TEXT NOT NULL,
  verdict_message TEXT NOT NULL,
  unit TEXT,
  owner_name TEXT,
  vehicle_status TEXT,
  inspector TEXT,
  location TEXT,
  memo TEXT,
  photo_path TEXT,
  lat REAL,
  lng REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cctv_search_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_code TEXT NOT NULL,
  requester_username TEXT NOT NULL,
  photo_path TEXT NOT NULL,
  location TEXT NOT NULL,
  search_time TEXT NOT NULL,
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
);

CREATE TABLE IF NOT EXISTS ocr_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_code TEXT NOT NULL,
  raw_key TEXT,
  raw_ocr_text TEXT,
  suggested_plate TEXT,
  corrected_plate TEXT NOT NULL,
  accepted INTEGER NOT NULL DEFAULT 0,
  candidates_json TEXT,
  photo_path TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  pw_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vehicles_site_plate ON vehicles(site_code, plate);
CREATE INDEX IF NOT EXISTS idx_enforcement_site_created_at ON enforcement_events(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_status_time ON cctv_search_requests(site_code, status, search_time);
CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_requester ON cctv_search_requests(site_code, requester_username);
CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_assignee ON cctv_search_requests(site_code, assigned_to);
CREATE INDEX IF NOT EXISTS idx_import_runs_site_imported_at ON import_runs(site_code, imported_at);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_created_at ON ocr_feedback(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_raw_key ON ocr_feedback(site_code, raw_key);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_suggested ON ocr_feedback(site_code, suggested_plate);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_corrected ON ocr_feedback(site_code, corrected_plate);


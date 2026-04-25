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

CREATE TABLE IF NOT EXISTS sites (
  site_code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_code TEXT NOT NULL DEFAULT 'APT1100',
  username TEXT NOT NULL,
  pw_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS site_billing (
  site_code TEXT PRIMARY KEY,
  plan TEXT NOT NULL DEFAULT 'trial',
  status TEXT NOT NULL DEFAULT 'trialing',
  trial_ends_at TEXT,
  current_period_ends_at TEXT,
  payment_provider TEXT NOT NULL DEFAULT 'manual',
  external_customer_id TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

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
);

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
);

CREATE INDEX IF NOT EXISTS idx_vehicles_site_plate ON vehicles(site_code, plate);
CREATE INDEX IF NOT EXISTS idx_enforcement_site_created_at ON enforcement_events(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_requester ON cctv_search_requests(site_code, requester_username);
CREATE INDEX IF NOT EXISTS idx_cctv_requests_site_assignee ON cctv_search_requests(site_code, assigned_to);
CREATE INDEX IF NOT EXISTS idx_import_runs_site_imported_at ON import_runs(site_code, imported_at);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_created_at ON ocr_feedback(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_raw_key ON ocr_feedback(site_code, raw_key);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_suggested ON ocr_feedback(site_code, suggested_plate);
CREATE INDEX IF NOT EXISTS idx_ocr_feedback_site_corrected ON ocr_feedback(site_code, corrected_plate);
CREATE INDEX IF NOT EXISTS idx_sites_created_at ON sites(created_at);
CREATE INDEX IF NOT EXISTS idx_billing_inquiries_site_created_at ON billing_inquiries(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_google_play_purchases_site_verified ON google_play_purchases(site_code, verified_at);

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

CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  pw_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vehicles_site_plate ON vehicles(site_code, plate);
CREATE INDEX IF NOT EXISTS idx_enforcement_site_created_at ON enforcement_events(site_code, created_at);
CREATE INDEX IF NOT EXISTS idx_import_runs_site_imported_at ON import_runs(site_code, imported_at);


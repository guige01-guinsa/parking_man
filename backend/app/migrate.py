from pathlib import Path

from .db import DEFAULT_SITE_CODE, init_db, maybe_seed_demo, seed_users
from .excel_import import sync_registry_from_dir


def main() -> None:
    init_db()
    seed_users()
    maybe_seed_demo()
    imports_dir = Path(__file__).resolve().parent.parent / "imports"
    if imports_dir.exists():
        try:
            summary = sync_registry_from_dir(imports_dir, DEFAULT_SITE_CODE)
            print(summary)
        except Exception as exc:
            print(f"registry sync skipped: {exc}")


if __name__ == "__main__":
    main()


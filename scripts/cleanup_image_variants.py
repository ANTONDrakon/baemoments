from __future__ import annotations

import re
from pathlib import Path


MASTER_RE = re.compile(r"^dress-\d{2}\.(jpg|webp|avif)$", re.IGNORECASE)
VARIANT_RE = re.compile(r"^dress-\d{2}-\d{3,4}\.(jpg|webp|avif)$", re.IGNORECASE)


def main() -> int:
    images_dir = Path("images")
    if not images_dir.exists():
        raise SystemExit("images/ not found")

    removed = 0
    for p in images_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if not name.lower().startswith("dress-"):
            continue
        if MASTER_RE.match(name) or VARIANT_RE.match(name):
            continue
        # Remove any accidental nested variants like dress-01-320-320.avif etc.
        try:
            p.unlink()
            removed += 1
        except Exception as e:
            raise SystemExit(f"Failed to remove {p}: {e}") from e

    print(f"Removed {removed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


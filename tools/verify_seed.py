"""Check immutable archival copies and the originals when available locally."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "docs/SEED_MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        archive = ROOT / entry["archive"]
        if hashlib.sha256(archive.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"Immutable archive changed: {entry['archive']}")
        original = Path(entry["original"])
        if original.exists() and hashlib.sha256(original.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"Original seed changed: {original.name}")
    print(f"Verified {len(manifest['files'])} immutable seed archives; available originals also match.")


if __name__ == "__main__":
    main()

"""Execute checks and write actual outputs plus a source-hash receipt."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    receipts = root / "receipts"
    receipts.mkdir(exist_ok=True)
    checks = [
        ("seed_integrity", [sys.executable, "tools/verify_seed.py"], root),
        ("ingestion", [sys.executable, "-m", "unittest", "discover", "-s", "backend/tests", "-v"], root),
        ("untouched_master", [sys.executable, "-m", "unittest", "test_spatial_engine", "-v"], root / "reference/seed"),
        ("dependency_consistency", [sys.executable, "-m", "pip", "check"], root),
        ("syntax", [sys.executable, "-m", "compileall", "-q", "backend", "tools", "demo_runner.py"], root),
    ]
    results = []
    for name, command, cwd in checks:
        result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
        output = result.stdout
        output_path = receipts / f"{name}.txt"
        output_path.write_text(output, encoding="utf-8", newline="\n")
        match = re.search(r"Ran (\d+) tests? in", output)
        results.append({"name": name, "exit_code": result.returncode, "tests_run": int(match.group(1)) if match else None,
                        "output_file": f"receipts/{name}.txt", "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest()})
        print(f"{name}: exit={result.returncode}" + (f", tests={match.group(1)}" if match else ""), flush=True)
    source_paths = [*root.glob("requirements*"), root / "docker-compose.yml", root / "Dockerfile", root / "demo_runner.py",
                    *root.glob("backend/**/*.py"), *root.glob("tools/*.py"), *root.glob(".github/workflows/*.yml")]
    manifest = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(source_paths)) if p.is_file()}
    summary = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "checks": results,
               "source_sha256": manifest, "live_lta_acceptance": False, "physical_device_acceptance": False,
               "cloud_ci_executed": False, "postgis_redis_gate_passed": False}
    (receipts / "checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    if any(result["exit_code"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

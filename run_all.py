"""Rebuild the panel and results.json from data/input, into build/ (one command: python run_all.py).

Runs the steps listed in README.md, in order, each in its own process, and stops at the first failure. Nothing is
downloaded. Compare with: python -m pytest code/tests/test_reproduction.py

It first empties build/interim, build/processed and build/output (4.0.0), so files from an earlier run can never pass
or fail the tests, and writes build/run_stamp.json: the SHA-256 of every file in code/src and code/manifest when the
run started. The reproduction tests fail if the stamp is missing or the code has changed since. WTNGD_BUILD sets
another build folder; only those three folders and the stamp in it are removed.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "code" / "src"
BUILD = Path(os.environ.get("WTNGD_BUILD", str(REPO / "build")))
STEPS = [
    ('01_check_manifest.py', []),
    ('02b_reporting_areas.py', []),
    ('03_parse_dirs.py', []),
    ('04_validate_dirs.py', []),
    ('05_fips.py', []),
    ('06_eaglei.py', []),
    ('07_nhc.py', []),
    ('08_fema_svi_bdc.py', []),
    ('09_build_panel.py', []),
    ('10_analysis.py', ['3', '4', '5', '6', '7', '8', '9']),
    ('10_analysis.py', ['1', '2']),
    ('12_v2_analysis.py', ['v2_1', 'v2_2', 'v2_3', 'v2_5_groups', 'v2_5', 'report_card']),
    ('12b_analysis_ready.py', []),
    ('15_external_validation.py', []),
    ('16_fema_ia.py', []),
    ('17_cable_wireline.py', []),
    ('18_hazard_ncei.py', []),
    ('15b_external_michael_olukola.py', []),
]


def code_digest() -> str:
    h = hashlib.sha256()
    for folder in (REPO / "code" / "src", REPO / "code" / "manifest"):
        for p in sorted(folder.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                h.update(p.relative_to(REPO).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def clear_build() -> None:
    for name in ("interim", "processed", "output"):
        shutil.rmtree(BUILD / name, ignore_errors=True)
    (BUILD / "run_stamp.json").unlink(missing_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)


def main():
    t0 = time.time()
    clear_build()
    stamp = {"code_sha256": code_digest(), "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "complete": False}
    (BUILD / "run_stamp.json").write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")
    for script, args in STEPS:
        print(f"== {script} {' '.join(args)}", flush=True)
        r = subprocess.run([sys.executable, script, *args], cwd=SRC)
        if r.returncode:
            raise SystemExit(f"{script} failed (exit {r.returncode})")
    stamp["complete"] = True
    (BUILD / "run_stamp.json").write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")
    print(f"done in {(time.time() - t0) / 60:.1f} min; outputs in {BUILD}")


if __name__ == "__main__":
    main()

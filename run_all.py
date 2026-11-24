"""Rebuild the panel and results.json from data/input, into build/ (one command: python run_all.py).

Runs the steps listed in README.md, in order, each in its own process, and stops at the first failure. Nothing is
downloaded. Compare with: python -m pytest code/tests/test_reproduction.py
"""
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "code" / "src"
STEPS = [
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
]


def main():
    t0 = time.time()
    for script, args in STEPS:
        print(f"== {script} {' '.join(args)}", flush=True)
        r = subprocess.run([sys.executable, script, *args], cwd=SRC)
        if r.returncode:
            raise SystemExit(f"{script} failed (exit {r.returncode})")
    print(f"done in {(time.time() - t0) / 60:.1f} min; outputs in build/")


if __name__ == "__main__":
    main()

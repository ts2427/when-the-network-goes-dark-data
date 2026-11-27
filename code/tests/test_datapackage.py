"""datapackage.json is a valid Data Package: frictionless validate datapackage.json gives 0 errors (v2.2.0).

Checks the descriptor and every tabular resource's rows against its schema (types, required values, primary keys)."""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def test_datapackage_validates_with_no_errors():
    frictionless = pytest.importorskip("frictionless", reason="pip install frictionless (in requirements.txt)")
    report = frictionless.validate(str(REPO / "datapackage.json"))
    errors = [e.message for e in report.errors]
    for task in report.tasks:
        errors += [f"{task.name}: {e.message}" for e in task.errors]
    assert report.valid and not errors, errors[:20]


def test_every_resource_hash_matches():
    """Each resource's SHA-256 (since 3.2.1 the Parquet's too, which frictionless does not check) matches its file."""
    import hashlib
    import json
    pkg = json.loads((REPO / "datapackage.json").read_text(encoding="utf-8"))
    for r in pkg["resources"]:
        if "hash" in r:
            got = "sha256:" + hashlib.sha256((REPO / r["path"]).read_bytes()).hexdigest()
            assert got == r["hash"], r["path"]


def test_byte_counts_match():
    """bytes where the resource has the field; for the Parquet, the count in its description (4.0.0)."""
    import json
    import re
    pkg = json.loads((REPO / "datapackage.json").read_text(encoding="utf-8"))
    for r in pkg["resources"]:
        size = (REPO / r["path"]).stat().st_size
        if "bytes" in r:
            assert r["bytes"] == size, r["path"]
        elif r["format"] == "parquet":
            assert re.search(rf"; {size} bytes\.", r["description"]), r["path"]

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

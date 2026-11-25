""".zenodo.json (v3.1.1): valid against Zenodo's legacy deposit schema (plus version) and built from CITATION.cff.

Zenodo uses .zenodo.json instead of CITATION.cff when it archives a GitHub release ("If your repository contains both
a .zenodo.json and a CITATION.cff file, Zenodo will only use the .zenodo.json metadata", help.zenodo.org), so the
deposit's type (dataset), keywords and related identifiers come from this file.
"""
import copy
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from config import PROCESSED  # noqa: E402

SCHEMA = ROOT / "tests" / "schemas" / "zenodo_legacyrecord.json"
PUBLIC = ROOT.parent  # the public repository's root (code/tests -> code -> repo)
needs_panel = pytest.mark.skipif(not (PROCESSED / "dirs_county_day.csv").exists(),
                                 reason="step 14 reads the published panel: run the pipeline first")


def schema() -> dict:
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    s = copy.deepcopy(s)
    s["properties"]["version"] = {"type": "string"}  # documented by Zenodo for .zenodo.json; see tests/schemas/README.md
    return s


def metadata() -> tuple:
    """(.zenodo.json, CITATION.cff text): the published files in the public repository, else built here."""
    if (PUBLIC / ".zenodo.json").exists() and (PUBLIC / "CITATION.cff").exists():
        return (json.loads((PUBLIC / ".zenodo.json").read_text(encoding="utf-8")),
                (PUBLIC / "CITATION.cff").read_text(encoding="utf-8"))
    if not (PROCESSED / "dirs_county_day.csv").exists():
        pytest.skip("step 14 reads the published panel: run the pipeline first")
    import tempfile
    m = importlib.import_module("14_data_repo")
    d = Path(tempfile.mkdtemp())
    m.citation_cff(d)
    m.zenodo_json(d)
    return json.loads((d / ".zenodo.json").read_text(encoding="utf-8")), (d / "CITATION.cff").read_text(encoding="utf-8")


def test_zenodo_json_validates_against_the_legacy_deposit_schema():
    jsonschema = pytest.importorskip("jsonschema")
    meta, _ = metadata()
    jsonschema.Draft4Validator(schema()).validate(meta)
    assert meta["upload_type"] == "dataset" and meta["access_right"] == "open"


def test_zenodo_json_agrees_with_citation_cff():
    import yaml
    meta, cff_text = metadata()
    cff = yaml.safe_load(cff_text)
    assert meta["title"] == cff["title"] and meta["version"] == str(cff["version"])
    assert meta["publication_date"] == str(cff["date-released"]) and meta["license"] == cff["license"]
    assert meta["keywords"] == cff["keywords"]
    assert [c["orcid"] for c in meta["creators"]] == [a["orcid"].removeprefix("https://orcid.org/") for a in cff["authors"]]


def test_related_identifiers_are_the_verified_table():
    import pandas as pd
    meta, _ = metadata()
    rel = pd.read_csv(ROOT / "manifest" / "related_identifiers.csv", dtype=str, keep_default_na=False)
    assert (rel.verified != "").all()
    assert [r["identifier"] for r in meta["related_identifiers"]] == rel.identifier.tolist()
    want = {"isDocumentedBy": 1, "isDerivedFrom": 1}
    got = rel.relation.value_counts().to_dict()
    assert all(got.get(k) == n for k, n in want.items()) and got["references"] == len(rel) - 2
    for r in meta["related_identifiers"]:
        if r["scheme"] == "doi":
            assert r["identifier"].startswith("10.")
        if r["scheme"] == "url":
            assert r["identifier"].startswith("https://")


@needs_panel
def test_the_schema_rejects_a_wrong_upload_type():
    jsonschema = pytest.importorskip("jsonschema")
    meta, _ = metadata()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft4Validator(schema()).validate({**meta, "upload_type": "spreadsheet"})

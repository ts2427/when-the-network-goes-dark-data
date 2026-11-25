"""The page restructure of 2026-11-25: new order, same numbers.

Every line of the page as it was before (tests/snapshots/page_before_restructure.md) that holds a number is on the
new page word for word, or is one of the deliberate changes listed below, whose numbers all appear on the new page.
Every number in "What it adds up to" appears in the chapter it comes from. Old anchors still resolve.
"""
import importlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
step11 = importlib.import_module("11_build_page")
from config import OUTPUT  # noqa: E402

BEFORE = ROOT / "tests" / "snapshots" / "page_before_restructure.md"
RESULTS = OUTPUT / "results.json"
built = pytest.mark.skipif(not step11.PAGE.exists() or not RESULTS.exists(),
                           reason="needs the built page and results.json (private project, after step 11)")
results = pytest.mark.skipif(not RESULTS.exists() or not (OUTPUT / "external_validation_fcc_2017.csv").exists(),
                             reason="needs results.json and step 15's table from a build: run python run_all.py first")

# Lines that change on purpose, by how they start: headings and tags (renumbered or retagged), the opening's former
# "What version 2 adds" (now marked Exploratory in one list), the Method and Data sources boxes (merged into Sources),
# lines whose chapter references are renumbered, and the Sources entries (links merged in).
CHANGED = ("## ", "### What version 2 adds", "*Exploratory:", "Exploratory: added after version 1", "- In all ",
           "- The FCC printed sites operating", "- Where the order could be determined", "- In storms from 2022 on",
           "Everything here is descriptive", "method: ", "  - name: ", "    url: ", "    caption: \"Each row is a storm",
           "**What it means.** With wind zone in the model", "**Intervals.**", "**Mobile and fixed providers (chapter 13)",
           "- Olukola, O.", "- Federal Communications Commission.", "- National Hurricane Center.", "- CDC/ATSDR")
# Release metadata, not results: the data release moved from 3.0.0 to 3.1.0 (version, DOI, file, Updated date).
RELEASE = ('updated: "', 'dataset: {"name": ', "**Reproduce it.**",
           "Each report's flags and reasons are in the snapshot's")  # its link is pinned to the release tag
NOT_VALUES = re.compile(r"(?i)chapters? \d+(?:(?:, | to | and )\d+)*|^#+ \d+\.|version \d+(?:\.\d+)*|"
                        r"\(chapter 13\)|chapter 12\)|2\.1\.0")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> set:
    return {n.rstrip(".,") for n in NUMBER.findall(NOT_VALUES.sub(" ", text))}


@built
def test_every_number_on_the_old_page_is_on_the_new_page():
    old = BEFORE.read_text(encoding="utf-8")
    new = step11.PAGE.read_text(encoding="utf-8")
    changed = [ln for ln in old.splitlines() if NUMBER.search(ln) and ln.strip() and ln not in new
               and not ln.startswith(RELEASE)]
    unexpected = [ln for ln in changed if not ln.startswith(CHANGED)]
    assert not unexpected, unexpected[:5]
    new_numbers = numbers(new)
    for ln in changed:
        assert numbers(ln) <= new_numbers, (ln[:120], numbers(ln) - new_numbers)
    kept = sum(1 for ln in old.splitlines() if NUMBER.search(ln) and ln.strip() and ln in new)
    assert kept >= 400 and len(changed) <= 50  # almost every line is unchanged, word for word


@built
def test_old_anchors_resolve_and_new_headings_have_ids():
    new = step11.PAGE.read_text(encoding="utf-8")
    old_ids = ["what-i-found", "what-version-2-adds", "how-to-read-it", "1-the-question-and-the-data",
               "2-anatomy-of-a-storm-isaias-october-2026", "3-how-much-goes-dark", "4-how-fast-it-comes-back",
               "5-why-sites-go-dark", "6-the-power-coupling", "7-exposure", "8-who-waits-longest", "9-did-the-rules-help",
               "10-what-the-public-record-misses", "11-sites-on-backup-power",
               "12-which-comes-back-first-power-or-cell-service",
               "13-do-counties-with-more-mobile-providers-recover-differently",
               "14-how-complete-are-the-fccs-public-reports", "methods-data-and-licenses"]
    for i in old_ids:
        slug_heading = {"what-i-found": "### What I found", "how-to-read-it": "### How to read it"}.get(i)
        assert f"{{#{i}}}" in new or f'id="{i}"' in new or (slug_heading and slug_heading in new), i
    for h in ("## What it adds up to", "### Audit trail {#audit-trail}", "## Download the data",
              "## Part I: What happens when the network goes dark", "## Part IV: What the public record can and can't tell us"):
        assert h in new


@built
def test_chapters_are_numbered_1_to_12_in_order_and_version_words_are_gone():
    new = step11.PAGE.read_text(encoding="utf-8")
    nums = [int(m) for m in re.findall(r"^### (\d+)\. ", new, re.M)]
    assert nums == list(range(1, 13))
    body = new.split("---\n", 2)[2]
    start = body.index("### Audit trail")
    audit = body[start:body.index("</details>", start)]
    reader = body.replace(audit, "")
    assert not re.search(r"(?i)version [12]\b|version 2\.1|What version 2 adds", reader)
    assert new.count('<p class="tag-exploratory">Exploratory</p>') == 5  # old chapters 10 to 14
    for ref in re.findall(r"(?i)chapters? \d[^.;)]*", reader):  # every reference uses the page's numbers
        assert all(int(n) <= 12 for n in re.findall(r"\d+", ref)), ref
    assert "chapter 13" not in reader and "chapter 14" not in reader


@results
def test_every_takeaway_number_appears_in_its_chapter():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    blocks = {**step11.chapter_blocks(r), **step11.v2_blocks(r), "external": [step11.external_check_paragraph()]}
    items = step11.takeaways(r)
    assert [w for w, _, _ in items] == ["emergency managers", "carriers", "regulators", "researchers"]
    for who, text, sources in items:
        source_text = "\n".join("\n".join(blocks[k]) for k in sources)
        missing = numbers(text) - numbers(source_text)
        assert not missing, (who, missing)


@results
def test_takeaways_use_association_language_only():
    r = json.loads(RESULTS.read_text(encoding="utf-8"))
    text = " ".join(t for _, t, _ in step11.takeaways(r)).lower()
    for word in ("caused", "causes the", "because of", "leads to", "led to", "results in", "drives", "error"):
        assert word not in text, word


def test_renumber_stops_on_a_reference_that_is_not_there():
    with pytest.raises(ValueError, match="chapter reference not found"):
        step11.renumber("no references here", [("chapter 3", "chapter 2")])

"""Tests for tools/control_lookup.py. Run with:  python -m pytest"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from control_lookup import Catalog, main, normalize_id  # noqa: E402


@pytest.fixture(scope="module")
def cat():
    return Catalog.load()


# ---------------------------------------------------------------- ID normalization

@pytest.mark.parametrize("raw, expected", [
    ("AC-2", "ac-2"),
    ("ac-2", "ac-2"),
    ("AC-02", "ac-2"),
    ("AC 2", "ac-2"),
    ("AC-2(1)", "ac-2.1"),
    ("ac-2 (1)", "ac-2.1"),
    ("AC-02(01)", "ac-2.1"),
    ("ac-2.1", "ac-2.1"),
    ("SC-7(21)", "sc-7.21"),
])
def test_normalize_id_accepts_common_forms(raw, expected):
    assert normalize_id(raw) == expected


@pytest.mark.parametrize("bad", ["", "AC", "2", "ACC-2", "AC-2(", "hello"])
def test_normalize_id_rejects_garbage(bad):
    with pytest.raises(ValueError):
        normalize_id(bad)


# ---------------------------------------------------------------- catalog contents

def test_catalog_has_all_20_families(cat):
    assert len(cat.families) == 20
    assert cat.families["AC"] == "Access Control"
    assert cat.families["SR"] == "Supply Chain Risk Management"


def test_catalog_size_is_plausible(cat):
    base = [c for c in cat.controls.values() if not c.is_enhancement]
    enh = [c for c in cat.controls.values() if c.is_enhancement]
    assert len(base) > 300
    assert len(enh) > 800


def test_get_base_control(cat):
    c = cat.get("AC-2")
    assert c.id == "AC-2"
    assert c.title == "Account Management"
    assert c.family_id == "AC"
    assert not c.is_enhancement
    assert not c.withdrawn
    assert "AC-2(1)" in c.enhancements
    assert "IA-2" in c.related


def test_get_enhancement(cat):
    c = cat.get("IA-2(1)")
    assert c.is_enhancement
    assert c.parent == "IA-2"
    assert "multi-factor authentication" in c.statement.lower()


def test_parameters_are_rendered_not_left_as_placeholders(cat):
    for c in cat.controls.values():
        assert "{{" not in c.statement, f"unrendered parameter in {c.id}"
        assert "{{" not in c.guidance, f"unrendered parameter in {c.id} guidance"


def test_assignment_and_selection_rendering(cat):
    assert "[Assignment:" in cat.get("AC-2").statement
    assert "[Selection (one or more):" in cat.get("AC-1").statement


def test_withdrawn_control_points_to_replacement(cat):
    c = cat.get("AC-2(10)")
    assert c.withdrawn
    assert c.withdrawn_to == ["AC-2"]


def test_unknown_control_raises_key_error(cat):
    with pytest.raises(KeyError):
        cat.get("AC-999")


def test_family_listing_excludes_enhancements_and_withdrawn_by_default(cat):
    ctls = cat.family("ir")
    assert all(c.family_id == "IR" and not c.is_enhancement and not c.withdrawn for c in ctls)
    assert "IR-8" in [c.id for c in ctls]


def test_unknown_family_raises(cat):
    with pytest.raises(KeyError):
        cat.family("ZZ")


# ---------------------------------------------------------------- search

def test_search_finds_mfa_controls(cat):
    ids = [c.id for c, _ in cat.search("multi-factor authentication", limit=5)]
    assert "IA-2(1)" in ids and "IA-2(2)" in ids


def test_search_ranks_the_obvious_control_first(cat):
    assert cat.search("incident response plan", limit=1)[0][0].id == "IR-8"
    assert cat.search("account management", limit=1)[0][0].id == "AC-2"


def test_search_family_filter(cat):
    hits = cat.search("training", family="AT", limit=50)
    assert hits and all(c.family_id == "AT" for c, _ in hits)


def test_search_requires_every_term(cat):
    assert cat.search("zzqx nonexistentword") == []


def test_search_excludes_withdrawn_by_default(cat):
    assert all(not c.withdrawn for c, _ in cat.search("account", limit=200))


# ---------------------------------------------------------------- command line

def test_cli_get_json(capsys):
    assert main(["get", "AC-2", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["id"] == "AC-2" and data["family_id"] == "AC"


def test_cli_search_prints_results(capsys):
    assert main(["search", "audit record", "--limit", "3"]) == 0
    assert "AU-" in capsys.readouterr().out


def test_cli_bad_id_returns_error_code(capsys):
    assert main(["get", "not-a-control"]) == 1
    assert "Error" in capsys.readouterr().err

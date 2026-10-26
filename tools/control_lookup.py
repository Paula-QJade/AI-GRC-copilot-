#!/usr/bin/env python3
"""Look up and search NIST SP 800-53 Rev. 5 controls from the official OSCAL catalog.

Usable two ways:

* As a command-line tool:
      python tools/control_lookup.py get AC-2
      python tools/control_lookup.py get "IA-2(1)" --json
      python tools/control_lookup.py search "multi-factor authentication" --limit 5
      python tools/control_lookup.py family IR
      python tools/control_lookup.py families

* As a library (the MCP server in phase 3 imports it):
      from control_lookup import Catalog
      cat = Catalog.load()
      cat.get("AC-2")

Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_CATALOG = (
    Path(__file__).resolve().parent.parent / "data" / "NIST_SP-800-53_rev5_catalog.json"
)

_PARAM_RE = re.compile(r"\{\{\s*insert:\s*param,\s*([\w.\-]+)\s*\}\}")
_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


# --------------------------------------------------------------------------- data model


@dataclass
class Control:
    """One control or control enhancement, with parameters rendered as readable text."""

    id: str  # official label, e.g. "AC-2" or "AC-2(1)"
    oscal_id: str  # catalog id, e.g. "ac-2" or "ac-2.1"
    title: str
    family_id: str  # e.g. "AC"
    family_title: str  # e.g. "Access Control"
    is_enhancement: bool
    parent: str | None  # parent control label for enhancements
    withdrawn: bool
    withdrawn_to: list[str] = field(default_factory=list)  # where a withdrawn control went
    statement: str = ""
    guidance: str = ""
    related: list[str] = field(default_factory=list)
    enhancements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- id handling


def normalize_id(raw: str) -> str:
    """Turn any common way of writing a control ID into the catalog form.

    "AC-2", "ac-2", "AC-02", "AC 2"            -> "ac-2"
    "AC-2(1)", "ac-2 (1)", "AC-02(01)", "ac-2.1" -> "ac-2.1"
    """
    s = raw.strip().lower().replace(" ", "")
    m = re.fullmatch(r"([a-z]{2})-?0*(\d+)(?:\(0*(\d+)\)|\.0*(\d+))?", s)
    if not m:
        raise ValueError(
            f"'{raw}' is not a valid 800-53 control ID. Use a form like AC-2 or AC-2(1)."
        )
    family, number, enh_paren, enh_dot = m.groups()
    enh = enh_paren or enh_dot
    return f"{family}-{int(number)}" + (f".{int(enh)}" if enh else "")


def _label_from_oscal(oscal_id: str) -> str:
    """'ac-2.1' -> 'AC-2(1)'."""
    base, _, enh = oscal_id.partition(".")
    return base.upper() + (f"({enh})" if enh else "")


# --------------------------------------------------------------------------- catalog


class Catalog:
    """An in-memory index of every control and enhancement in the catalog."""

    def __init__(self, raw_catalog: dict):
        self.version = raw_catalog["metadata"].get("version", "unknown")
        self.title = raw_catalog["metadata"].get("title", "")
        self.families: dict[str, str] = {}
        self._params: dict[str, dict] = {}
        self._raw: dict[str, dict] = {}
        self._family_of: dict[str, str] = {}
        self._parent_of: dict[str, str] = {}

        for group in raw_catalog["groups"]:
            fam = group["id"].upper()
            self.families[fam] = group["title"]
            self._index(group.get("controls", []), fam, parent=None)

        self.controls: dict[str, Control] = {
            oid: self._build(oid) for oid in self._raw
        }

    @classmethod
    def load(cls, path: str | Path = DEFAULT_CATALOG) -> "Catalog":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Catalog not found at {path}. See docs/data-sources.md to download it."
            )
        with path.open(encoding="utf-8") as f:
            return cls(json.load(f)["catalog"])

    # ---- indexing

    def _index(self, controls: list[dict], family: str, parent: str | None) -> None:
        for ctl in controls:
            oid = ctl["id"]
            self._raw[oid] = ctl
            self._family_of[oid] = family
            if parent:
                self._parent_of[oid] = parent
            for p in ctl.get("params", []):
                self._params[p["id"]] = p
            self._index(ctl.get("controls", []), family, parent=oid)

    # ---- rendering

    def _render_param(self, param_id: str, depth: int = 0) -> str:
        """Render a parameter the way NIST prints it: [Assignment: ...] or [Selection: ...]."""
        p = self._params.get(param_id)
        if p is None or depth > 5:
            return f"[{param_id}]"
        if "select" in p:
            sel = p["select"]
            how = sel.get("how-many")
            prefix = "Selection (one or more)" if how == "one-or-more" else "Selection"
            choices = [self._render_text(c, depth + 1) for c in sel.get("choice", [])]
            return f"[{prefix}: {'; '.join(choices)}]"
        # Many 800-53A parameters "aggregate" others and only carry a label.
        label = p.get("label")
        if label:
            return f"[Assignment: {label}]"
        guidelines = p.get("guidelines") or []
        if guidelines:
            return f"[Assignment: {guidelines[0].get('prose', '').rstrip(';')}]"
        return f"[Assignment: {param_id}]"

    def _render_text(self, text: str, depth: int = 0) -> str:
        return _PARAM_RE.sub(lambda m: self._render_param(m.group(1), depth), text or "")

    def _render_part(self, part: dict, indent: int = 0) -> list[str]:
        lines = []
        label = next(
            (p["value"] for p in part.get("props", []) if p["name"] == "label"), ""
        )
        prose = self._render_text(part.get("prose", ""))
        if prose or label:
            lines.append(("  " * indent) + f"{label} {prose}".strip())
        for sub in part.get("parts", []):
            lines.extend(self._render_part(sub, indent + 1))
        return lines

    def _build(self, oid: str) -> Control:
        raw = self._raw[oid]
        parts = {p["name"]: p for p in raw.get("parts", [])}
        status = [p["value"] for p in raw.get("props", []) if p["name"] == "status"]
        withdrawn = "withdrawn" in status

        statement = ""
        if "statement" in parts:
            smt = parts["statement"]
            lines = []
            if smt.get("prose"):
                lines.append(self._render_text(smt["prose"]))
            for sub in smt.get("parts", []):
                lines.extend(self._render_part(sub))
            statement = "\n".join(lines)

        guidance = self._render_text(parts.get("guidance", {}).get("prose", ""))

        related, moved_to = [], []
        for link in raw.get("links", []):
            target = link.get("href", "").lstrip("#")
            # Links to statement parts look like "ac-2_smt.k"; keep the control part.
            target_ctl = target.split("_")[0]
            if target_ctl not in self._raw:
                continue  # a bibliography reference, not a control
            if link.get("rel") == "related":
                related.append(_label_from_oscal(target_ctl))
            elif link.get("rel") in ("incorporated-into", "moved-to"):
                moved_to.append(_label_from_oscal(target_ctl))

        parent = self._parent_of.get(oid)
        family = self._family_of[oid]
        return Control(
            id=_label_from_oscal(oid),
            oscal_id=oid,
            title=raw["title"],
            family_id=family,
            family_title=self.families[family],
            is_enhancement=parent is not None,
            parent=_label_from_oscal(parent) if parent else None,
            withdrawn=withdrawn,
            withdrawn_to=moved_to,
            statement=statement,
            guidance=guidance,
            related=related,
            enhancements=[_label_from_oscal(c["id"]) for c in raw.get("controls", [])],
        )

    # ---- public API

    def get(self, control_id: str) -> Control:
        """Return one control. Raises KeyError if it does not exist."""
        oid = normalize_id(control_id)
        if oid not in self.controls:
            raise KeyError(f"{control_id} is not in NIST SP 800-53 Rev. 5 ({self.version}).")
        return self.controls[oid]

    def family(self, family_id: str, include_enhancements: bool = False,
               include_withdrawn: bool = False) -> list[Control]:
        """List the controls in one family, in catalog order."""
        fam = family_id.strip().upper()
        if fam not in self.families:
            raise KeyError(
                f"{family_id} is not a control family. Families: {', '.join(self.families)}"
            )
        return [
            c for c in self.controls.values()
            if c.family_id == fam
            and (include_enhancements or not c.is_enhancement)
            and (include_withdrawn or not c.withdrawn)
        ]

    def search(self, query: str, limit: int = 10, family: str | None = None,
               include_withdrawn: bool = False) -> list[tuple[Control, float]]:
        """Keyword search across titles, statements and guidance.

        Every word in the query must appear somewhere in the control. Results are ranked:
        a match in the title counts most, then the statement, then the guidance. An exact
        phrase match earns a bonus.
        """
        terms = _WORD_RE.findall(query.lower())
        if not terms:
            return []
        phrase = " ".join(terms)
        fam = family.strip().upper() if family else None

        results = []
        for c in self.controls.values():
            if c.withdrawn and not include_withdrawn:
                continue
            if fam and c.family_id != fam:
                continue
            title, stmt, gdn = c.title.lower(), c.statement.lower(), c.guidance.lower()
            words = {
                "title": set(_WORD_RE.findall(title)),
                "stmt": set(_WORD_RE.findall(stmt)),
                "gdn": set(_WORD_RE.findall(gdn)),
            }
            if not all(any(_matches(t, w) for w in words.values()) for t in terms):
                continue
            score = 0.0
            for t in terms:
                score += 5.0 * _matches(t, words["title"])
                score += 2.0 * _matches(t, words["stmt"])
                score += 0.5 * _matches(t, words["gdn"])
            if len(terms) > 1:
                if phrase in title:
                    score += 10
                elif phrase in stmt:
                    score += 4
                elif phrase in gdn:
                    score += 1
            if not c.is_enhancement:
                score += 1.0  # prefer a base control over an enhancement on a near-tie
            results.append((c, round(score, 2)))

        results.sort(key=lambda r: (-r[1], r[0].oscal_id))
        return results[:limit]


def _matches(term: str, words: set[str]) -> bool:
    """A term matches a word exactly or as its prefix ('authenticat' -> 'authentication')."""
    if term in words:
        return True
    if len(term) >= 4:
        return any(w.startswith(term) for w in words)
    return False


# --------------------------------------------------------------------------- output


def _wrap(text: str, indent: str = "  ", hanging: bool = True) -> str:
    """Wrap text to 96 columns. With hanging=True, list items like 'a. ...' keep their
    continuation lines aligned under the item text."""
    out = []
    for line in text.splitlines():
        lead = len(line) - len(line.lstrip(" "))
        hang = 3 if hanging else 0
        out.append(
            textwrap.fill(line.strip(), width=96,
                          initial_indent=indent + " " * lead,
                          subsequent_indent=indent + " " * (lead + hang))
        )
    return "\n".join(out)


def format_control(c: Control, show_guidance: bool = True) -> str:
    lines = [f"{c.id}  {c.title}", f"Family: {c.family_id} ({c.family_title})"]
    if c.is_enhancement:
        lines.append(f"Enhancement of: {c.parent}")
    if c.withdrawn:
        moved = ", ".join(c.withdrawn_to) or "not specified"
        lines.append(f"Status: WITHDRAWN (incorporated into {moved})")
        return "\n".join(lines)
    lines += ["", "Control statement:", _wrap(c.statement)]
    if show_guidance and c.guidance:
        lines += ["", "Discussion:", _wrap(c.guidance, hanging=False)]
    if c.related:
        lines += ["", "Related controls: " + ", ".join(c.related)]
    if c.enhancements:
        lines += ["Enhancements: " + ", ".join(c.enhancements)]
    return "\n".join(lines)


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="control_lookup",
        description="Look up and search NIST SP 800-53 Rev. 5 controls.",
    )
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG),
                        help="Path to the OSCAL catalog JSON (default: data/...)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get", help="Show one control or enhancement")
    p_get.add_argument("control_id", help='e.g. AC-2 or "AC-2(1)"')
    p_get.add_argument("--no-guidance", action="store_true", help="Omit the discussion text")
    p_get.add_argument("--json", action="store_true", help="Machine-readable output")

    p_search = sub.add_parser("search", help="Keyword search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--family", help="Restrict to one family, e.g. IA")
    p_search.add_argument("--include-withdrawn", action="store_true")
    p_search.add_argument("--json", action="store_true")

    p_fam = sub.add_parser("family", help="List the controls in a family")
    p_fam.add_argument("family_id", help="e.g. AC, IR, SR")
    p_fam.add_argument("--enhancements", action="store_true", help="Include enhancements")
    p_fam.add_argument("--json", action="store_true")

    p_fams = sub.add_parser("families", help="List all control families")
    p_fams.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    try:
        cat = Catalog.load(args.catalog)

        if args.cmd == "get":
            c = cat.get(args.control_id)
            print(json.dumps(c.to_dict(), indent=2) if args.json
                  else format_control(c, show_guidance=not args.no_guidance))

        elif args.cmd == "search":
            hits = cat.search(args.query, limit=args.limit, family=args.family,
                              include_withdrawn=args.include_withdrawn)
            if args.json:
                print(json.dumps([{"id": c.id, "title": c.title, "family": c.family_id,
                                   "score": s} for c, s in hits], indent=2))
            elif not hits:
                print(f'No controls match "{args.query}".')
            else:
                for c, s in hits:
                    print(f"{c.id:<10} {c.title}  (score {s})")

        elif args.cmd == "family":
            ctls = cat.family(args.family_id, include_enhancements=args.enhancements)
            if args.json:
                print(json.dumps([{"id": c.id, "title": c.title} for c in ctls], indent=2))
            else:
                print(f"{args.family_id.upper()}  {cat.families[args.family_id.upper()]}"
                      f"  ({len(ctls)} controls)")
                for c in ctls:
                    print(f"  {c.id:<10} {c.title}")

        elif args.cmd == "families":
            if args.json:
                print(json.dumps(cat.families, indent=2))
            else:
                for fid, title in cat.families.items():
                    n = len(cat.family(fid))
                    print(f"{fid}  {title}  ({n} controls)")

    except (KeyError, ValueError, FileNotFoundError) as e:
        msg = e.args[0] if e.args else str(e)
        print(f"Error: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

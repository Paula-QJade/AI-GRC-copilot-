# AI GRC Copilot

**A Claude Code toolkit for governance, risk and compliance work: control lookup, framework
mapping, vendor and AI risk assessment, and audit-ready reporting.**

GRC analysts spend hours finding the right control, mapping documents to frameworks and
writing up findings. AI GRC Copilot turns that work into repeatable, cited, reviewable
workflows built on Claude Code: MCP servers for authoritative framework data, skills that
codify assessment methodology, slash commands for common tasks and hooks that keep an audit
trail of every AI-assisted finding.

Built by **Paula Queen Baffoe-Bonnie**, lawyer and GRC / AI governance practitioner,
as a portfolio project. Read the build notes on [CyberJuris](https://cyberjuris.substack.com).

> **Status:** in progress. Phases 1-2 of 12 complete.

## What works today

`tools/control_lookup.py` looks up and searches all 1,196 controls and enhancements in
**NIST SP 800-53 Rev. 5** (release 5.2.0), straight from NIST's official machine-readable
OSCAL catalog. Organization-defined parameters are rendered the way NIST prints them, and
the 182 withdrawn controls point to where they moved.

```text
$ python tools/control_lookup.py search "multi-factor authentication" --limit 3
IA-2(1)    Multi-factor Authentication to Privileged Accounts  (score 25.0)
IA-2(2)    Multi-factor Authentication to Non-privileged Accounts  (score 25.0)
IA-10      Adaptive Authentication  (score 10.0)

$ python tools/control_lookup.py get "AC-2(10)"
AC-2(10)  Shared and Group Account Credential Change
Family: AC (Access Control)
Enhancement of: AC-2
Status: WITHDRAWN (incorporated into AC-2)
```

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/Paula-QJade/ai-grc-copilot.git
cd ai-grc-copilot
pip install -r requirements.txt

python tools/control_lookup.py families              # all 20 control families
python tools/control_lookup.py family IR             # one family
python tools/control_lookup.py get AC-2              # full control text
python tools/control_lookup.py get "IA-2(1)" --json  # machine-readable
python tools/control_lookup.py search "supply chain risk" --limit 5

python -m pytest                                     # run the test suite
```

## Roadmap

| Phase | Builds | Status |
| --- | --- | --- |
| 1 | Project setup and `CLAUDE.md` context | Done |
| 2 | Control lookup tool + tests | Done |
| 3 | MCP server exposing control lookup to Claude | Next |
| 4 | Framework crosswalk: CSF 2.0, 800-53, AI RMF, EU AI Act | Planned |
| 5 | Skills: vendor risk and AI impact assessment methodology | Planned |
| 6 | Slash commands: `/vendor-review`, `/policy-gap`, `/ai-risk-triage` | Planned |
| 7 | Hooks: audit trail for AI-assisted findings, personal-data guard | Planned |
| 8 | Multi-source vendor risk correlation | Planned |
| 9 | Report generators: risk register, gap report, executive memo | Planned |
| 10 | Capstone: end-to-end assessment of an AI patient-intake chatbot | Planned |
| 11 | Reviewer personas: auditor, privacy counsel, CISO | Planned |
| 12 | Cross-framework analysis for one AI system | Planned |

## Project rules

- **Synthetic data only.** All inputs describe a fictional organization,
  [Larkspur Community Health](samples/company-profile.md).
- **Cited findings.** Every mapping and rating names its control, article and source.
- **ISO by reference.** ISO/IEC 27001 and 42001 are cited by clause number only.
- **Human in the loop.** Outputs are drafts prepared with AI assistance for review by a
  qualified professional. The tool assists; a person decides.

See [`docs/data-sources.md`](docs/data-sources.md) for sources and reuse terms.

## Licence

Code: MIT (see [LICENSE](LICENSE)). NIST data: US government work, public domain in the US.

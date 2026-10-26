# AI GRC Copilot: project context for Claude Code

This file tells Claude Code what this project is, which data it may use, and the rules every
output must follow. Claude reads it at the start of every session in this folder.

## What this project is

AI GRC Copilot is a portfolio toolkit that helps a governance, risk and compliance (GRC)
analyst:

- look up and search security controls (NIST SP 800-53 Rev. 5)
- map policies, vendor evidence and AI systems to frameworks (NIST CSF 2.0, NIST AI RMF 1.0,
  ISO/IEC 27001 and 42001 by clause number, EU AI Act)
- run vendor risk and AI impact assessments using a written methodology
- produce risk registers, gap reports and executive memos

All work is done for a **fictional** organization described in `samples/company-profile.md`.

## Rules for every output

1. **Synthetic data only.** Use only the documents in `samples/` and `case-study/`. Never ask for,
   accept or process real employer, client, patient or personal data. If a file looks like real
   personal data, stop and say so.
2. **Cite every finding.** Each mapping, gap or risk rating names the control ID, framework
   function or legal article it rests on, and the source document and section it came from.
3. **Use the tools for control text.** Get 800-53 wording from `tools/control_lookup.py` (or the
   MCP server once built). Do not quote control text from memory.
4. **ISO standards are copyrighted.** Cite ISO/IEC 27001 and 42001 by clause or Annex A number and
   write original summaries. Never reproduce ISO text.
5. **Drafts for a human reviewer.** Every report states that it is a draft prepared with AI
   assistance for review by a qualified professional. The tool assists; a person decides.
6. **Say what is uncertain.** If evidence is missing or a mapping is a judgment call, label it
   as such rather than guessing.

## Project layout

| Folder | Contents |
| --- | --- |
| `data/` | NIST 800-53 Rev. 5 OSCAL catalog; framework crosswalks (phase 4) |
| `tools/` | Command-line tools, starting with `control_lookup.py` |
| `mcp/` | MCP servers that expose the tools to Claude (phases 3-4) |
| `skills/` | Assessment methodologies written as Claude skills (phase 5) |
| `.claude/commands/` | Slash commands for repeatable workflows (phase 6) |
| `personas/` | Reviewer personas: auditor, privacy counsel, CISO (phase 11) |
| `reports/` | Report templates (phase 9) |
| `samples/` | Synthetic company documents used as inputs |
| `case-study/` | Capstone: end-to-end assessment of an AI vendor (phase 10) |
| `docs/` | Data sources, design decisions, framework notes |
| `tests/` | Automated tests (`python -m pytest`) |

## Useful commands

```bash
python tools/control_lookup.py get AC-2            # one control, full text
python tools/control_lookup.py get "IA-2(1)"       # an enhancement
python tools/control_lookup.py search "multi-factor authentication" --limit 5
python tools/control_lookup.py family IR           # list a family
python tools/control_lookup.py families            # list all 20 families
python -m pytest                                   # run the tests
```

Add `--json` to any lookup command for machine-readable output.

## Style

- Plain English, short sentences. Write for a busy risk owner, not a specialist.
- Control IDs in the official form: `AC-2`, `AC-2(1)`.
- Risk ratings use the scale defined in the active methodology skill (phase 5).

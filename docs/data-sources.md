# Data sources

| Source | File | Licence / reuse | Notes |
| --- | --- | --- | --- |
| NIST SP 800-53 Rev. 5 control catalog (OSCAL JSON), release 5.2.0 | `data/NIST_SP-800-53_rev5_catalog.json` | US government work, public domain in the US | From NIST's [oscal-content](https://github.com/usnistgov/oscal-content) repository, `nist.gov/SP800-53/rev5/json/`. Includes 800-53A assessment objectives. |

## Planned (later phases)

| Source | Use | Reuse note |
| --- | --- | --- |
| NIST CSF 2.0 and its informative references | Crosswalk to 800-53 (phase 4) | Public domain |
| NIST AI RMF 1.0 and Playbook | AI risk functions and actions (phase 4) | Public domain |
| EU AI Act (Regulation (EU) 2024/1689) | Article-level obligations (phase 4) | EU legal text, reusable with attribution |
| ISO/IEC 27001:2022, ISO/IEC 42001:2023 | Clause references only | Copyrighted: cite numbers, write original summaries |

## Updating the 800-53 catalog

```bash
curl -L -o data/NIST_SP-800-53_rev5_catalog.json \
  https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json
python -m pytest   # confirm the tool still works with the new release
```

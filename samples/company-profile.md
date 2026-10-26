# Company profile: Larkspur Community Health (fictional)

> Every name, figure and system in this file is invented for a portfolio project. Any
> resemblance to a real organization is coincidental.

## Organization

- **Type:** regional nonprofit hospital network, United States
- **Size:** 3 hospitals, 11 outpatient clinics, about 4,200 staff
- **Regulatory context:** HIPAA (health data), state breach-notification laws; treats some
  EU-resident patients, so EU AI Act obligations are reviewed for AI tools touching them
- **Security framework:** NIST CSF 2.0 as the program framework, NIST SP 800-53 Rev. 5 as the
  control catalog
- **AI governance:** adopting the NIST AI RMF 1.0; considering ISO/IEC 42001 certification

## People (roles used in assessments)

| Role | Responsibility |
| --- | --- |
| Chief Information Security Officer (CISO) | Owns security risk acceptance |
| Privacy Officer | Owns HIPAA and data protection decisions |
| AI Governance Committee | Approves any AI system that touches patients |
| Vendor Risk Analyst | Runs third-party assessments (the user of this toolkit) |
| General Counsel | Reviews contract terms and regulatory exposure |

## Current initiative

Larkspur is evaluating **an AI patient-intake chatbot** from a third-party vendor. The chatbot
would collect symptoms and insurance details before appointments. This is the subject of the
capstone case study in `case-study/`.

## Risk appetite (summary)

- **Low** appetite for risks to patient safety and patient data confidentiality
- **Moderate** appetite for operational risk from new technology pilots
- Any AI system that influences care decisions needs AI Governance Committee approval

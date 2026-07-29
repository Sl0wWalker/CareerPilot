# ATS Compatibility Report

Date: 2026-07-29  
Evaluated commit: `c549950` plus the compatibility fixes in this change  
Mode: local fixture-backed Playwright dry-run; no real application submitted

## Executive result

CareerPilot is **not ready for real application submission**. The repository had
hostname detection for four ATS families and generic form inspection, but the API
did not invoke Playwright. It could report a non-dry run as `running` without
opening a browser. That false-positive state is now rejected.

The repaired browser runner passes a controlled compatibility contract for nine
ATS categories. This proves common form mechanics, not compatibility with every
live version of those products.

## Test scope

The automated lab validates:

- visible text and email inputs;
- accessible label discovery;
- required-field discovery;
- select option handling;
- checkbox handling;
- resume file upload;
- sensitive-field pause;
- CAPTCHA, MFA, and authentication interruption detection;
- selector-drift reporting;
- the invariant that final submit is never clicked.

The lab uses fictional HTML. It does not use credentials, personal data, CAPTCHA
bypass, legal attestations, or real submissions.

## Platform readiness

| Platform | Detection | Fixture contract | Live evidence | Readiness |
|---|---:|---:|---:|---|
| Greenhouse | Pass | Pass | None | Experimental dry-run |
| Lever | Pass | Pass | None | Experimental dry-run |
| Ashby | Pass | Pass | None | Experimental dry-run |
| Workday | Pass | Pass | None | Foundation only |
| SmartRecruiters | Added/pass | Pass | None | Foundation only |
| iCIMS | Added/pass | Pass | None | Foundation only |
| Taleo | Added/pass | Pass | None | Foundation only |
| SAP SuccessFactors | Added/pass | Pass | None | Foundation only |
| Generic HTML | Pass | Pass | None | Experimental dry-run |

Contract success rate: **9/9 categories (100%)**.  
Live-site success rate: **not measured**.  
Submission success rate: **not applicable; submission is intentionally absent**.

## Fixes applied

- Added explicit detection for SmartRecruiters, iCIMS, Taleo, and SuccessFactors.
- Tightened hostname matching to domain boundaries.
- Added stable selectors to inspected fields.
- Added accessible-name, `aria-labelledby`, label, placeholder, and name fallbacks.
- Added select, checkbox, and radio filling.
- Added local resume upload.
- Added selector-drift issue reporting.
- Added CAPTCHA, MFA, and authentication interruption detection.
- Added fixture-backed Playwright tests for all requested ATS categories.
- Prevented the API from reporting unimplemented live execution as `running`.

## Known gaps

1. The API is not wired to a durable browser worker.
2. There are no sanitized snapshots from real ATS pages.
3. There are no per-platform selectors for dynamic widgets, shadow DOM, iframes,
   repeated employment sections, or multi-page navigation.
4. Retry counters exist, but browser restart and checkpoint restoration are not
   implemented end to end.
5. Screenshot and trace capture are not wired into `AutomationStep`.
6. Login, MFA, and CAPTCHA are detected only by page text and require the user.
7. Cover-letter upload has not been validated.
8. Workday, iCIMS, Taleo, and SuccessFactors need dedicated multi-page adapters.
9. Resume import through document generation is covered by separate unit/API
   tests, not one browser-level end-to-end journey.

## Prioritized next work

1. Wire one supervised Greenhouse flow to a durable Playwright worker.
2. Add sanitized Greenhouse and Lever page snapshots and trace-based regression
   fixtures.
3. Persist screenshots, field mappings, validation messages, and checkpoints.
4. Add multi-page navigation and safe resume-from-checkpoint behavior.
5. Conduct a user-observed private alpha that stops at final review.
6. Add one ATS at a time only after its live dry-run suite is repeatable.

## Release recommendation

**NO-GO for live submission or claims of broad ATS support.**  
**Conditional GO for local, supervised compatibility development and dry-run
testing**, clearly labeled experimental.

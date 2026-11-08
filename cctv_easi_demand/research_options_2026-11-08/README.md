# CCTV EASI research options, 2026-11-08

This package contains two proposed designs, not new econometric estimates.

- `heterogeneity.md`: regional/household elasticity comparisons, estimands and common support.
- `inference.md`: direct difference tests, paired province inference and multiple comparisons.
- `sensitivity.md`: directed functional-form sensitivity, based on Andrews, Essig Aberg and Shapiro (2026).
- `workflow.md`: analytic checks, search budget and independent verification.
- `overview.md`, `combined.md`, `decisions.md`, `sources.md`: overview, paper framing, author decisions and sources.
- `design_manifest.json`: machine-readable design status. Proposed targets are not findings.
- `checks/`: website QA code, report and screenshots; not econometric outputs.
- `portal_integration/`: only this project's registry fragment and review backend additions.

Canonical local root:

`/root/data/Paper/央视数据/Paper1-EASI/research_options_2026-11-08/`

Live review:

`http://127.0.0.1:8891/static/review/papers/cctv-easi-design/overview.html`

On a remote connection, retain the host used for the existing 8891 website.
The project also appears in the 8891 review directory. Notes in this static
entry are browser-local and exportable, not synchronized between devices.
The existing server was not restarted. Existing projects and notes were not
replaced. Raw transactions, household identifiers and review databases are
not included in this package.

The web backend is maintained separately at:

`/root/data/Paper/央视数据/paper10-warning-consumption/web/`

After an approved content change, the established publisher is:

```bash
cd /root/data/Paper/央视数据/paper10-warning-consumption/web
python3 export_review_8891.py
```

Verification (Flask backend tests use a temporary database; browser tests use
a fresh isolated context):

```bash
cd /root/data/Paper/央视数据/Paper1-EASI/research_options_2026-11-08
python3 checks/verify_review.py
```

QA dependencies: the existing Flask review environment, Playwright Python,
and Google Chrome at `/usr/bin/google-chrome`. The verification checks route
and download allowlists, formulas, note save/reload/export and project
isolation, and all eight sections at 1440, 390 and 320 pixel widths.

No new R/Stata estimation or directed sensitivity search was executed.
Existing Stata estimators are not modified by this review package.

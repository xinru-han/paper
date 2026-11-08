# Portal integration scope

`project.json` is the single new registry entry from `web/review_projects.json`.
It is not a replacement for that registry: all existing entries remain.

`review.py.patch` records only the CCTV content-root and download-allowlist
additions to the existing review backend. It excludes unrelated concurrent
changes to other projects. The backend already provides generic section
rendering, review forms and static export; no new application is needed.

For an installation with the same generic `content_root` backend:

```bash
cd /root/data/Paper/央视数据/paper10-warning-consumption/web
git apply --check /root/data/Paper/央视数据/Paper1-EASI/research_options_2026-11-08/portal_integration/review.py.patch
```

The patch has already been applied on the current machine; the command above
is intended for a clean installation, not for repeated application. Registry
integration is by unique project ID `cctv-easi-design`, preserving the other
entries. The existing `export_review_8891.py` publishes the resulting pages.

No service restart, raw-data endpoint or change to browser storage keys was
required. Static HTML snapshots are regenerated artifacts, not canonical
drafts. The proposal Markdown remains canonical in this package.

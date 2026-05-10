SLT Usage Monitor (Playwright + GitHub Actions)

This project provides an initial safe-mode Playwright script that loads the SLT MySLT portal and saves a screenshot for debugging.

Files:
- .github/workflows/run.yml — GitHub Actions workflow (runs every 6 hours)
- fetch.py — Playwright script (safe-mode)
- requirements.txt — Python dependencies
- storage.json — optional history file

Optional environment variables (used in Phase 2 login skeleton):
- `SLT_USER` — SLT username (set as GitHub Secret `SLT_USER`)
- `SLT_PASS` — SLT password (set as GitHub Secret `SLT_PASS`)
- `STORAGE_STATE_PATH` — path to save Playwright storage state (default `storage_state.json`)

Quick local run (recommended in a virtualenv):

```bash
pip install -r requirements.txt
playwright install chromium
python fetch.py
```

Notes:
- This is Phase 1 (safe mode). It only opens the SLT portal and captures `slt_debug.png`.
- Do not hardcode credentials; Phase 2 will add secure login handling via GitHub Secrets.
 - If you set `SLT_USER` and `SLT_PASS` as repository Secrets, the workflow will attempt a login skeleton and save a `storage_state.json` file for reuse in later phases.

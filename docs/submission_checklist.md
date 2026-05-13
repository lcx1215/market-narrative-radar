# Submission Checklist

Use this as the short handoff for the NYU Text as Data project submission.

## What the Instructor Should See

- Open `http://127.0.0.1:8765`.
- The first screen shows `Market Narrative Radar` and one main action: `Pay $1 & generate`.
- The visible topic focus includes `U.S. policy & trade`.
- The app produces a public-text narrative brief, not a trading recommendation.
- `Evidence and sources` expands to show the passages behind the answer.
- No browser API key is requested or displayed.

## What to Submit

- GitHub repo or zipped project folder, excluding `.env`, `.mnr-runtime/`, `__pycache__/`, screenshots, and temporary browser artifacts.
- `README.md` for startup and project overview.
- `report/project_report.md` as the written project report.
- `docs/course_methods_map.md` to show how course methods map to the app.
- `docs/replication_package.md` for reproducibility.
- `docs/teacher_review_checklist.md` for the grading/demo path.

## Final Local Checks

Run these from the project folder before submitting:

```bash
python3 scripts/validate_project.py
python3 scripts/mnr.py test
python3 scripts/mnr.py test --provider
git status --short
```

Expected result: validation and tests pass, provider reports `minimax-compatible` when `.env` is present, and `git status --short` does not include `.env`, `.mnr-runtime/`, Python caches, or screenshots.

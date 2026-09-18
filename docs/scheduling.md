# Scheduling

The offline loop is a set of idempotent scripts. It is intentionally scheduler-agnostic:
nothing in the code depends on how the scripts are triggered. This document records the
intended cadence and the contract each script honors.

## Cadences

| Job                     | Cadence           | Script                              | Publishes                     |
|-------------------------|-------------------|-------------------------------------|-------------------------------|
| Feature/model publish   | on model release  | scripts/publish_models.py           | state/model_versions/         |
| Graph snapshot refresh  | hourly            | scripts/publish_graph.py            | state/graph_snapshots/        |
| Cost model inputs       | daily             | scripts/build_cost_inputs.py        | state/cost_model_inputs/      |
| Drift snapshot          | daily             | scripts/compute_drift.py            | state/drift_signals/          |
| Quality report          | daily             | scripts/compute_quality.py          | state/quality_metrics/        |
| Threshold optimization  | weekly            | scripts/optimize_thresholds.py      | state/threshold_tables/       |
| Full offline sequence   | daily (nightly)   | scripts/pipeline_offline.ps1        | all of the above              |

## Contract

- Every script writes a single artifact with a version string into state/<kind>/<version>.json.
- Every script is safe to re-run for the same version: publishing overwrites the same file.
- The hot path reads the newest file by mtime via state/loader.load_latest(kind).
- The hot path never writes to state/. Publishing is offline only.
- Rollback is a filesystem operation: delete or rename the newest file; the loader picks
  up the previous newest on next read.

## Wiring this to a real scheduler

This repository does not install a scheduler. To wire it in production, invoke
scripts/pipeline_offline.ps1 from whichever scheduler the host already uses:

- Windows Task Scheduler: create a daily task that runs
  powershell -ExecutionPolicy Bypass -File <repo>\scripts\pipeline_offline.ps1
- cron (WSL / Linux): run pwsh -File <repo>/scripts/pipeline_offline.ps1 daily
- Kubernetes CronJob: wrap the Dockerfile with a command override that calls the same script

Do not create parallel scheduling inside the application. The app must never mutate state/
at request time.

## Auto-rebuild during outcome submission

The outcome endpoint optionally triggers an in-process rebuild, gated by:

- env FINCRIME_AUTO_REBUILD=1 (default 1; tests set 0)
- config.auto_rebuild.enabled
- a minimum interval (config.auto_rebuild.min_interval_seconds, default 30)

This exists to keep the loop warm during development and short-tail deployments. In
production, prefer the scheduled pipeline and set FINCRIME_AUTO_REBUILD=0 to keep the
request path deterministic.
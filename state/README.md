# state/

Versioned artifact store. Offline components publish here; the hot path reads here.

## Layout

state/
  threshold_tables/<version>.json
  graph_snapshots/<version>.json
  model_versions/<version>.json

## Contract

- Each file is a JSON object with at least a "version" field.
- Filenames match the version string: <version>.json
- The hot path reads the newest file (by mtime) via load_latest(kind).
- The hot path NEVER writes here. Publishing is a separate offline step.
- Rollback = deleting or ignoring newer files; the loader picks up the previous newest.

## Kinds

- threshold_tables: {"version": str, "entries": {segment_key: [t_challenge, t_decline]}}
- graph_snapshots: {"version": str, "ring_scores": {...}, "confirmed_members": {...},
                     "connected_accounts": {...}, "confirmed_fraud_neighbors": {...}}
- model_versions:   {"version": str, "models": {component: version_str}}

## Publishing

scripts/publish_all.ps1

## Reading

from fincrime_os.state.loader import load_latest, load_version, publish
import subprocess
import sys
from pathlib import Path

import fincrime_os.state.loader as loader

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_publish_thresholds_script(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    # The script imports loader at runtime; patch via env-style only for this test.
    # Skip if STATE_ROOT override is not possible from the subprocess path.
    # Instead, assert the script exits 0 and prints the expected prefix.
    r = _run("publish_thresholds.py", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "published threshold_tables version=v-script-test" in r.stdout


def test_publish_models_script():
    r = _run("publish_models.py", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "published model_versions version=v-script-test" in r.stdout


def test_publish_graph_script():
    r = _run("publish_graph.py", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "published graph_snapshots version=v-script-test" in r.stdout


def test_build_cost_inputs_script():
    r = _run("build_cost_inputs.py", "--window-days", "1", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "cost_model_inputs version=v-script-test" in r.stdout


def test_compute_drift_script():
    r = _run("compute_drift.py", "--window-days", "1", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "drift_signals version=v-script-test" in r.stdout


def test_compute_quality_script():
    r = _run("compute_quality.py", "--window-days", "1", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "quality_metrics version=v-script-test" in r.stdout


def test_optimize_thresholds_script():
    r = _run("optimize_thresholds.py", "--window-days", "1", "--version", "v-script-test")
    assert r.returncode == 0, r.stderr
    assert "threshold_tables version=v-script-test" in r.stdout
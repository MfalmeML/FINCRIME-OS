import json
import subprocess
import sys
from pathlib import Path

import joblib

import fincrime_os.state.loader as loader

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def test_publish_models_marks_fallbacks_when_untrained():
    # Do not patch STATE_ROOT here: the subprocess runs against the real state/.
    # The repo may or may not have trained models. The test asserts structure only.
    r = _run("publish_models.py", "--version", "v-pub-models-test")
    assert r.returncode == 0, r.stderr
    assert "published model_versions version=v-pub-models-test" in r.stdout
    for component in (
        "transaction_model",
        "behavioral_model",
        "temporal_model",
        "fusion_model",
        "graph_model",
    ):
        assert f"  {component}=" in r.stdout

    path = loader.STATE_ROOT / "model_versions" / "v-pub-models-test.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "models" in payload
    assert "trained" in payload
    assert set(payload["models"].keys()) == {
        "transaction_model",
        "behavioral_model",
        "temporal_model",
        "fusion_model",
        "graph_model",
    }
    assert all(isinstance(v, bool) for v in payload["trained"].values())
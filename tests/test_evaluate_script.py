import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_evaluate_model_script(tmp_path):
    preds = tmp_path / "preds.jsonl"
    labels = tmp_path / "labels.jsonl"
    segs = tmp_path / "segs.jsonl"
    _write(preds, [
        {"transaction_id": "t1", "score": 0.9},
        {"transaction_id": "t2", "score": 0.1},
        {"transaction_id": "t3", "score": 0.8},
        {"transaction_id": "t4", "score": 0.2},
    ])
    _write(labels, [
        {"transaction_id": "t1", "is_fraud": 1},
        {"transaction_id": "t2", "is_fraud": 0},
        {"transaction_id": "t3", "is_fraud": 1},
        {"transaction_id": "t4", "is_fraud": 0},
    ])
    _write(segs, [
        {"transaction_id": "t1", "segment": {"customer_tier": "vip"}},
        {"transaction_id": "t2", "segment": {"customer_tier": "vip"}},
        {"transaction_id": "t3", "segment": {"customer_tier": "default"}},
        {"transaction_id": "t4", "segment": {"customer_tier": "default"}},
    ])
    r = subprocess.run(
        [
            sys.executable, str(REPO_ROOT / "scripts" / "evaluate_model.py"),
            "--predictions", str(preds),
            "--labels", str(labels),
            "--segments", str(segs),
            "--threshold", "0.5",
            "--version", "v-eval-test",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "eval_reports version=v-eval-test" in r.stdout
    assert "overall precision=1.0000" in r.stdout
    assert "segment=vip" in r.stdout
    assert "segment=default" in r.stdout
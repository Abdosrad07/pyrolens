"""Tests de reproductibilité : data/raw jamais modifié, artefacts réellement écrits."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from pyrolens.audit import audit_file, temporal_gaps, write_anomaly_csvs
from pyrolens.audit_report import build_audit_summary, write_audit_markdown
from pyrolens.baselines import run_baselines
from pyrolens.config import load_config
from pyrolens.fixture import write_fixture
from pyrolens.observability import run_observability

ROOT = Path(__file__).resolve().parents[1]


def _tree_hashes(root: Path) -> dict[str, str]:
    out = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_data_raw_never_modified(tmp_path):
    raw = ROOT / "data" / "raw"
    before = _tree_hashes(raw)
    assert before, "data/raw attendu (géométrie / inventaire CMR acquis)"

    cfg = load_config()
    files = write_fixture(tmp_path / "fx", date(2019, 1, 1), date(2019, 1, 31))
    audits = [audit_file(p, bbox=cfg.get("region.bbox")) for p in files if p.suffix == ".csv"]
    gaps = temporal_gaps(audits)
    summary = build_audit_summary(audits, "synthetic_fixture", gaps)
    write_anomaly_csvs(audits, tmp_path / "anomalies")
    write_audit_markdown(summary, tmp_path / "audit.md")

    rows = [r for a in audits for r in a.rows]
    run_baselines(rows, cfg, tmp_path / "baselines", tmp_path / "artifacts", "synthetic_fixture")
    run_observability(
        {"terra": [r for r in rows if r["satellite"] == "Terra"]},
        cfg, tmp_path / "baselines", tmp_path / "artifacts", "synthetic_fixture",
    )

    after = _tree_hashes(raw)
    assert before == after, "data/raw a été modifié par le pipeline"


def test_artifacts_written_and_parseable(tmp_path):
    cfg = load_config()
    files = write_fixture(tmp_path / "fx2", date(2019, 1, 1), date(2019, 1, 31))
    audits = [audit_file(p, bbox=cfg.get("region.bbox")) for p in files if p.suffix == ".csv"]
    rows = [r for a in audits for r in a.rows]

    baselines_dir = tmp_path / "b"
    artifacts_dir = tmp_path / "a"
    payload = run_baselines(rows, cfg, baselines_dir, artifacts_dir, "synthetic_fixture")
    for name in ("summary.csv", "jaccard_monthly.csv", "daily_divergence.csv",
                 "monthly_divergence.csv", "spatial_distribution.csv", "regional_divergence.csv"):
        assert (baselines_dir / name).exists(), name
        assert (baselines_dir / name).stat().st_size > 0
    loaded = json.loads((artifacts_dir / "baselines.json").read_text(encoding="utf-8"))
    assert loaded["data_origin"] == "synthetic_fixture"
    assert len(loaded["summary"]) == len(payload["summary"]) == 24  # 2 paires x 3 grilles x 4 fenêtres


def test_fixture_is_deterministic(tmp_path):
    a = write_fixture(tmp_path / "d1", date(2019, 1, 1), date(2019, 1, 10))
    b = write_fixture(tmp_path / "d2", date(2019, 1, 1), date(2019, 1, 10))
    for pa, pb in zip(a, b):
        if pa.suffix != ".csv":
            continue
        assert pa.read_bytes() == pb.read_bytes(), f"non déterministe : {pa.name}"

"""CLI Typer du pipeline PyroLens phase 2.

Chaque commande est indépendante, journalisée, et enregistre son statut
(blocage compris) dans web/public/artifacts/execution.json.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from . import __version__
from .config import PROJECT_ROOT, Config, load_config
from .logging_utils import get_logger
from .provenance import now_iso


def _load_env_files() -> None:
    """Charge `.env` puis `.env.local` (prioritaire) — convention env.example.

    python-dotenv est optionnel : absent, les variables d'environnement
    du processus restent la seule source.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_file = PROJECT_ROOT / ".env"
    local_file = PROJECT_ROOT / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
    if local_file.exists():
        load_dotenv(local_file, override=True)


_load_env_files()

app = typer.Typer(help="PyroLens phase 2 — pipeline MODIS / VIIRS (pilote Cameroun).", no_args_is_help=True)


def _paths(cfg: Config):
    return {key: cfg.path_of(key) for key in
            ("raw", "fixture", "manifests", "reports", "anomalies", "logs", "baselines", "figures", "artifacts")}


def _artifacts(cfg: Config) -> Path:
    p = cfg.path_of("artifacts")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _execution(cfg: Config) -> dict:
    path = _artifacts(cfg) / "execution.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"steps": [], "blockers": [], "commands": []}


def _save_execution(cfg: Config, payload: dict) -> None:
    (_artifacts(cfg) / "execution.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def record_step(cfg: Config, step: str, status: str, detail: str, *, blocker: bool = False,
                http_status=None, action: str | None = None, what: str | None = None,
                manifest: str | None = None) -> None:
    payload = _execution(cfg)
    payload.setdefault("steps", []).append({"step": step, "status": status, "detail": detail, "at": now_iso()})
    if blocker:
        payload.setdefault("blockers", []).append(
            {"what": what or step, "detail": detail, "http_status": http_status,
             "action": action, "at": now_iso()}
        )
    if manifest:
        payload["manifest"] = manifest
    payload.setdefault("period_start", cfg.get("period.start"))
    payload.setdefault("period_end", cfg.get("period.end"))
    payload["project_version"] = __version__
    _save_execution(cfg, payload)


def record_command(cfg: Config, argv: list[str], status: str) -> None:
    payload = _execution(cfg)
    payload.setdefault("commands", []).append({"cmd": argv, "status": status, "at": now_iso()})
    _save_execution(cfg, payload)


def _source_dir(cfg: Config, source: Optional[str]) -> tuple[Path, str]:
    """Retourne (répertoire de source, origine des données)."""
    if source:
        p = Path(source)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        if "archive" in p.parts:
            origin = "firms_archive_sp"
        else:
            origin = "nasa_firms" if "raw" in p.parts else "synthetic_fixture"
        return p, origin
    raw_firms = cfg.path_of("raw") / "firms"
    if raw_firms.exists() and list(raw_firms.glob("*.csv")):
        return raw_firms, "nasa_firms"
    fixture = cfg.path_of("fixture")
    if fixture.exists() and list(fixture.glob("*.csv")):
        return fixture, "synthetic_fixture"
    raise typer.BadParameter(
        "Aucun CSV trouvé : exécuter `pyrolens download` (données NASA, credentials requis) "
        "ou `pyrolens fixture` (échantillon synthétique de démonstration)."
    )


def _load_audits(cfg: Config, source: Optional[str] = None, keep_rows: bool = True):
    from .audit import audit_file

    src_dir, origin = _source_dir(cfg, source)
    bbox = cfg.get("region.bbox")
    n_regions = int(cfg.get("analysis.n_regions", 3))
    geometry = None
    geo_file = cfg.path_of("raw") / "geo" / "ne_110m_admin_0_countries.geojson"
    if geo_file.exists():
        try:
            from .emprise import load_region_polygon

            geometry = load_region_polygon(geo_file, cfg.get("region.iso3", "CMR"))
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"[audit] polygone d'emprise indisponible ({exc}) : filtre bbox seul.")
    audits = []
    for path in sorted(src_dir.glob("*.csv")):
        fa = audit_file(path, bbox=bbox, geometry=geometry, n_regions=n_regions)
        if not keep_rows:
            # Le résumé d'audit n'a pas besoin des lignes ligne à ligne : les
            # libérer immédiatement garde la mémoire bornée sur des CSV réels.
            fa.rows = []
        audits.append(fa)
    if not audits:
        raise typer.BadParameter(f"Aucun CSV dans {src_dir}")
    return audits, origin, src_dir


# ------------------------------------------------------------------ commandes
@app.command()
def doctor() -> None:
    """État de l'environnement (Python, bibliothèques, clés présentes — noms uniquement)."""
    import os

    import polars as pl

    typer.echo(f"PyroLens {__version__}")
    typer.echo(f"Python  {sys.version.split()[0]} ({platform.platform()})")
    for mod in ("polars", "pandas", "shapely", "matplotlib", "typer", "yaml", "pytest", "docx", "httpx"):
        try:
            m = __import__(mod)
            typer.echo(f"  {mod:<12} {getattr(m, '__version__', 'ok')}")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"  {mod:<12} ABSENT ({exc})")
    typer.echo(f"  polars dump : {pl.__version__}")
    for key in ("FIRMS_MAP_KEY", "EARTHDATA_TOKEN", "EARTHDATA_USER", "EARTHDATA_PASSWORD"):
        typer.echo(f"  env {key:<22} {'présente' if os.environ.get(key) else 'absente'}")
    typer.echo(f"  projet      {PROJECT_ROOT}")
    record_step(load_config(), "doctor", "ok", "environnement inspecté")


@app.command()
def geo() -> None:
    """Télécharge la géométrie d'emprise documentée (Natural Earth)."""
    from .download import download_emprise, write_download_manifest

    cfg = load_config()
    entries: list = []
    target = download_emprise(cfg.path_of("raw"), entries)
    write_download_manifest(cfg.path_of("manifests"), entries, "downloads_geo.json")
    if target:
        typer.echo(f"Emprise : {target}")
        record_step(cfg, "geo", "ok", f"polygone administratif acquis : {target.name}")
    else:
        typer.echo("ÉCHEC : polygone d'emprise non acquis", err=True)
        record_step(cfg, "geo", "bloqué", "impossible de télécharger la géométrie d'emprise",
                    blocker=True, what="Géométrie d'emprise",
                    action="réessayer ou fournir un GeoJSON")
        raise typer.Exit(code=1)


@app.command()
def inventory() -> None:
    """Inventaire réel des produits/périodes via l'API CMR (public, sans clé)."""
    from .cmr import run_inventory

    cfg = load_config()
    payload = run_inventory(cfg, cfg.path_of("raw"))
    art = _artifacts(cfg)
    (art / "inventory.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(
        y.get("granules_in_bbox", 0)
        for s in payload["sensors"].values()
        for y in s.get("years", {}).values()
        if isinstance(y, dict)
    )
    typer.echo(f"Inventaire CMR écrit : data/raw/cmr/inventory.json (granules bbox cumulés = {total})")
    for key, spec in payload["sensors"].items():
        years = {y: v.get("granules_in_bbox") for y, v in spec.get("years", {}).items() if isinstance(v, dict)}
        typer.echo(f"  {key}: version={spec.get('version_used')} granules/an={years}")
    record_step(cfg, "inventory", "ok",
                f"CMR : versions et granules par année vérifiés ({total} granules bbox cumulés)")


@app.command()
def download(
    start: Optional[str] = typer.Option(None, help="date de début (AAAA-MM-JJ), défaut : config"),
    end: Optional[str] = typer.Option(None, help="date de fin (AAAA-MM-JJ), défaut : config"),
    sensors: Optional[str] = typer.Option(None, help="capteurs FIRMS séparés par virgules (défaut : tous)"),
    workers: int = typer.Option(8, min=1, max=12, help="requêtes FIRMS en parallèle"),
    deadline: int = typer.Option(150, min=10, max=175, help="budget en secondes avant arrêt propre (reprise idempotente)"),
) -> None:
    """Prépare/télécharge : emprise + FIRMS API + probe granule Earthdata (sans contournement)."""
    from .cmr import sample_granules
    from .download import download_emprise, download_firms, probe_granule_access, write_download_manifest

    cfg = load_config()
    entries: list = []
    paths = _paths(cfg)
    sensor_keys = [s.strip() for s in sensors.split(",") if s.strip()] if sensors else None

    geo_target = download_emprise(paths["raw"], entries)
    if geo_target:
        record_step(cfg, "download:geo", "ok", f"emprise acquise ({geo_target.name})")

    # FIRMS API (bloqué sans FIRMS_MAP_KEY — jamais de clé en dur)
    try:
        firms_res = download_firms(
            cfg, paths["raw"], entries,
            start=date.fromisoformat(start) if start else None,
            end=date.fromisoformat(end) if end else None,
            sensor_keys=sensor_keys,
            workers=workers,
            deadline_s=float(deadline),
        )
        if firms_res.get("blocked"):
            record_step(cfg, "download:firms", "bloqué",
                        "FIRMS_MAP_KEY absent : API FIRMS inaccessible sans clé",
                        blocker=True, what="FIRMS API (CSV par emprise)",
                        http_status=None,
                        action="fournir FIRMS_MAP_KEY via Settings → Environment (clé gratuite FIRMS)")
            typer.echo("FIRMS API : bloqué (FIRMS_MAP_KEY absent)")
        else:
            new = sum(1 for e in entries if e.get("status") == "downloaded")
            kept = sum(1 for e in entries if e.get("status") == "already_present")
            deferred = sum(1 for e in entries if e.get("status") == "deferred")
            errors = sum(1 for e in entries if e.get("status") in ("http_error", "error"))
            typer.echo(f"FIRMS API : {new} nouveaux / {kept} déjà présents / "
                       f"{deferred} reportés / {errors} erreurs")
            if errors or deferred:
                record_step(cfg, "download:firms", "attention",
                            f"{new} nouveaux fichiers ; {errors} erreurs, {deferred} reportés "
                            f"(rejouer la commande reprend l'acquisition)")
            else:
                record_step(cfg, "download:firms", "ok",
                            f"{new} nouveaux fichiers FIRMS (total session {kept} déjà présents)")
    except Exception as exc:  # noqa: BLE001
        record_step(cfg, "download:firms", "erreur", str(exc), blocker=True,
                    what="FIRMS API", action="vérifier réseau/clé")

    # Probe d'un granule standard (MOD14 2019 sur l'emprise) — sans contournement
    try:
        samples = sample_granules("MOD14", "061", cfg.get("region.bbox"),
                                  "2019-01-01T00:00:00Z,2019-01-02T00:00:00Z", n=1)
        if samples and samples[0].get("download_links"):
            res = probe_granule_access(samples[0]["download_links"][0], entries,
                                       dataset="MOD14.061 granule (traitement scientifique standard)")
            if not res.get("acquired"):
                record_step(
                    cfg, "download:earthdata", "bloqué",
                    "Redirection vers Earthdata Login : granule standard non accessible sans authentification",
                    blocker=True, what="Archives standard (MOD14/MYD14/VNP14IMG)",
                    http_status=res.get("http_status"),
                    action="fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc)",
                )
            else:
                record_step(cfg, "download:earthdata", "ok", "granule standard acquis")
        else:
            record_step(cfg, "download:earthdata", "attention", "aucun granule renvoyé par CMR")
    except Exception as exc:  # noqa: BLE001
        record_step(cfg, "download:earthdata", "erreur", str(exc), blocker=True,
                    what="Archives standard", action="vérifier l'accès réseau CMR")

    # Accumulation : les exécutions partielles (--start/--end) ne doivent pas
    # écraser la provenance des téléchargements précédents.
    existing: list = []
    manifest_path = paths["manifests"] / "downloads.json"
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", [])
        except Exception:  # noqa: BLE001
            existing = []
    manifest = write_download_manifest(paths["manifests"], existing + entries, "downloads.json")
    # copie dans les artefacts web
    try:
        (_artifacts(cfg) / "downloads.json").write_text(manifest.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    acquired = sum(1 for e in entries if e.get("acquired"))
    typer.echo(f"Manifest : {manifest} ({acquired} acquis / {len(entries)} entrées)")


@app.command()
def fixture(
    start: str = typer.Option("2019-01-01", help="date de début (AAAA-MM-JJ)"),
    end: str = typer.Option("2019-12-31", help="date de fin (AAAA-MM-JJ)"),
    seed: int = typer.Option(20260101, help="graine déterministe"),
) -> None:
    """Génère l'échantillon SYNTHÉTIQUE de démonstration (jamais des données réelles)."""
    from .fixture import write_fixture

    cfg = load_config()
    written = write_fixture(cfg.path_of("fixture"), date.fromisoformat(start), date.fromisoformat(end), seed)
    typer.echo(f"{len(written)} fichiers synthétiques écrits dans {cfg.path_of('fixture')}")
    record_step(cfg, "fixture", "ok",
                f"échantillon synthétique {start} → {end} ({len(written)} fichiers, graine {seed})")


@app.command()
def audit(source: Optional[str] = typer.Option(None, help="répertoire CSV (défaut : raw/firms puis fixture)")) -> None:
    """Audit qualité → rapport Markdown, CSV d'anomalies, journal, artefact JSON."""
    from .audit import temporal_gaps, write_anomaly_csvs
    from .audit_report import build_audit_summary, write_audit_artifact, write_audit_markdown

    cfg = load_config()
    paths = _paths(cfg)
    logger = get_logger("pyrolens.audit", paths["logs"], "audit.log")
    audits, origin, src_dir = _load_audits(cfg, source, keep_rows=False)
    logger.info("audit de %d fichiers depuis %s (origine=%s)", len(audits), src_dir, origin)

    gaps = temporal_gaps(audits)
    summary = build_audit_summary(audits, origin, gaps)
    anomaly_files = write_anomaly_csvs(audits, paths["anomalies"])
    md = write_audit_markdown(summary, paths["reports"] / "data_quality_audit.md")
    art = write_audit_artifact(summary, _artifacts(cfg))

    total_anom = sum(summary["anomalies_by_category"].values())
    typer.echo(f"Audit : {summary['n_files']} fichiers, {total_anom} anomalies, "
               f"{len(anomaly_files)} CSV d'anomalies → {md}")
    typer.echo(f"  classification : {summary['rows_by_classification']}")
    record_step(cfg, "audit", "ok",
                f"{summary['n_files']} fichiers audités, {total_anom} anomalies, origine={origin}")


@app.command()
def baselines(source: Optional[str] = typer.Option(None, help="répertoire CSV")) -> None:
    """Baselines A (Terra-Aqua), B (Aqua-VIIRS), C (sensibilité)."""
    from .baselines import run_baselines

    cfg = load_config()
    paths = _paths(cfg)
    audits, origin, _ = _load_audits(cfg, source)
    rows = [row for a in audits for row in a.rows]
    payload = run_baselines(rows, cfg, paths["baselines"], paths["artifacts"], origin)
    typer.echo(f"Baselines : {len(payload['summary'])} configurations, "
               f"{len(payload['monthly'])} lignes mensuelles → baselines/")
    record_step(cfg, "baselines", "ok",
                f"{len(payload['summary'])} configurations comparées, origine={origin}")


@app.command()
def observability(source: Optional[str] = typer.Option(None, help="répertoire CSV")) -> None:
    """Classification des états d'observabilité (4 états, aucun « pas de feu »)."""
    from .baselines import select_rows
    from .observability import run_observability

    cfg = load_config()
    paths = _paths(cfg)
    audits, origin, _ = _load_audits(cfg, source)
    rows = [row for a in audits for row in a.rows]

    sensor_keys = list((cfg.get("sensors") or {}).keys())
    rows_by_sensor = {k: select_rows(rows, cfg, k) for k in sensor_keys}
    payload = run_observability(rows_by_sensor, cfg, paths["baselines"], paths["artifacts"], origin)
    typer.echo(f"Observabilité : { {k: dict(v) for k, v in payload['states'].items()} }")
    record_step(cfg, "observability", "ok",
                "états classés (détection / observabilité inconnue / indéterminé) "
                "— aucun état « pas de feu »")


@app.command()
def figures() -> None:
    """Génère les figures PNG (reports + artefacts web)."""
    from .figures import generate_all

    cfg = load_config()
    paths = _paths(cfg)
    art = _artifacts(cfg)

    def _load(name: str) -> dict:
        p = art / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    written = generate_all(_load("audit.json"), _load("baselines.json"), _load("observability.json"),
                           paths["figures"], art)
    typer.echo(f"{len(written)} figures → figures/ (+ artefacts web)")
    record_step(cfg, "figures", "ok", f"{len(written)} figures générées")


@app.command()
def report() -> None:
    """Rapport scientifique Markdown + DOCX."""
    from .report import load_artifacts, write_report

    cfg = load_config()
    paths = _paths(cfg)
    artifacts = load_artifacts(_artifacts(cfg))
    out = write_report(
        artifacts,
        paths["reports"],
        refs_present=(PROJECT_ROOT / "docs" / "references.md").exists(),
        inv_present=(PROJECT_ROOT / "docs" / "data_inventory.md").exists(),
    )
    typer.echo(f"Rapport : {out['markdown']}" + (f" + {out['docx']}" if out.get("docx") else ""))
    record_step(cfg, "report", "ok", f"rapport généré (DOCX: {'oui' if out.get('docx') else 'non'})")


@app.command()
def normalize() -> None:
    """Fenêtres canoniques 5 j : fusionne les tronçons chevauchants (dédoublonnage strict)."""
    from .normalize import normalize_firms_dir

    cfg = load_config()
    paths = _paths(cfg)
    firms_dir = paths["raw"] / "firms"
    anchor = date.fromisoformat(cfg.get("period.start"))
    period_end = date.fromisoformat(cfg.get("period.end"))
    stats = normalize_firms_dir(firms_dir, anchor, period_end)

    from .provenance import now_iso

    stats["generated_at"] = now_iso()
    (paths["manifests"] / "normalize.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(
        f"Normalisation : {stats['files_in']} fichiers → {stats['files_out']} fenêtres canoniques, "
        f"{stats['rows_in']} lignes lues, {stats['rows_out']} écrites, "
        f"{stats['duplicate_rows_removed']} doublons stricts supprimés, "
        f"{stats['files_removed']} fichiers d'origine supprimés.")
    record_step(cfg, "normalize", "ok",
                f"{stats['files_in']} → {stats['files_out']} fenêtres canoniques ; "
                f"{stats['duplicate_rows_removed']} doublons supprimés "
                f"(comptabilité vérifiée : {stats['rows_in']} = {stats['rows_out']} + doublons)")


@app.command()
def run(
    source: Optional[str] = typer.Option(None, help="répertoire CSV existant"),
    with_fixture: bool = typer.Option(True, help="générer l'échantillon synthétique si aucune donnée réelle"),
) -> None:
    """Exécute la séquence complète : geo → inventaire → acquisition → audit → baselines → figures → rapport."""
    cfg = load_config()
    steps_run: list[str] = []

    def _step(name: str, fn) -> None:
        typer.echo(f"— {name} …")
        fn()
        steps_run.append(name)

    _step("geo", geo)
    _step("inventaire CMR", inventory)
    _step("acquisition", download)

    try:
        _source_dir(cfg, source)
    except typer.BadParameter:
        if with_fixture:
            _step("échantillon synthétique", fixture)
        else:
            typer.echo("Aucune donnée et --no-fixture : arrêt.", err=True)
            raise typer.Exit(code=1)

    _step("audit", lambda: audit(source))
    _step("baselines", lambda: baselines(source))
    _step("observabilité", lambda: observability(source))
    _step("figures", figures)
    _step("rapport", report)

    typer.echo(f"Pipeline terminé : {', '.join(steps_run)}")
    record_step(cfg, "run", "ok", "séquence complète exécutée : " + ", ".join(steps_run))


@app.command()
def predict(
    source: Optional[str] = typer.Option(None, help="répertoire CSV (défaut : raw/firms puis fixture)"),
    grid: float = typer.Option(0.25, help="maille spatiale en degrés"),
    window: int = typer.Option(8, help="horizon de prédiction en jours"),
    stride: int = typer.Option(7, help="pas d'échantillonnage temporel en jours"),
    reference_date: Optional[str] = typer.Option(None, help="date de référence AAAA-MM-JJ (défaut : max des données)"),
    out: Optional[str] = typer.Option(None, help="chemin de sortie (défaut : web/public/artifacts/fire_risk.json)"),
) -> None:
    """Prédit le risque d'activité de feu DÉTECTÉE (baseline fréquence + RandomForest).

    Backtest historique uniquement : les données s'arrêtent en 2020 — le résultat
    n'est jamais une prévision actuelle. Voir docs/FIRE_RISK_PREDICTION.md.
    """
    from .prediction import run_prediction

    cfg = load_config()
    src_dir, origin = _source_dir(cfg, source)
    # rglob : --source accepte aussi un arbre (ex. data/raw/archive/{capteur}/)
    csv_paths = sorted(src_dir.rglob("*.csv"))
    if not csv_paths:
        raise typer.BadParameter(f"Aucun CSV dans {src_dir}")
    ref = date.fromisoformat(reference_date) if reference_date else None
    typer.echo(f"Source : {src_dir} (origine={origin}) — {len(csv_paths)} CSV")

    def _progress(step: str, pct: float, detail: str | None = None) -> None:
        typer.echo(f"  [{pct:5.1f}%] {step:<10} {detail or ''}")

    payload = run_prediction(
        csv_paths,
        grid_deg=grid,
        horizon=window,
        stride=stride,
        reference_date=ref,
        out_path=out,
        model_dir=cfg.path_of("models"),
        progress=_progress,
    )
    m = payload.get("metrics", {})
    typer.echo(
        f"Modèle : {payload['model']['type']} — {len(payload['cells'])} cellules, "
        f"référence {payload['reference_date']} ({payload['estimate_kind']})"
    )
    typer.echo(
        f"Test : PR-AUC={m.get('pr_auc')} F1={m.get('f1')} recall={m.get('recall')} "
        f"Brier={m.get('brier')}"
    )
    record_step(cfg, "predict", "ok",
                f"fire_risk.json — {payload['model']['type']}, origine={payload['data_origin']}")


@app.command("web-artifacts")
def web_artifacts() -> None:
    """Vérifie/synchronise les artefacts JSON consommés par le frontend."""
    cfg = load_config()
    art = _artifacts(cfg)
    expected = ["audit.json", "baselines.json", "observability.json", "execution.json", "inventory.json"]
    for name in expected:
        p = art / name
        typer.echo(f"  {'OK ' if p.exists() else 'MANQUANT'} {p}")
    (art / "generated_at.txt").write_text(now_iso() + "\n", encoding="utf-8")


if __name__ == "__main__":
    app()

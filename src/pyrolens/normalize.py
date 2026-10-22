"""Normalisation des CSV FIRMS téléchargés en fenêtres canoniques de 5 jours.

Les téléchargements ont été lancés par tranches de dates avec des grilles de
5 jours d'origines différentes (début de tranche), ce qui a produit des
fichiers CHEVAUCHANTS : une même détection peut apparaître dans deux fichiers.
Ce module réécrit l'arborescence en fenêtres canoniques (ancrage =
period.start, pas de 5 jours), en supprimant les doublons stricts de lignes,
avec une comptabilité vérifiée ligne à ligne :

    lignes lues = lignes écrites + doublons stricts supprimés

Aucune ligne n'est modifiée (le texte brut est conservé), aucune coordonnée
n'est corrigée. L'opération échoue (sans rien supprimer) si un fichier ne
respecte pas les en-têtes attendus ou si la comptabilité ne tombe pas juste.
"""

from __future__ import annotations

import bisect
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

FILE_RE = re.compile(r"^(?P<src>[a-z0-9_]+)_(?P<start>\d{4}-\d{2}-\d{2})_(?P<end>\d{4}-\d{2}-\d{2})\.csv$")


def canonical_windows(anchor: date, last: date, chunk_days: int = 5) -> list[tuple[date, date]]:
    windows = []
    cur = anchor
    while cur <= last:
        end = min(cur + timedelta(days=chunk_days - 1), last)
        windows.append((cur, end))
        cur = end + timedelta(days=1)
    return windows


def normalize_firms_dir(firms_dir: Path, anchor: date, period_end: date) -> dict[str, Any]:
    firms_dir = Path(firms_dir)
    inputs = sorted(p for p in firms_dir.glob("*.csv") if FILE_RE.match(p.name))
    if not inputs:
        raise ValueError(f"aucun CSV FIRMS dans {firms_dir}")

    # Regroupement par source FIRMS (modis_sp, viirs_snpp_sp, ...)
    by_src: dict[str, list[Path]] = {}
    for p in inputs:
        by_src.setdefault(FILE_RE.match(p.name).group("src"), []).append(p)

    tmp_dir = firms_dir / ".norm_tmp"
    if tmp_dir.exists():
        for old in tmp_dir.glob("*"):
            old.unlink()
    tmp_dir.mkdir(parents=True, exist_ok=True)

    stats: dict[str, Any] = {
        "anchor": anchor.isoformat(),
        "chunk_days": 5,
        "sources": {},
        "files_in": len(inputs),
        "rows_in": 0,
        "rows_out": 0,
        "duplicate_rows_removed": 0,
        "files_out": 0,
    }
    canonical_names: set[str] = set()
    windows = canonical_windows(anchor, period_end)

    try:
        for src, paths in sorted(by_src.items()):
            header: list[str] | None = None
            handles: dict[tuple[date, date], Any] = {}
            rows_in = 0
            win_starts = [w[0] for w in windows]
            try:
                for p in paths:
                    with p.open("r", encoding="utf-8") as fh:
                        first = fh.readline().rstrip("\n")
                        cols = first.split(",")
                        if header is None:
                            header = cols
                        elif cols != header:
                            raise ValueError(f"en-tête différent dans {p.name} (source {src})")
                        if "acq_date" not in cols:
                            raise ValueError(f"colonne acq_date absente de {p.name}")
                        di = cols.index("acq_date")
                        n_cols = len(cols)
                        for line in fh:
                            line = line.rstrip("\n")
                            if not line:
                                continue
                            parts = line.split(",")
                            if len(parts) != n_cols:
                                raise ValueError(
                                    f"{p.name}: ligne à {len(parts)} champs au lieu de {n_cols} "
                                    "(normalisation refusée, audit en charge des lignes mal formées)")
                            d = date.fromisoformat(parts[di])
                            if d < anchor or d > period_end:
                                raise ValueError(f"{p.name}: date {d} hors période cible")
                            idx = bisect.bisect_right(win_starts, d) - 1
                            win = windows[idx]
                            h = handles.get(win)
                            if h is None:
                                h = (tmp_dir / f"{src}__{win[0].isoformat()}__{win[1].isoformat()}.tmp").open(
                                    "a", encoding="utf-8")
                                handles[win] = h
                            h.write(line + "\n")
                            rows_in += 1
            finally:
                for h in handles.values():
                    h.close()
            if header is None:
                raise ValueError(f"source {src}: aucun contenu")
            buckets = {
                win: tmp_dir / f"{src}__{win[0].isoformat()}__{win[1].isoformat()}.tmp"
                for win in handles
            }

            # Écriture canonique avec dédoublonnage strict, puis comptabilité
            rows_out = 0
            dups = 0
            for win, bp in sorted(buckets.items()):
                seen: set[str] = set()
                uniq: list[str] = []
                with bp.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.rstrip("\n")
                        if line in seen:
                            dups += 1
                        else:
                            seen.add(line)
                            uniq.append(line)
                name = f"{src}_{win[0].isoformat()}_{win[1].isoformat()}.csv"
                target = firms_dir / name
                tmp = target.with_name(target.name + ".part")
                with tmp.open("w", encoding="utf-8") as out:
                    out.write("\n".join([",".join(header)] + uniq) + "\n")
                tmp.replace(target)
                canonical_names.add(name)
                rows_out += len(uniq)
                bp.unlink()

            if rows_in != rows_out + dups:
                raise ValueError(
                    f"comptabilité incorrecte pour {src} : lu={rows_in}, "
                    f"écrit={rows_out}, doublons={dups}")
            stats["sources"][src] = {
                "files_in": len(paths),
                "rows_in": rows_in,
                "rows_out": rows_out,
                "duplicate_rows_removed": dups,
                "files_out": len(buckets),
            }
            stats["rows_in"] += rows_in
            stats["rows_out"] += rows_out
            stats["duplicate_rows_removed"] += dups
            stats["files_out"] += len(buckets)

        # Comptabilité globale avant toute suppression
        if stats["rows_in"] != stats["rows_out"] + stats["duplicate_rows_removed"]:
            raise ValueError("comptabilité globale incorrecte : aucune suppression effectuée")

        removed: list[str] = []
        for p in inputs:
            if p.name not in canonical_names:
                p.unlink()
                removed.append(p.name)
        stats["files_removed"] = len(removed)
        stats["files_removed_names"] = removed
    finally:
        for left in tmp_dir.glob("*"):
            left.unlink()
        tmp_dir.rmdir()

    return stats

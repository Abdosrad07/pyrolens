"""Lecture des CSV FIRMS en préservant strictement le contenu brut.

Le parseur est ligne à ligne : chaque ligne physique est conservée telle quelle,
les lignes mal formées sont signalées avec leur numéro de ligne et le motif, et
aucune valeur n'est réparée automatiquement.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .schema import normalize_header


@dataclass
class Anomaly:
    file: str
    line_number: int
    column: str
    raw_value: str
    category: str
    reason: str
    classification: str = "excluded"  # valid | ambiguous | reconstructed | excluded

    def as_row(self) -> dict[str, str]:
        return {
            "file": self.file,
            "line_number": str(self.line_number),
            "column": self.column,
            "raw_value": self.raw_value,
            "category": self.category,
            "reason": self.reason,
            "classification": self.classification,
        }


@dataclass
class ParsedFile:
    path: Path
    header: list[str]
    raw_header: list[str]
    records: list[dict[str, str]] = field(default_factory=list)
    record_lines: list[int] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.name


def parse_csv_file(path: str | Path) -> ParsedFile:
    """Parse un CSV FIRMS. Les lignes mal formées sont isolées, jamais corrigées."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        raise ValueError(f"Fichier vide : {p}")

    # En-tête (première ligne non vide)
    header_idx = next((i for i, line in enumerate(lines) if line.strip()), None)
    if header_idx is None:
        raise ValueError(f"Fichier sans en-tête : {p}")
    raw_header = next(csv.reader([lines[header_idx]]))
    header = normalize_header(raw_header)
    parsed = ParsedFile(path=p, header=header, raw_header=raw_header)

    if len(set(header)) != len(header):
        parsed.anomalies.append(
            Anomaly(
                file=p.name,
                line_number=header_idx + 1,
                column=",".join(raw_header),
                raw_value=lines[header_idx],
                category="duplicate_column",
                reason="en-tête avec colonnes dupliquées après normalisation",
                classification="excluded",
            )
        )

    n_fields = len(header)
    for offset, line in enumerate(lines[header_idx + 1 :], start=header_idx + 2):
        if not line.strip():
            continue
        fields = next(csv.reader([line]))
        if len(fields) != n_fields:
            parsed.anomalies.append(
                Anomaly(
                    file=p.name,
                    line_number=offset,
                    column="<ligne>",
                    raw_value=line,
                    category="malformed_row",
                    reason=(
                        f"{len(fields)} champs pour {n_fields} colonnes attendues"
                    ),
                    classification="excluded",
                )
            )
            continue
        record = dict(zip(header, fields))
        parsed.records.append(record)
        parsed.record_lines.append(offset)
    return parsed

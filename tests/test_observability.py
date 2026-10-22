"""Tests de la classification en 4 états d'observabilité (aucun « pas de feu »)."""

from __future__ import annotations

from datetime import date

from pyrolens.observability import (
    STATE_DETECTED,
    STATE_INDETERMINATE,
    STATE_NO_DET,
    STATE_UNKNOWN,
    classify_states,
    coverage_absent_states,
)

ALLOWED = {STATE_DETECTED, STATE_NO_DET, STATE_UNKNOWN, STATE_INDETERMINATE}


def _rows(coords):
    return [
        {"longitude": lon, "latitude": lat, "acq_date": date(2019, 1, 10)}
        for lon, lat in coords
    ]


def test_without_coverage_only_detected_or_unknown():
    rows = {"terra": _rows([(10.0, 6.0)]), "aqua": _rows([(12.0, 7.0)])}
    states = coverage_absent_states(rows, 0.25)
    for counter in states.values():
        assert set(counter) <= ALLOWED
    # l'état par défaut est l'observabilité inconnue, jamais « pas de feu »
    assert states["terra"][STATE_UNKNOWN] > 0
    assert STATE_NO_DET not in states["terra"]
    assert states["terra"][STATE_DETECTED] == 1


def test_with_coverage_can_state_plausible_conditions():
    rows = {"terra": _rows([(10.0, 6.0)])}
    coverage = {("0:0", "2019-01-10"): "not_observed", ("1:1", "2019-01-10"): "clear_observed",
                ("2:2", "2019-01-10"): "cloudy"}
    states = classify_states(rows, 0.25, coverage_available=True, coverage=coverage)
    counter = states["terra"]
    assert counter[STATE_DETECTED] >= 1
    assert counter[STATE_NO_DET] == 1
    assert counter[STATE_UNKNOWN] == 1
    assert counter[STATE_INDETERMINATE] == 1
    assert set(counter) <= ALLOWED


def test_states_are_never_interpreted_as_no_fire():
    rows = {"terra": _rows([(10.0, 6.0)]), "viirs": []}
    states = coverage_absent_states(rows, 0.25)
    assert all("fire" not in state and "feu" not in state for state in states["terra"])

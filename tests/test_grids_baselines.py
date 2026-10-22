"""Tests de grilles, fenêtres, clés d'ensembles et métriques (Jaccard sur cas connus)."""

from __future__ import annotations

from pyrolens.baselines import compare_sets, select_rows
from pyrolens.grids import build_set, cell_id, epoch_days, make_key, window_index, window_start
from datetime import date


def test_cell_id_origin_and_edges():
    assert cell_id(-180.0, -90.0, 0.25) == (0, 0)
    assert cell_id(0.0, 0.0, 0.25) == (720, 360)
    # point strictement à la frontière haute de la cellule
    assert cell_id(0.0, 0.0, 0.10) == (1800, 900)
    # même cellule pour des points proches
    assert cell_id(10.00, 6.00, 0.25) == cell_id(10.01, 6.01, 0.25)


def test_window_index_alignment_and_roundtrip():
    # fenêtres alignées sur l'epoch (1970-01-01), pas sur le mois
    d1 = date(2019, 1, 15)
    start = window_start(window_index(d1, 8), 8)
    assert window_index(start, 8) == epoch_days(start) // 8
    # toute date de la même fenêtre partage la même clé de fenêtre
    from datetime import timedelta

    same = start + timedelta(days=7)
    next_one = start + timedelta(days=8)
    assert window_index(start, 8) == window_index(same, 8)
    assert window_index(next_one, 8) == window_index(start, 8) + 1
    # aller-retour
    assert window_start(window_index(d1, 8), 8) <= d1
    assert window_start(window_index(d1, 8) + 1, 8) > d1


def test_key_definitions():
    k1 = make_key(10.0, 6.0, "2019-01-15", 0.25, 1)
    assert "|" in k1
    assert k1.endswith("2019-01-15")          # (cellule, date)
    k8 = make_key(10.0, 6.0, "2019-01-15", 0.25, 8)
    assert "|w" in k8                          # (cellule, fenêtre)
    # même clé pour deux dates de la MÊME fenêtre alignée
    start = window_start(window_index(date(2019, 1, 15), 8), 8)
    from datetime import timedelta

    d_a, d_b = start, start + timedelta(days=5)
    assert make_key(10.0, 6.0, d_a.isoformat(), 0.25, 8) == make_key(
        10.0, 6.0, d_b.isoformat(), 0.25, 8
    )
    assert make_key(10.0, 6.0, (start + timedelta(days=8)).isoformat(), 0.25, 8) != k8


def test_build_set_is_a_set_of_keys():
    rows = [
        {"longitude": 10.00, "latitude": 6.00, "acq_date": date(2019, 1, 15)},
        {"longitude": 10.01, "latitude": 6.01, "acq_date": date(2019, 1, 15)},  # même cellule 0,25°
        {"longitude": 10.15, "latitude": 6.10, "acq_date": date(2019, 1, 15)},  # même cellule 0,25° mais autre cellule 0,10°
        {"longitude": 10.00, "latitude": 6.00, "acq_date": date(2019, 1, 15)},  # doublon de clé
    ]
    assert len(build_set(rows, 0.25, 1)) == 1
    assert len(build_set(rows, 0.10, 1)) == 2   # découpage plus fin → 2 cellules
    # clé stable : une date différente change la clé en fenêtre de 1 jour
    other = [{**rows[0], "acq_date": date(2019, 1, 16)}]
    assert build_set(other, 0.25, 1) != build_set(rows[:1], 0.25, 1)


def test_jaccard_known_values():
    a = {"1:1|2019-01-01", "1:2|2019-01-01", "2:2|2019-01-01"}
    b = {"1:1|2019-01-01", "3:3|2019-01-01"}
    cmp = compare_sets("x", a, b, 0.25, 1)
    assert cmp.a_size == 3 and cmp.b_size == 2
    assert cmp.intersection == 1
    assert cmp.union == 4
    assert abs(cmp.jaccard - 0.25) < 1e-12
    # cas limites
    assert compare_sets("x", set(), set(), 0.25, 1).jaccard == 0.0
    assert compare_sets("x", a, a, 0.25, 1).jaccard == 1.0


def test_select_rows_filters_by_kind_and_satellite():
    cfg_rows = [
        {"sensor": "modis", "satellite": "Terra"},
        {"sensor": "modis", "satellite": "Aqua"},
        {"sensor": "viirs", "satellite": "N"},
        {"sensor": "viirs", "satellite": "1"},   # NOAA-20 : hors pilote S-NPP
    ]

    class Cfg:
        def get(self, key, default=None):
            data = {
                "sensors.terra": {"kind": "modis", "satellites": ["Terra"], "label": "MODIS Terra"},
                "sensors.aqua": {"kind": "modis", "satellites": ["Aqua"], "label": "MODIS Aqua"},
                "sensors.viirs_snpp": {"kind": "viirs", "satellites": ["N"], "label": "VIIRS S-NPP"},
            }
            return data.get(key, default)

    cfg = Cfg()
    assert len(select_rows(cfg_rows, cfg, "terra")) == 1
    assert len(select_rows(cfg_rows, cfg, "aqua")) == 1
    viirs = select_rows(cfg_rows, cfg, "viirs_snpp")
    assert len(viirs) == 1 and viirs[0]["satellite"] == "N"

import sys
from math import log10
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aashto93 import (ParametrosRigido, espesor_requerido, log_w18_admisible,
                      zr_desde_confiabilidad, ec_desde_fc)

# Ejemplo de la Guía AASHTO 1993 (Fig. 3.7): el nomograma da D ≈ 10.0 pulg
EJEMPLO_GUIA = ParametrosRigido(W18=5.1e6, R=0.95, S0=0.29, p0=4.2, pt=2.5,
                                Sc=650, Ec=5e6, k=72, J=3.2, Cd=1.0)


def test_zr_tabla_aashto():
    assert zr_desde_confiabilidad(0.95) == pytest.approx(-1.645, abs=1e-3)
    assert zr_desde_confiabilidad(0.90) == pytest.approx(-1.282, abs=1e-3)
    assert zr_desde_confiabilidad(0.50) == pytest.approx(0.0, abs=1e-9)


def test_ejemplo_guia_aashto():
    D = espesor_requerido(EJEMPLO_GUIA)
    assert 9.5 < D < 10.1


def test_la_raiz_cumple_la_ecuacion():
    D = espesor_requerido(EJEMPLO_GUIA)
    assert log_w18_admisible(D, EJEMPLO_GUIA) == pytest.approx(log10(5.1e6), abs=1e-6)


def test_mas_trafico_mas_espesor():
    base = espesor_requerido(EJEMPLO_GUIA)
    p = ParametrosRigido(**{**EJEMPLO_GUIA.__dict__, "W18": 2e7})
    assert espesor_requerido(p) > base


def test_mejor_concreto_menos_espesor():
    base = espesor_requerido(EJEMPLO_GUIA)
    p = ParametrosRigido(**{**EJEMPLO_GUIA.__dict__, "Sc": 750})
    assert espesor_requerido(p) < base


def test_ec_aci():
    # f'c = 280 kg/cm² ≈ 3983 psi -> Ec ≈ 3.6e6 psi
    assert ec_desde_fc(280) == pytest.approx(3.597e6, rel=1e-3)

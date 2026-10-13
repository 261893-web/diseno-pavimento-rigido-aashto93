"""
Diseño de espesor de losa para pavimentos rígidos según la Guía AASHTO 1993.

La ecuación de diseño no se puede despejar para D, así que se resuelve
numéricamente (método de Brent) buscando el D que hace que el número
de ejes equivalentes admisibles sea igual al de diseño.

Unidades de la ecuación original (sistema inglés):
    D  [pulg], Sc [psi], Ec [psi], k [pci]
Se incluyen funciones de conversión para trabajar en SI.
"""
from dataclasses import dataclass
from math import log10, sqrt

from scipy.optimize import brentq
from scipy.stats import norm

MPA_A_PSI = 145.0377
PULG_A_CM = 2.54
MPA_M_A_PCI = 3.684      # 1 MPa/m ≈ 3.684 pci


def zr_desde_confiabilidad(R):
    """Desviación normal estándar para una confiabilidad R (0-1).
    Ej.: R = 0.95 -> ZR = -1.645"""
    return norm.ppf(1 - R)


@dataclass
class ParametrosRigido:
    W18: float          # ejes equivalentes de 18 kip (8.2 t) en el periodo de diseño
    R: float            # confiabilidad (0-1)
    S0: float           # desviación estándar global (0.30-0.40 en rígidos)
    p0: float           # serviciabilidad inicial
    pt: float           # serviciabilidad final
    Sc: float           # módulo de rotura del concreto [psi]
    Ec: float           # módulo elástico del concreto [psi]
    k: float            # módulo de reacción efectivo de la subrasante [pci]
    J: float = 3.2      # coeficiente de transferencia de carga
    Cd: float = 1.0     # coeficiente de drenaje


def log_w18_admisible(D, p: ParametrosRigido):
    """Lado derecho de la ecuación AASHTO 93 para un espesor D [pulg]."""
    ZR = zr_desde_confiabilidad(p.R)
    dpsi = p.p0 - p.pt
    t1 = ZR * p.S0
    t2 = 7.35 * log10(D + 1) - 0.06
    t3 = log10(dpsi / (4.5 - 1.5)) / (1 + 1.624e7 / (D + 1) ** 8.46)
    num = p.Sc * p.Cd * (D**0.75 - 1.132)
    den = 215.63 * p.J * (D**0.75 - 18.42 / (p.Ec / p.k) ** 0.25)
    t4 = (4.22 - 0.32 * p.pt) * log10(num / den)
    return t1 + t2 + t3 + t4


def espesor_requerido(p: ParametrosRigido, d_min=4.0, d_max=20.0):
    """Espesor de losa D [pulg] que satisface exactamente W18."""
    objetivo = log10(p.W18)
    f = lambda D: log_w18_admisible(D, p) - objetivo
    if f(d_min) > 0:
        return d_min
    if f(d_max) < 0:
        raise ValueError("Se necesita más de %.0f pulg; revisa los datos." % d_max)
    return brentq(f, d_min, d_max, xtol=1e-6)


def ec_desde_fc(fc_kgcm2):
    """Ec [psi] con la expresión ACI: Ec = 57000·√f'c (f'c en psi)."""
    fc_psi = fc_kgcm2 * 14.2233
    return 57000 * sqrt(fc_psi)


def redondeo_constructivo(D_pulg, paso_cm=0.5):
    """Lleva el espesor a cm y lo redondea hacia arriba al paso indicado."""
    from math import ceil
    d_cm = D_pulg * PULG_A_CM
    return ceil(d_cm / paso_cm) * paso_cm

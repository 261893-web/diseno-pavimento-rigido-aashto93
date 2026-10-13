"""
Caso de aplicación: vía urbana de pavimento rígido en Cusco.
Calcula el espesor de losa y hace un análisis de sensibilidad
para ver qué parámetros pesan más en el diseño.
"""
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
from aashto93 import (ParametrosRigido, espesor_requerido, ec_desde_fc,
                      redondeo_constructivo, MPA_A_PSI, MPA_M_A_PCI, PULG_A_CM)

# ---- datos de diseño (supuestos razonables para una vía colectora) ----
fc = 280                         # kg/cm²
MR = 4.5                         # MPa, módulo de rotura a 28 días
k_sub = 40                       # MPa/m, subrasante con base granular

base = ParametrosRigido(
    W18=3.0e6, R=0.85, S0=0.35, p0=4.5, pt=2.5,
    Sc=MR * MPA_A_PSI, Ec=ec_desde_fc(fc), k=k_sub * MPA_M_A_PCI,
    J=3.2, Cd=1.0,
)

D = espesor_requerido(base)
print("=== Diseño AASHTO 93 - pavimento rígido ===")
print(f"W18 = {base.W18:.2e} EE | R = {base.R:.0%} | S0 = {base.S0}")
print(f"Sc = {base.Sc:.0f} psi | Ec = {base.Ec:.3e} psi | k = {base.k:.0f} pci")
print(f"Espesor requerido: {D:.2f} pulg = {D * PULG_A_CM:.1f} cm")
print(f"Espesor constructivo: {redondeo_constructivo(D, 1.0):.0f} cm")

# ---- sensibilidad: cuánto cambia D si cada parámetro varía ±20 % ----
variables = {
    "Tránsito W18": "W18",
    "Módulo de rotura Sc": "Sc",
    "Subrasante k": "k",
    "Transferencia J": "J",
    "Drenaje Cd": "Cd",
}
tornado = []
for etiqueta, attr in variables.items():
    v = getattr(base, attr)
    d_bajo = espesor_requerido(replace(base, **{attr: v * 0.8})) * PULG_A_CM
    d_alto = espesor_requerido(replace(base, **{attr: v * 1.2})) * PULG_A_CM
    tornado.append((etiqueta, d_bajo, d_alto))
tornado.sort(key=lambda t: abs(t[2] - t[1]))

fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))

ax = axs[0]
D_cm = D * PULG_A_CM
for y, (et, lo, hi) in enumerate(tornado):
    ax.barh(y, lo - D_cm, left=D_cm, color="#2e86c1")
    ax.barh(y, hi - D_cm, left=D_cm, color="#e67e22")
ax.axvline(D_cm, color="k", lw=1)
ax.set_yticks(range(len(tornado)), [t[0] for t in tornado])
ax.set_xlabel("Espesor de losa [cm]")
ax.set_title("Sensibilidad del espesor a ±20 % en cada parámetro")
ax.legend(["Caso base", "−20 %", "+20 %"], loc="lower right", fontsize=8)

# ---- curvas de diseño: espesor vs tránsito para varios MR ----
ax = axs[1]
W = np.logspace(5.7, 7.7, 40)
for mr in (4.0, 4.5, 5.0):
    d = [espesor_requerido(replace(base, W18=w, Sc=mr * MPA_A_PSI)) * PULG_A_CM for w in W]
    ax.semilogx(W, d, lw=2, label=f"MR = {mr} MPa")
ax.set_xlabel("Ejes equivalentes W18")
ax.set_ylabel("Espesor de losa [cm]")
ax.set_title("Curvas de diseño (R = 85 %, k = 40 MPa/m)")
ax.grid(True, which="both", alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig(RAIZ / "figuras" / "sensibilidad_y_curvas.png", dpi=150)
print("Figura guardada en figuras/sensibilidad_y_curvas.png")

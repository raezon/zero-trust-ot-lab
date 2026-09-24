"""
Automate (PLC) simule — niveau 1 du modele de Purdue.

Pilote un petit procede : une cuve alimentee par une pompe, chauffee vers une
consigne, avec une vanne de decharge (V-101). Les grandeurs physiques evoluent
dans le temps (simulation legere, avancee a chaque lecture) et reagissent aux
commandes : c'est ce qui donne des "donnees reelles" au tableau de bord et au
terminal du lab.

Dans l'architecture Zero-Trust, l'automate NE DOIT etre joignable QUE via la
passerelle (conduit). En mode "legacy" (reseau plat), il est joignable
directement : c'est precisement le probleme que l'on demontre.
"""
from __future__ import annotations

import random
import time

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="PLC (niveau 1) - simulateur de procede")

# Etat nominal du procede (point de depart / RESET).
ETAT_NOMINAL = {
    "tank_level_pct": 62.0,   # niveau de cuve
    "temperature_C": 68.0,    # temperature produit
    "setpoint_C": 68.0,       # consigne de chauffe
    "pressure_bar": 1.90,     # pression ligne
    "flow_m3h": 125.0,        # debit
    "pump_on": True,          # pompe d'alimentation
    "valve_open": False,      # vanne de decharge V-101
    "line_running": True,     # ligne en production
}
STATE = dict(ETAT_NOMINAL)
_LAST = time.time()

# Programme automate (logique ladder simplifiee) : propriete intellectuelle du
# procede. Sa lecture = vol de savoir-faire + preparation d'une attaque ciblee.
PROGRAMME = {
    "nom": "LIGNE_PVC_NANTES_V3.2",
    "automate": "PLC-N1-01 (simule)",
    "rungs": [
        "IF tank_level > 85% THEN CLOSE V-101",
        "IF temperature > 78C THEN STOP_LINE",
        "IF pressure > 2.4 bar THEN OPEN V-102 (decharge securite)",
    ],
    "seuils_securite": {"niveau_max_pct": 85, "temp_max_C": 78, "pression_max_bar": 2.4},
}

# Description des capteurs de terrain (niveau 0) remontes par l'automate.
CAPTEURS = [
    {"tag": "LT-101", "type": "niveau",      "cle": "tank_level_pct", "unite": "%"},
    {"tag": "TT-102", "type": "temperature", "cle": "temperature_C",  "unite": "C"},
    {"tag": "PT-103", "type": "pression",    "cle": "pressure_bar",   "unite": "bar"},
    {"tag": "FT-104", "type": "debit",       "cle": "flow_m3h",       "unite": "m3/h"},
]


class ExecIn(BaseModel):
    action: str
    params: dict = {}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _tick():
    """Avance la simulation physique depuis la derniere lecture."""
    global _LAST
    now = time.time()
    dt = min(now - _LAST, 5.0)  # borne pour eviter les sauts apres inactivite
    _LAST = now
    s = STATE

    # Temperature : converge vers la consigne si la ligne tourne.
    if s["line_running"]:
        s["temperature_C"] += (s["setpoint_C"] - s["temperature_C"]) * 0.15 * dt
    else:
        s["temperature_C"] += (20.0 - s["temperature_C"]) * 0.05 * dt  # refroidit
    s["temperature_C"] += random.uniform(-0.15, 0.15)

    # Niveau de cuve : la pompe remplit, la vanne vide.
    inflow = 3.0 * dt if (s["pump_on"] and s["line_running"]) else 0.0
    outflow = 5.0 * dt if s["valve_open"] else 0.0
    s["tank_level_pct"] = _clamp(s["tank_level_pct"] + inflow - outflow, 0.0, 100.0)

    # Pression : monte avec le niveau, chute quand la vanne s'ouvre.
    if s["valve_open"]:
        s["pressure_bar"] -= 0.25 * dt
    else:
        s["pressure_bar"] += (s["tank_level_pct"] - 60.0) * 0.004 * dt
    s["pressure_bar"] = _clamp(s["pressure_bar"] + random.uniform(-0.02, 0.02), 0.0, 4.0)

    # Debit.
    base = 125.0 if s["line_running"] else 0.0
    if s["valve_open"]:
        base *= 0.6  # fuite par la decharge
    s["flow_m3h"] = _clamp(base + random.uniform(-2, 2), 0.0, 200.0)


def _alarmes():
    s, al = STATE, []
    seuils = PROGRAMME["seuils_securite"]
    if s["valve_open"] and s["line_running"]:
        al.append("V-101 ouverte EN PRODUCTION : deversement produit — procede impacte !")
    if s["tank_level_pct"] >= seuils["niveau_max_pct"]:
        al.append(f"Niveau cuve haut ({s['tank_level_pct']:.0f}%)")
    if s["tank_level_pct"] <= 5:
        al.append("Cuve quasi vide : desamorcage pompe")
    if s["pressure_bar"] >= seuils["pression_max_bar"]:
        al.append(f"Surpression ({s['pressure_bar']:.2f} bar)")
    if s["temperature_C"] >= seuils["temp_max_C"]:
        al.append(f"Surchauffe ({s['temperature_C']:.1f} C)")
    return al


def _snapshot():
    _tick()
    s = STATE
    return {
        "tank_level_pct": round(s["tank_level_pct"], 1),
        "temperature_C": round(s["temperature_C"], 1),
        "setpoint_C": round(s["setpoint_C"], 1),
        "pressure_bar": round(s["pressure_bar"], 2),
        "flow_m3h": round(s["flow_m3h"], 1),
        "pump_on": s["pump_on"],
        "valve_open": s["valve_open"],
        "line_running": s["line_running"],
        "alarmes": _alarmes(),
    }


def _sensors():
    snap = _snapshot()
    return [
        {"tag": c["tag"], "type": c["type"], "valeur": snap[c["cle"]], "unite": c["unite"]}
        for c in CAPTEURS
    ]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/state")
def state():
    return _snapshot()


@app.get("/sensors")
def sensors():
    return {"capteurs": _sensors()}


@app.post("/execute")
def execute(body: ExecIn):
    a = body.action
    if a == "OPEN_VALVE":
        STATE["valve_open"] = True
        snap = _snapshot()
        return {"ok": True, "message": "/!\\ VANNE V-101 OUVERTE — decharge en cours, procede physique impacte",
                "state": snap}
    if a == "CLOSE_VALVE":
        STATE["valve_open"] = False
        return {"ok": True, "message": "Vanne V-101 fermee", "state": _snapshot()}
    if a == "STOP_LINE":
        STATE["line_running"] = False
        STATE["pump_on"] = False
        return {"ok": True, "message": "/!\\ LIGNE ARRETEE — production interrompue", "state": _snapshot()}
    if a == "START_LINE":
        STATE["line_running"] = True
        STATE["pump_on"] = True
        return {"ok": True, "message": "Ligne redemarree", "state": _snapshot()}
    if a == "SET_SETPOINT":
        STATE["setpoint_C"] = _clamp(float(body.params.get("value", STATE["setpoint_C"])), 20.0, 95.0)
        return {"ok": True, "message": f"Consigne = {STATE['setpoint_C']:.1f} C", "state": _snapshot()}
    if a in ("READ_SENSORS", "READ_METRICS"):
        return {"ok": True, "capteurs": _sensors()}
    if a == "READ_STATE":
        return {"ok": True, "state": _snapshot()}
    if a == "READ_PROGRAM":
        return {"ok": True, "program": PROGRAMME}
    if a == "RESET":
        STATE.update(ETAT_NOMINAL)
        return {"ok": True, "message": "Etat nominal restaure", "state": _snapshot()}
    return {"ok": False, "message": f"action inconnue: {a}"}

"""
Supervision SCADA / historian — niveau 3 du modele de Purdue.
Expose des metriques de supervision (lecture seule).
"""
from __future__ import annotations

import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SCADA (niveau 3) - simulateur")

# Donnees sensibles hebergees par la supervision : cibles typiques d'un
# attaquant (espionnage industriel, preparation d'une attaque sur le procede).
RECETTES = [
    {"id": "RX-PVC-12", "produit": "Tube PVC 110mm", "temp_C": 68, "debit_m3h": 125},
    {"id": "RX-PVC-20", "produit": "Tube PVC 200mm", "temp_C": 71, "debit_m3h": 140},
    {"id": "RX-PEHD-07", "produit": "Gaine PEHD", "temp_C": 64, "debit_m3h": 110},
]
TOPOLOGIE = {
    "automates": [{"tag": "PLC-N1-01", "adresse": "plc:8000", "role": "vanne V-101"}],
    "ihm": [{"tag": "HMI-N2-01", "poste": "salle de controle Nantes"}],
    "comptes_service": ["svc_historian", "svc_opc_ua"],
}


class ExecIn(BaseModel):
    action: str
    params: dict = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/state")
def state():
    """Etat de supervision pour le tableau de bord (lecture seule)."""
    return {
        "temperature_C": round(60 + random.random() * 5, 2),
        "pression_bar": round(1.8 + random.random() * 0.2, 2),
        "debit_m3h": round(120 + random.random() * 10, 1),
        "nb_recettes": len(RECETTES),
        "nb_automates": len(TOPOLOGIE["automates"]),
    }


@app.post("/execute")
def execute(body: ExecIn):
    if body.action in ("READ_METRICS", "READ_STATE"):
        return {"ok": True, "metrics": {
            "temperature_C": round(60 + random.random() * 5, 2),
            "pression_bar": round(1.8 + random.random() * 0.2, 2),
            "debit_m3h": round(120 + random.random() * 10, 1),
        }}
    if body.action == "EXPORT_RECIPES":
        return {"ok": True, "recipes": RECETTES}
    if body.action == "READ_TOPOLOGY":
        return {"ok": True, "topology": TOPOLOGIE}
    return {"ok": False, "message": f"action non supportee par le SCADA: {body.action}"}

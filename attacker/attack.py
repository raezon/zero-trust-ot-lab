"""
Scenario pedagogique — mouvement lateral IT -> OT, lu couche par couche
(modele de Purdue).

/!\\ Usage strictement pedagogique, dans le lab fourni. Aucune technique
d'exploitation reelle : on envoie de simples requetes HTTP a des services
SIMULES pour illustrer l'effet de la segmentation et du Zero-Trust.

Le scenario est joue DEPUIS le conteneur attacker (zone IT). C'est important :
seule cette vue reseau permet de constater honnetement la microsegmentation
(en Zero-Trust, l'automate n'existe meme pas pour l'attaquant).

En fin de course, le resultat structure (statut de chaque equipement, donnees
exposees, controle ayant bloque) est envoye au tableau de bord de la passerelle
(POST /dashboard/report) pour affichage graphique.
"""
from __future__ import annotations

import os
import time

import httpx

PLC_URL = os.environ.get("PLC_URL", "http://plc:8000")
SCADA_URL = os.environ.get("SCADA_URL", "http://scada:8000")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://gateway:8000")
STOLEN_TOKEN = os.environ.get("STOLEN_TOKEN", "tok-admin-it")  # identifiant IT hameconne
TIMEOUT = 3
SEP = "=" * 68

# Statuts, du plus grave au moins grave.
COMPROMIS = "compromis"      # l'attaquant controle/modifie l'equipement
EXPOSE = "expose"            # donnees lues, mais pas de controle du procede
BLOQUE = "bloque"            # tentative arretee par un controle de securite
NON_ATTEINT = "non_atteint"  # l'attaquant n'a meme pas pu tenter

steps: list[dict] = []


def _step(niveau, equipement, titre, statut, donnees=None, controle="", detail=""):
    s = {
        "niveau": niveau, "equipement": equipement, "titre": titre,
        "statut": statut, "donnees": donnees or [], "controle": controle,
        "detail": detail,
    }
    steps.append(s)
    icone = {COMPROMIS: "[X]", EXPOSE: "[!]", BLOQUE: "[#]", NON_ATTEINT: "[-]"}[statut]
    print(f"  {icone} N{niveau:<3} {equipement:<10} {statut.upper():<12} {titre}")
    if donnees:
        for d in donnees:
            print(f"         └─ derobe : {d}")
    if controle:
        print(f"         └─ bloque par : {controle}")


def _post_direct(base, action):
    r = httpx.post(f"{base}/execute", json={"action": action, "params": {}}, timeout=TIMEOUT)
    return r.json()


def _via_pep(action, target):
    r = httpx.post(
        f"{GATEWAY_URL}/command",
        headers={
            "Authorization": f"Bearer {STOLEN_TOKEN}",
            "X-Source-Zone": "it",
            "X-Device-Posture": "unmanaged",
        },
        json={"target": target, "action": action, "params": {}},
        timeout=TIMEOUT,
    )
    return r.status_code, r.json()


# --------------------------------------------------------------------------- #

def couche_it():
    """Niveaux 5-4 : point d'entree. Hypothese Zero-Trust : deja compromis."""
    _step("5", "mail", "Hameconnage : piece jointe ouverte", COMPROMIS,
          detail="Vecteur d'entree initial (simule).")
    _step("4", "poste_it", "Poste IT sous controle, identifiant recupere", COMPROMIS,
          donnees=[f"Jeton « {STOLEN_TOKEN} » (compte j.durand, role admin_it)"],
          detail="L'attaquant agit desormais avec une identite valide.")


def acces_direct(nom, base, niveau, equipement, actions_lecture, action_controle=None):
    """Tente d'atteindre une ressource OT SANS passer par la passerelle."""
    try:
        httpx.get(f"{base}/health", timeout=TIMEOUT)
    except Exception as exc:
        _step(niveau, equipement, f"Acces direct a {nom} (hors passerelle)", NON_ATTEINT,
              controle=f"Microsegmentation reseau — {nom} injoignable ({type(exc).__name__})",
              detail="La ressource n'existe pas dans la zone de l'attaquant.")
        return
    # Reseau plat : la ressource repond directement.
    donnees = []
    for act in actions_lecture:
        try:
            rep = _post_direct(base, act)
            donnees.append(f"{act} -> {str(rep)[:90]}")
        except Exception:
            pass
    statut = EXPOSE
    detail = "Reseau plat : aucun conduit, l'attaquant lit les donnees."
    if action_controle:
        _post_direct(base, action_controle)
        statut = COMPROMIS
        detail = "Reseau plat : l'attaquant COMMANDE le procede physique."
    _step(niveau, equipement, f"Acces direct a {nom} (hors passerelle)", statut,
          donnees=donnees, detail=detail)


def acces_via_passerelle():
    """Tente via la passerelle, avec le jeton IT vole : le PDP arbitre."""
    tentatives = [
        ("OPEN_VALVE", "plc", "1", "plc", "Ouvrir la vanne via la passerelle"),
        ("EXPORT_RECIPES", "scada", "3", "scada", "Exfiltrer les recettes via la passerelle"),
        ("READ_METRICS", "scada", "3", "scada", "Lire les metriques via la passerelle"),
    ]
    for action, target, niveau, equipement, titre in tentatives:
        try:
            code, rep = _via_pep(action, target)
        except Exception as exc:
            _step(niveau, equipement, titre, NON_ATTEINT,
                  controle=f"Passerelle injoignable ({type(exc).__name__})")
            continue
        if code == 403:
            _step(niveau, equipement, titre, BLOQUE,
                  controle=f"PEP/PDP — {rep.get('principle')} : {rep.get('reason')}")
        elif code == 200 and rep.get("decision") == "ALLOW":
            _step(niveau, equipement, titre, EXPOSE,
                  donnees=[f"{action} -> {str(rep.get('result'))[:90]}"],
                  detail="Autorise : le role vole a legitimement ce droit (lecture).")
        else:
            _step(niveau, equipement, titre, BLOQUE,
                  controle=f"HTTP {code} : {str(rep)[:90]}")


def remonter_rapport():
    mode = "reseau-plat"
    if any(s["equipement"] in ("plc", "scada") and s["statut"] == NON_ATTEINT for s in steps):
        mode = "zero-trust"
    payload = {"mode": mode, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": steps}
    try:
        httpx.post(f"{GATEWAY_URL}/dashboard/report", json=payload, timeout=TIMEOUT)
        print(f"\n  Rapport envoye au tableau de bord ({mode}).")
    except Exception as exc:
        print(f"\n  (Tableau de bord injoignable : {type(exc).__name__} — mode {mode}.)")


if __name__ == "__main__":
    print(SEP)
    print(" SCENARIO PEDAGOGIQUE — progression IT -> OT par couche (Purdue)")
    print(SEP)
    couche_it()
    print("  " + "-" * 64)
    print("  Tentative 1 : acces DIRECT aux ressources OT (test de segmentation)")
    acces_direct("l'automate", PLC_URL, "1", "plc",
                 actions_lecture=["READ_PROGRAM", "READ_STATE"], action_controle="OPEN_VALVE")
    acces_direct("le SCADA", SCADA_URL, "3", "scada",
                 actions_lecture=["EXPORT_RECIPES", "READ_TOPOLOGY"])
    print("  " + "-" * 64)
    print("  Tentative 2 : via la PASSERELLE avec le jeton IT vole (test de politique)")
    acces_via_passerelle()
    print(SEP)
    remonter_rapport()

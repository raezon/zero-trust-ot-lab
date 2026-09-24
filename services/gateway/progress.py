"""
Suivi pedagogique des etudiants (mini-LMS du lab).

Role :
  - "sign-in" d'IDENTIFICATION (nom + e-mail + groupe) : PAS de mot de passe.
    On identifie l'etudiant pour suivre sa progression, on ne gere pas de
    secret d'authentification (adapte a une salle de classe).
  - suivi des objectifs valides pendant l'exercice terminal -> note /100.
  - export du rapport de classe en CSV (telechargeable par le formateur).
  - envoi optionnel du rapport par e-mail (active UNIQUEMENT si des variables
    SMTP sont fournies ; aucun identifiant n'est stocke dans le code).

Stockage : un simple fichier JSON (DATA_DIR/students.json). Suffisant pour un
lab ; a remplacer par une vraie base en production.
"""
from __future__ import annotations

import csv
import io
import json
import os
import pathlib
import smtplib
import threading
import time
from email.message import EmailMessage

_HERE = pathlib.Path(__file__).parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", str(_HERE / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORE = DATA_DIR / "students.json"
_LOCK = threading.Lock()

# Destinataire du rapport (fourni explicitement par le formateur).
REPORT_TO = os.environ.get("REPORT_TO", "amardjebabla10@gmail.com")
# Code formateur pour telecharger le rapport (protection legere).
INSTRUCTOR_CODE = os.environ.get("INSTRUCTOR_CODE", "prof")

# Objectifs de l'exercice (total = 100 points).
OBJECTIFS = [
    {"id": "reconnaissance",   "label": "Reconnaissance reseau (scan)",                    "points": 10},
    {"id": "identite",         "label": "Identifier son jeton (whoami)",                   "points": 5},
    {"id": "refus_privilege",  "label": "Provoquer un refus (moindre privilege)",          "points": 15},
    {"id": "escalade_role",    "label": "Escalader le role (use operator)",                "points": 10},
    {"id": "escalade_zone",    "label": "Changer de zone (set zone OT)",                   "points": 10},
    {"id": "escalade_posture", "label": "Poste maitrise (set posture managed)",            "points": 10},
    {"id": "attaque_physique", "label": "Ouvrir la vanne (ALLOW apres escalade complete)", "points": 25},
    {"id": "exfiltration",     "label": "Exfiltrer la telemetrie (read sensors)",          "points": 10},
    {"id": "protection_pi",    "label": "Constater la protection de la PI (recipes DENY)", "points": 5},
]
_POINTS = {o["id"]: o["points"] for o in OBJECTIFS}
TOTAL = sum(_POINTS.values())


# --------------------------------------------------------------------------- #
# Stockage
# --------------------------------------------------------------------------- #

def _load() -> dict:
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(email: str, name: str) -> str:
    e = (email or "").strip().lower()
    return e if e else "anon:" + (name or "").strip().lower()


def _score(rec: dict) -> int:
    return sum(_POINTS.get(o, 0) for o in rec.get("objectifs", {}))


# --------------------------------------------------------------------------- #
# API interne
# --------------------------------------------------------------------------- #

def login(name: str, email: str, group: str = "") -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _LOCK:
        data = _load()
        sid = _key(email, name)
        rec = data.get(sid) or {
            "id": sid, "name": name, "email": email, "group": group,
            "created_at": now, "objectifs": {}, "events": [],
            "submitted_at": None,
        }
        rec.update({"name": name or rec["name"], "email": email or rec["email"],
                    "group": group or rec.get("group", ""), "updated_at": now})
        rec["score"] = _score(rec)
        data[sid] = rec
        _save(data)
        return rec


def mark(sid: str, objective: str) -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _LOCK:
        data = _load()
        rec = data.get(sid)
        if not rec:
            return {"ok": False, "error": "etudiant inconnu"}
        if objective in _POINTS and objective not in rec["objectifs"]:
            rec["objectifs"][objective] = now
        rec["score"] = _score(rec)
        rec["updated_at"] = now
        data[sid] = rec
        _save(data)
        return {"ok": True, "score": rec["score"], "total": TOTAL,
                "done": list(rec["objectifs"].keys())}


def add_event(sid: str, text: str) -> None:
    with _LOCK:
        data = _load()
        rec = data.get(sid)
        if not rec:
            return
        rec.setdefault("events", []).append(
            {"ts": time.strftime("%H:%M:%S"), "text": text[:200]})
        rec["events"] = rec["events"][-50:]
        data[sid] = rec
        _save(data)


def submit(sid: str) -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with _LOCK:
        data = _load()
        rec = data.get(sid)
        if not rec:
            return {"ok": False, "error": "etudiant inconnu"}
        rec["submitted_at"] = now
        rec["score"] = _score(rec)
        data[sid] = rec
        _save(data)
    emailed = _try_email(rec)
    return {"ok": True, "score": rec["score"], "total": TOTAL, "emailed": emailed}


def all_records() -> list:
    return sorted(_load().values(), key=lambda r: (r.get("group", ""), r.get("name", "")))


def to_csv() -> str:
    buf = io.StringIO()
    cols = ["name", "email", "group", "score", "total", "objectifs_valides",
            "created_at", "updated_at", "submitted_at"]
    w = csv.writer(buf)
    w.writerow(cols)
    for r in all_records():
        w.writerow([
            r.get("name", ""), r.get("email", ""), r.get("group", ""),
            r.get("score", 0), TOTAL, ";".join(r.get("objectifs", {}).keys()),
            r.get("created_at", ""), r.get("updated_at", ""), r.get("submitted_at") or "",
        ])
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# E-mail (optionnel : actif seulement si SMTP configure)
# --------------------------------------------------------------------------- #

def _try_email(rec: dict) -> bool:
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    pwd = os.environ.get("SMTP_PASS")
    if not (host and user and pwd):
        return False  # non configure -> on s'appuie sur le CSV telechargeable
    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = os.environ.get("REPORT_FROM", user)
    try:
        msg = EmailMessage()
        msg["Subject"] = (f"[Lab Zero-Trust OT] Resultats — {rec.get('name')} "
                          f"({rec.get('score')}/{TOTAL})")
        msg["From"] = sender
        msg["To"] = REPORT_TO
        msg.set_content(
            f"Etudiant : {rec.get('name')} <{rec.get('email')}>\n"
            f"Groupe   : {rec.get('group')}\n"
            f"Note     : {rec.get('score')}/{TOTAL}\n"
            f"Soumis   : {rec.get('submitted_at')}\n\n"
            f"Objectifs valides : {', '.join(rec.get('objectifs', {}).keys()) or 'aucun'}\n\n"
            "Le rapport complet de la classe est en piece jointe (CSV)."
        )
        msg.add_attachment(to_csv().encode("utf-8"), maintype="text",
                           subtype="csv", filename="rapport_classe.csv")
        with smtplib.SMTP(host, port, timeout=10) as s:
            if os.environ.get("SMTP_TLS", "true").lower() != "false":
                s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception as exc:  # on ne casse jamais l'app pour un souci d'e-mail
        logging_safe(f"envoi e-mail echoue: {type(exc).__name__}: {exc}")
        return False


def logging_safe(msg: str) -> None:
    try:
        print(json.dumps({"lms": msg}, ensure_ascii=False))
    except Exception:
        pass
